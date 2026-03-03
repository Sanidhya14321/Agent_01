"""
packages/security/src/pii_masker.py

PII Anonymiser — strips PII from text before sending to any LLM.
Uses a multi-layer approach:
  1. Regex patterns (fast, deterministic)
  2. Token-map for reversibility (stored server-side only)

Replacements: [USER_NAME], [EMAIL], [PHONE], [ADDRESS], [PAYMENT_INFO], [SSN]
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional


# ── PII Patterns ──────────────────────────────────────────────────────────────

_PII_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    (
        "EMAIL",
        "[EMAIL]",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"),
    ),
    (
        "PHONE",
        "[PHONE]",
        re.compile(
            r"(?<!\d)"
            r"(\+?\d{1,3}[\s\-\.])?"          # country code
            r"(\(?\d{3}\)?[\s\-\.])"            # area code
            r"(\d{3}[\s\-\.])"
            r"(\d{4})"
            r"(?!\d)"
        ),
    ),
    (
        "PAYMENT_INFO",
        "[PAYMENT_INFO]",
        re.compile(
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|"   # Visa
            r"5[1-5][0-9]{14}|"                 # MC
            r"3[47][0-9]{13}|"                  # Amex
            r"6(?:011|5[0-9]{2})[0-9]{12})\b"  # Discover
        ),
    ),
    (
        "SSN",
        "[SSN]",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    ),
    (
        "ADDRESS",
        "[ADDRESS]",
        re.compile(
            r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,4}"
            r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
            r"Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "IP_ADDRESS",
        "[IP_ADDRESS]",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
    ),
    (
        "API_KEY",
        "[API_KEY]",
        re.compile(
            r"\b(?:sk|pk|rk|ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"
        ),
    ),
]


@dataclass
class MaskResult:
    """
    Result of a masking operation.

    Attributes:
        masked_text : Text safe to send to LLM (PII replaced with tokens).
        token_map   : {token_id -> original_value} — NEVER sent to LLM.
                      Store server-side and use to reconstruct for display.
        entities_found : List of entity types discovered.
    """
    masked_text: str
    token_map: dict[str, str] = field(default_factory=dict)
    entities_found: list[str] = field(default_factory=list)


class PIIMasker:
    """
    Thread-safe, stateless PII masker.  Each call to `mask()` returns a
    fresh MaskResult with its own token_map.
    """

    def mask(self, text: str, reversible: bool = True) -> MaskResult:
        """
        Mask PII in `text`.

        Args:
            text       : Raw text that may contain PII.
            reversible : If True, maintains a token_map for later de-masking.
                         Set False if you never need the original values back.

        Returns:
            MaskResult with masked_text, token_map, entities_found.
        """
        result = text
        token_map: dict[str, str] = {}
        entities: list[str] = []

        for entity_type, placeholder, pattern in _PII_PATTERNS:
            matches = list(pattern.finditer(result))
            if not matches:
                continue

            entities.append(entity_type)
            for match in reversed(matches):  # reverse so indices stay valid
                original = match.group(0)
                if reversible:
                    token_id = f"{placeholder[:-1]}_{uuid.uuid4().hex[:8]}]"
                    token_map[token_id] = original
                    replacement = token_id
                else:
                    replacement = placeholder

                start, end = match.span()
                result = result[:start] + replacement + result[end:]

        return MaskResult(
            masked_text=result,
            token_map=token_map,
            entities_found=list(set(entities)),
        )

    def unmask(self, text: str, token_map: dict[str, str]) -> str:
        """
        Restore original values from token_map (server-side only, never call
        on LLM output that will be re-processed by an LLM).
        """
        result = text
        for token, original in token_map.items():
            result = result.replace(token, original)
        return result

    def is_safe(self, text: str) -> tuple[bool, list[str]]:
        """
        Quick-check: returns (is_safe, [entity_types_found]).
        Use in the Purification Node to decide whether to block tool output.
        """
        found = []
        for entity_type, _, pattern in _PII_PATTERNS:
            if pattern.search(text):
                found.append(entity_type)
        return (len(found) == 0, found)


# ── Module-level singleton ────────────────────────────────────────────────────

masker = PIIMasker()


def mask_text(text: str, reversible: bool = True) -> MaskResult:
    """Convenience wrapper around PIIMasker.mask()."""
    return masker.mask(text, reversible=reversible)


def check_safe(text: str) -> tuple[bool, list[str]]:
    """Convenience wrapper around PIIMasker.is_safe()."""
    return masker.is_safe(text)
