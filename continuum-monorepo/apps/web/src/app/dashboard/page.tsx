"use client";
import { useState } from "react";
import Link from "next/link";

// ── Mock data (replaced with real API calls in production) ─────────────────
const MOCK_INSIGHTS = [
    {
        id: "1",
        title: "AWS costs up 34% — 3 culprit services identified",
        summary: "Gmail receipt analysis detected $247 in unexpected Lambda & S3 charges from Feb 28 billing cycle. Cross-referenced with GitHub repo 'ml-experiments' — nightly training jobs are leaving GPU instances running.",
        source: "gmail+github",
        confidence: 0.91,
        tags: ["cost", "aws", "ml"],
        createdAt: "2026-03-03",
        checkpointId: "ckpt_abc123",
    },
    {
        id: "2",
        title: "LangGraph learning streak — 8 videos this week",
        summary: "YouTube liked-video analysis shows a focused 8-video LangGraph/RAG learning sprint. Correlated with GitHub repo 'continuum-monorepo' — 42 commits pushed in the same window.",
        source: "youtube+github",
        confidence: 0.88,
        tags: ["learning", "langgraph", "rag"],
        createdAt: "2026-03-02",
        checkpointId: "ckpt_def456",
    },
    {
        id: "3",
        title: "GitHub Copilot ROI: 2.3× commit velocity",
        summary: "Comparing commit frequency before/after GitHub Copilot invoice date (Mar 1). Commits per day increased from 6.2 → 14.1 — a 2.3× lift attributable to the subscription period.",
        source: "github+gmail",
        confidence: 0.74,
        tags: ["copilot", "productivity", "roi"],
        createdAt: "2026-03-01",
        checkpointId: "ckpt_ghi789",
    },
    {
        id: "4",
        title: "Potential duplicate SaaS subscriptions detected",
        summary: "3 overlapping project-management tool invoices found across Gmail (Linear, Jira, Notion) with $89/mo combined overspend. Recommend consolidating to primary tool.",
        source: "gmail",
        confidence: 0.65,  // below threshold → HITL
        tags: ["saas", "spending", "audit"],
        createdAt: "2026-02-28",
        checkpointId: "ckpt_jkl012",
        hitl: true,
    },
];

interface CheckpointEntry {
    checkpoint_id: string;
    node_reached: string;
    confidence: number | null;
    iteration: number;
    status: string;
}

function ConfidenceBadge({ score, hitl }: { score: number; hitl?: boolean }) {
    if (hitl) return <span className="badge badge-hitl">⚠️ HITL Review</span>;
    if (score >= 0.85) return <span className="badge badge-success">● {(score * 100).toFixed(0)}% confidence</span>;
    if (score >= 0.7) return <span className="badge badge-warn">● {(score * 100).toFixed(0)}% confidence</span>;
    return <span className="badge badge-danger">● {(score * 100).toFixed(0)}% confidence</span>;
}

function SourceBadge({ source }: { source: string }) {
    const parts = source.split("+");
    return (
        <div className="flex" style={{ gap: "0.3rem" }}>
            {parts.map((s) => (
                <span key={s} className="badge badge-muted">{s}</span>
            ))}
        </div>
    );
}

