"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import {
    Treemap,
    ResponsiveContainer,
    Tooltip,
} from "recharts";

// ── Mock data (populated from GET /admin/heatmap in production) ─────────────
const HEATMAP_DATA = [
    { name: "github", size: 48200, color: "#0FA3B1", label: "GitHub Harvester", jobs: 24 },
    { name: "gmail", size: 31500, color: "#EA4335", label: "Gmail Harvester", jobs: 18 },
    { name: "youtube", size: 12847, color: "#7B61FF", label: "YouTube Harvester", jobs: 9 },
];

const HEALTH_DATA = [
    { source: "github", total: 24, completed: 22, failed: 1, hitl: 1, successRate: "91.7%", avgTokens: 2008, avgIter: 2.1 },
    { source: "gmail", total: 18, completed: 16, failed: 0, hitl: 2, successRate: "88.9%", avgTokens: 1750, avgIter: 1.8 },
    { source: "youtube", total: 9, completed: 9, failed: 0, hitl: 0, successRate: "100%", avgTokens: 1427, avgIter: 1.2 },
];

const TOTAL_TOKENS = HEATMAP_DATA.reduce((a, b) => a + b.size, 0);

// Custom Treemap content renderer
function HeatmapContent(props: any) {
    const { x, y, width, height, name, color, value } = props;
    if (width < 40 || height < 40) return null;
    const pct = ((value / TOTAL_TOKENS) * 100).toFixed(1);
    return (
        <g>
            <rect x={x} y={y} width={width} height={height} fill={color} fillOpacity={0.18} rx={10} />
            <rect x={x} y={y} width={width} height={3} fill={color} rx={2} />
            <text x={x + 14} y={y + 28} fill="#F0EEE9" fontSize={13} fontWeight={700} fontFamily="Inter,sans-serif">{name}</text>
            <text x={x + 14} y={y + 48} fill={color} fontSize={22} fontWeight={800} fontFamily="Inter,sans-serif">{value.toLocaleString()}</text>
            <text x={x + 14} y={y + 66} fill="rgba(240,238,233,0.5)" fontSize={11} fontFamily="Inter,sans-serif">{pct}% of total</text>
        </g>
    );
}

function StatusBadge({ val, total }: { val: number; total: number }) {
    const pct = total > 0 ? (val / total) * 100 : 0;
    if (pct >= 90) return <span className="badge badge-success">{val}</span>;
    if (pct >= 70) return <span className="badge badge-warn">{val}</span>;
    return <span className="badge badge-danger">{val}</span>;
}

