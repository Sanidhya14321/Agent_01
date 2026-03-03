"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const STEPS = [
    {
        id: 1,
        title: "Welcome to Continuum",
        subtitle: "Before we start, let's be transparent about what our agents can see.",
        content: (
            <div>
                <p className="t-body" style={{ marginBottom: "1.5rem" }}>
                    Continuum's agents are designed around <strong style={{ color: "var(--color-accent)" }}>minimum viable access</strong>.
                    We will never request permissions we don't need. Here's our promise:
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {[
                        { icon: "🔐", text: "OAuth tokens are encrypted with AES-256 and stored only on your account" },
                        { icon: "🕵️", text: "Your text is PII-anonymised before any LLM call — names become [USER_NAME]" },
                        { icon: "🔒", text: "Your knowledge graph lives in an isolated namespace — never mixed with other users" },
                        { icon: "↩️", text: "You can Rewind or delete any synthesised insight at any time" },
                        { icon: "💸", text: "A token quota caps your daily LLM cost — default $5/month" },
                    ].map((item) => (
                        <div key={item.text} className="card card-body flex" style={{ gap: "0.75rem", alignItems: "flex-start", padding: "0.85rem 1rem" }}>
                            <span style={{ fontSize: "1.2rem", flexShrink: 0 }}>{item.icon}</span>
                            <p style={{ fontSize: "0.875rem", color: "var(--color-ink-muted)", lineHeight: 1.55 }}>{item.text}</p>
                        </div>
                    ))}
                </div>
            </div>
        ),
    },
    {
        id: 2,
        title: "GitHub Access",
        subtitle: "What Continuum can and cannot see.",
        content: (
            <ScopeTable
                scopes={[
                    { scope: "repo (read-only)", canSee: "Repo names, languages, commit messages, file structure", cannotSee: "Private repo file contents, secrets or .env files, GitHub Actions logs" },
                    { scope: "user:email", canSee: "Your primary email address (for account linking)", cannotSee: "SSH keys, GPG keys, billing info, connected apps" },
                ]}
            />
        ),
    },
    {
        id: 3,
        title: "Gmail & YouTube Access",
        subtitle: "Metadata only — never the content of your emails.",
        content: (
            <ScopeTable
                scopes={[
                    { scope: "gmail.metadata", canSee: "Email subjects, sender addresses, timestamps, labels", cannotSee: "Email body text, attachments, contacts, drafts" },
                    { scope: "youtube.readonly", canSee: "Liked video titles, subscription channel names, watch history titles", cannotSee: "Comments, private playlists, YouTube revenue, account billing" },
                ]}
            />
        ),
    },
    {
        id: 4,
        title: "You're in control",
        subtitle: "Confirm your understanding before we proceed.",
        content: (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {[
                    "I understand Continuum reads only metadata — never the body of my emails",
                    "I understand my data is PII-anonymised before being sent to an LLM",
                    "I understand I can revoke access or delete my knowledge graph at any time",
                    "I accept the Terms of Service and Privacy Policy",
                ].map((item, i) => (
                    <label key={i} className="card card-body flex" style={{ gap: "0.85rem", alignItems: "center", cursor: "pointer", padding: "0.85rem 1rem" }}>
                        <input type="checkbox" style={{ width: 18, height: 18, accentColor: "var(--color-accent)", flexShrink: 0 }} />
                        <span style={{ fontSize: "0.875rem", color: "var(--color-ink-muted)" }}>{item}</span>
                    </label>
                ))}
            </div>
        ),
    },
];

function ScopeTable({ scopes }: { scopes: { scope: string; canSee: string; cannotSee: string }[] }) {
    return (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {scopes.map((s) => (
                <div key={s.scope} className="card card-body" style={{ padding: "1rem" }}>
                    <p className="t-label" style={{ marginBottom: "0.75rem" }}>{s.scope}</p>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                        <div style={{ background: "rgba(52,211,153,0.06)", borderRadius: 8, padding: "0.75rem" }}>
                            <p style={{ fontSize: "0.72rem", color: "var(--color-success)", fontWeight: 600, marginBottom: "0.4rem" }}>✓ CAN SEE</p>
                            <p style={{ fontSize: "0.825rem", color: "var(--color-ink-muted)" }}>{s.canSee}</p>
                        </div>
                        <div style={{ background: "rgba(248,113,113,0.06)", borderRadius: 8, padding: "0.75rem" }}>
                            <p style={{ fontSize: "0.72rem", color: "var(--color-danger)", fontWeight: 600, marginBottom: "0.4rem" }}>✕ CANNOT SEE</p>
                            <p style={{ fontSize: "0.825rem", color: "var(--color-ink-muted)" }}>{s.cannotSee}</p>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default function OnboardingPage() {
    const [step, setStep] = useState(0);
    const router = useRouter();

    const currentStep = STEPS[step];
    const isLast = step === STEPS.length - 1;

    return (
        <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
            <div style={{ width: "100%", maxWidth: 620 }}>
                {/* Header */}
                <div className="flex items-center justify-between" style={{ marginBottom: "2rem" }}>
                    <Link href="/" className="nav-logo" style={{ fontSize: "1.1rem" }}>Continu<span style={{ color: "var(--color-accent)" }}>um</span></Link>
                    <div className="step-indicator">
                        {STEPS.map((_, i) => (
                            <div key={i} className={`step-dot ${i < step ? "done" : i === step ? "active" : ""}`} />
                        ))}
                    </div>
                </div>

                {/* Card */}
                <div className="card card-body fade-in-up" style={{ padding: "2.5rem" }}>
                    <p className="t-label" style={{ marginBottom: "0.4rem" }}>Step {step + 1} of {STEPS.length}</p>
                    <h1 className="t-h2" style={{ marginBottom: "0.5rem" }}>{currentStep.title}</h1>
                    <p className="t-body" style={{ marginBottom: "2rem" }}>{currentStep.subtitle}</p>

                    {currentStep.content}

                    <div className="divider" />
                    <div className="flex justify-between items-center">
                        <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => setStep(Math.max(0, step - 1))}
                            disabled={step === 0}
                        >
                            ← Back
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={() => isLast ? router.push("/connect") : setStep(step + 1)}
                        >
                            {isLast ? "Connect integrations →" : "Continue →"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