function RewindModal({ insight, onClose }: { insight: typeof MOCK_INSIGHTS[0]; onClose: () => void }) {
    const [loading, setLoading] = useState(false);
    const [rewound, setRewound] = useState(false);

    const mockHistory: CheckpointEntry[] = [
        { checkpoint_id: insight.checkpointId, node_reached: "emit", confidence: insight.confidence, iteration: 2, status: "completed" },
        { checkpoint_id: `${insight.checkpointId}_pre`, node_reached: "synthesise", confidence: insight.confidence - 0.1, iteration: 1, status: "running" },
        { checkpoint_id: `${insight.checkpointId}_ingest`, node_reached: "purify", confidence: null, iteration: 0, status: "running" },
    ];

    const handleRewind = async (checkpointId: string) => {
        setLoading(true);
        try {
            await fetch(`http://localhost:8000/rewind/${insight.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ checkpoint_id: checkpointId }),
            });
            setRewound(true);
        } catch (_) {
            setRewound(true); // demo mode
        }
        setLoading(false);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-between items-center" style={{ marginBottom: "1.5rem" }}>
                    <h2 className="t-h3">↩️ Rewind State</h2>
                    <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
                </div>

                <p className="t-body" style={{ marginBottom: "1.5rem", fontSize: "0.875rem" }}>
                    Select a checkpoint to restore. The agent state at that node will be replayed.
                </p>

                {rewound ? (
                    <div className="card card-body" style={{ background: "rgba(52,211,153,0.06)", borderColor: "rgba(52,211,153,0.2)", textAlign: "center", padding: "2rem" }}>
                        <p style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>✓</p>
                        <p className="t-h3" style={{ color: "var(--color-success)" }}>State rewound successfully</p>
                        <p className="t-body" style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>The insight has been marked as REWOUND.</p>
                    </div>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                        {mockHistory.map((entry, i) => (
                            <div key={entry.checkpoint_id} className="card card-body" style={{ padding: "1rem" }}>
                                <div className="flex justify-between items-center">
                                    <div>
                                        <p className="t-label" style={{ marginBottom: "0.2rem" }}>Iteration {entry.iteration} · {entry.node_reached}</p>
                                        {entry.confidence !== null && (
                                            <p style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
                                                Confidence: {(entry.confidence * 100).toFixed(0)}%
                                            </p>
                                        )}
                                    </div>
                                    <button
                                        className="btn btn-outline btn-sm"
                                        onClick={() => handleRewind(entry.checkpoint_id)}
                                        disabled={loading || i === 0}
                                    >
                                        {i === 0 ? "Current" : loading ? "…" : "Rewind here"}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function DashboardPage() {
    const [rewindTarget, setRewindTarget] = useState<typeof MOCK_INSIGHTS[0] | null>(null);

    return (
        <>
            <nav className="nav">
                <div className="nav-inner">
                    <Link href="/" className="nav-logo">Continu<span>um</span></Link>
                    <div className="nav-links">
                        <Link href="/connect" className="nav-link">Connect</Link>
                        <Link href="/admin" className="nav-link">Admin</Link>
                        <Link href="/connect" className="btn btn-outline btn-sm">⚡ Harvest</Link>
                    </div>
                </div>
            </nav>

            <main className="container section">
                <div style={{ marginBottom: "2.5rem" }}>
                    <p className="t-label">Knowledge Graph</p>
                    <h1 className="t-h1" style={{ marginTop: "0.5rem", marginBottom: "0.75rem" }}>
                        Your synthesised insights
                    </h1>
                    <p className="t-body">
                        {MOCK_INSIGHTS.length} insights · 3 sources connected · Last harvest: 2 hours ago
                    </p>
                </div>

                {/* Stats row */}
                <div className="grid-3" style={{ marginBottom: "2.5rem" }}>
                    {[
                        { label: "Total Insights", value: "4", icon: "🧠", color: "var(--color-accent)" },
                        { label: "Tokens Used Today", value: "12,847", icon: "💸", color: "var(--color-warn)" },
                        { label: "HITL Pending", value: "1", icon: "⚠️", color: "var(--color-hitl)" },
                    ].map((stat) => (
                        <div key={stat.label} className="card card-body" style={{ padding: "1.25rem" }}>
                            <div className="flex items-center" style={{ gap: "0.75rem" }}>
                                <span style={{ fontSize: "1.5rem" }}>{stat.icon}</span>
                                <div className="stat-block">
                                    <span className="stat-value" style={{ color: stat.color }}>{stat.value}</span>
                                    <span className="stat-label">{stat.label}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Insight cards */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                    {MOCK_INSIGHTS.map((insight) => (
                        <div key={insight.id} className="card card-body" style={{ padding: "1.5rem", borderColor: insight.hitl ? "rgba(245,158,11,0.2)" : undefined }}>
                            <div className="flex justify-between items-center" style={{ marginBottom: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
                                <div className="flex items-center" style={{ gap: "0.5rem", flexWrap: "wrap" }}>
                                    <ConfidenceBadge score={insight.confidence} hitl={insight.hitl} />
                                    <SourceBadge source={insight.source} />
                                    <span style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>{insight.createdAt}</span>
                                </div>
                                <button
                                    className="btn btn-ghost btn-sm"
                                    onClick={() => setRewindTarget(insight)}
                                    title="Rewind this insight"
                                >
                                    ↩️ Rewind
                                </button>
                            </div>
                            <h2 className="t-h3" style={{ marginBottom: "0.5rem" }}>{insight.title}</h2>
                            <p className="t-body" style={{ fontSize: "0.875rem", marginBottom: "1rem" }}>{insight.summary}</p>
                            <div className="flex" style={{ gap: "0.4rem", flexWrap: "wrap" }}>
                                {insight.tags.map((tag) => (
                                    <span key={tag} className="badge badge-accent">#{tag}</span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </main>

            {rewindTarget && (
                <RewindModal insight={rewindTarget} onClose={() => setRewindTarget(null)} />
            )}
        </>
    );
}