export default function AdminPage() {
    const [activeTab, setActiveTab] = useState<"heatmap" | "health">("heatmap");

    return (
        <>
            <nav className="nav">
                <div className="nav-inner">
                    <Link href="/" className="nav-logo">Continu<span>um</span></Link>
                    <div className="nav-links">
                        <Link href="/dashboard" className="nav-link">Dashboard</Link>
                        <Link href="/connect" className="nav-link">Connect</Link>
                        <span className="badge badge-accent" style={{ fontSize: "0.7rem" }}>Admin</span>
                    </div>
                </div>
            </nav>

            <main className="container section">
                <div style={{ marginBottom: "2.5rem" }}>
                    <div className="glow-pill" style={{ display: "inline-flex" }}>🔭 Observability Control Plane</div>
                    <h1 className="t-h1" style={{ marginBottom: "0.75rem" }}>Admin Dashboard</h1>
                    <p className="t-body">Monitor agent health, token burn rates, and ingestion pipelines in real-time.</p>
                </div>

                {/* Summary stats */}
                <div className="grid-3" style={{ marginBottom: "2.5rem" }}>
                    {[
                        { label: "Total Tokens (24h)", value: TOTAL_TOKENS.toLocaleString(), icon: "🔥", color: "var(--color-warn)" },
                        { label: "Est. Cost (24h)", value: `$${(TOTAL_TOKENS / 1_000_000 * 5).toFixed(3)}`, icon: "💰", color: "var(--color-accent)" },
                        { label: "Total Jobs", value: HEALTH_DATA.reduce((a, b) => a + b.total, 0), icon: "⚡", color: "var(--color-accent-2)" },
                        { label: "HITL Pending", value: HEALTH_DATA.reduce((a, b) => a + b.hitl, 0), icon: "⚠️", color: "var(--color-hitl)" },
                        { label: "Failures", value: HEALTH_DATA.reduce((a, b) => a + b.failed, 0), icon: "❌", color: "var(--color-danger)" },
                        { label: "Avg Iterations", value: "1.7", icon: "🔄", color: "var(--color-ink-muted)" },
                    ].map((stat) => (
                        <div key={stat.label} className="card card-body" style={{ padding: "1.25rem" }}>
                            <div className="flex items-center" style={{ gap: "0.75rem" }}>
                                <span style={{ fontSize: "1.5rem" }}>{stat.icon}</span>
                                <div className="stat-block">
                                    <span className="stat-value" style={{ color: stat.color, fontSize: "1.6rem" }}>{stat.value}</span>
                                    <span className="stat-label">{stat.label}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Tabs */}
                <div className="flex" style={{ gap: "0.5rem", marginBottom: "1.5rem" }}>
                    <button
                        className={`btn btn-sm ${activeTab === "heatmap" ? "btn-primary" : "btn-ghost"}`}
                        onClick={() => setActiveTab("heatmap")}
                    >
                        🔥 Token Heatmap
                    </button>
                    <button
                        className={`btn btn-sm ${activeTab === "health" ? "btn-primary" : "btn-ghost"}`}
                        onClick={() => setActiveTab("health")}
                    >
                        📋 Agent Health
                    </button>
                </div>

                {/* Token Heatmap */}
                {activeTab === "heatmap" && (
                    <div className="card card-body fade-in-up" style={{ padding: "1.5rem" }}>
                        <div className="flex justify-between items-center" style={{ marginBottom: "1rem" }}>
                            <h2 className="t-h3">Token Burn Heatmap — Last 24h</h2>
                            <span className="t-body" style={{ fontSize: "0.8rem" }}>
                                Total: <strong style={{ color: "var(--color-accent)" }}>{TOTAL_TOKENS.toLocaleString()} tokens</strong>
                            </span>
                        </div>

                        <ResponsiveContainer width="100%" height={320}>
                            <Treemap
                                data={HEATMAP_DATA}
                                dataKey="size"
                                content={<HeatmapContent />}
                            >
                                <Tooltip
                                    content={({ active, payload }) => {
                                        if (!active || !payload?.length) return null;
                                        const d = payload[0].payload;
                                        return (
                                            <div className="card card-body" style={{ padding: "0.75rem 1rem", minWidth: 160 }}>
                                                <p style={{ fontWeight: 700, marginBottom: "0.25rem" }}>{d.label}</p>
                                                <p style={{ color: d.color, fontWeight: 700 }}>{(d.size as number).toLocaleString()} tokens</p>
                                                <p style={{ fontSize: "0.78rem", color: "var(--color-ink-muted)", marginTop: "0.2rem" }}>{d.jobs} jobs</p>
                                            </div>
                                        );
                                    }}
                                />
                            </Treemap>
                        </ResponsiveContainer>

                        <div className="divider" />
                        <div className="flex" style={{ gap: "1.5rem", flexWrap: "wrap" }}>
                            {HEATMAP_DATA.map((d) => (
                                <div key={d.name} className="flex items-center" style={{ gap: "0.5rem" }}>
                                    <div style={{ width: 10, height: 10, borderRadius: 3, background: d.color }} />
                                    <span style={{ fontSize: "0.825rem", color: "var(--color-ink-muted)" }}>
                                        {d.label}: <strong style={{ color: "var(--color-ink)" }}>{d.size.toLocaleString()}</strong>
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Agent Health Table */}
                {activeTab === "health" && (
                    <div className="card fade-in-up" style={{ overflow: "hidden" }}>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Source</th>
                                    <th>Total Jobs</th>
                                    <th>Completed</th>
                                    <th>HITL</th>
                                    <th>Failed</th>
                                    <th>Success Rate</th>
                                    <th>Avg Tokens</th>
                                    <th>Avg Iterations</th>
                                </tr>
                            </thead>
                            <tbody>
                                {HEALTH_DATA.map((row) => (
                                    <tr key={row.source}>
                                        <td>
                                            <span className="badge badge-muted" style={{ fontSize: "0.8rem" }}>{row.source}</span>
                                        </td>
                                        <td style={{ fontWeight: 600 }}>{row.total}</td>
                                        <td><StatusBadge val={row.completed} total={row.total} /></td>
                                        <td>
                                            {row.hitl > 0
                                                ? <span className="badge badge-hitl">{row.hitl}</span>
                                                : <span style={{ color: "var(--color-ink-muted)" }}>—</span>}
                                        </td>
                                        <td>
                                            {row.failed > 0
                                                ? <span className="badge badge-danger">{row.failed}</span>
                                                : <span style={{ color: "var(--color-ink-muted)" }}>—</span>}
                                        </td>
                                        <td style={{ color: "var(--color-success)", fontWeight: 600 }}>{row.successRate}</td>
                                        <td style={{ color: "var(--color-ink-muted)" }}>{row.avgTokens.toLocaleString()}</td>
                                        <td style={{ color: "var(--color-accent)" }}>{row.avgIter}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </main>
        </>
    );
}
