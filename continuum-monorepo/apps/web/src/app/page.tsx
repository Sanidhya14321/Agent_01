"use client";
import Link from "next/link";

export default function HomePage() {
    return (
        <>
            {/* ── Navigation ─────────────────────────────────────────────────── */}
            <nav className="nav">
                <div className="nav-inner">
                    <div className="nav-logo">
                        Continu<span>um</span>
                    </div>
                    <div className="nav-links">
                        <Link href="/dashboard" className="nav-link">Dashboard</Link>
                        <Link href="/connect" className="nav-link">Connect</Link>
                        <Link href="/admin" className="nav-link">Admin</Link>
                        <Link href="/onboarding" className="btn btn-primary btn-sm">Get Started</Link>
                    </div>
                </div>
            </nav>

            {/* ── Hero ──────────────────────────────────────────────────────── */}
            <main>
                <section className="section" style={{ paddingTop: "8rem", paddingBottom: "6rem" }}>
                    <div className="container" style={{ textAlign: "center", maxWidth: 760 }}>
                        <div className="glow-pill fade-in-up">
                            🛡️ Zero-Loss Knowledge Bridge
                        </div>
                        <h1 className="t-hero fade-in-up delay-1">
                            Your digital life,<br />
                            <span className="gradient-text">synthesised.</span>
                        </h1>
                        <p className="t-body fade-in-up delay-2" style={{ maxWidth: 560, margin: "1.5rem auto 2.5rem" }}>
                            Continuum autonomously harvests GitHub, Gmail, and YouTube —
                            turning your scattered digital work into a living knowledge graph.
                            Privacy-first, cost-controlled, and always in your control.
                        </p>
                        <div className="flex justify-center gap-4 fade-in-up delay-3">
                            <Link href="/onboarding" className="btn btn-primary btn-lg">Start for free →</Link>
                            <Link href="#how-it-works" className="btn btn-outline btn-lg">See how it works</Link>
                        </div>
                    </div>
                </section>

                {/* ── Trust Badges ──────────────────────────────────────────────── */}
                <section style={{ padding: "2rem 0", borderTop: "1px solid var(--color-border)", borderBottom: "1px solid var(--color-border)" }}>
                    <div className="container flex justify-center gap-8 items-center" style={{ flexWrap: "wrap" }}>
                        {[
                            { icon: "🔐", text: "OAuth Least Privilege" },
                            { icon: "🕵️", text: "PII Anonymised before LLM" },
                            { icon: "🔒", text: "Sovereign Vector Namespaces" },
                            { icon: "⚡", text: "Max 5 Iterations / Agent" },
                            { icon: "↩️", text: "State Rewind (Rollback)" },
                        ].map((b) => (
                            <div key={b.text} className="flex items-center gap-4" style={{ gap: "0.5rem", color: "var(--color-ink-muted)", fontSize: "0.85rem", fontWeight: 500 }}>
                                <span>{b.icon}</span> {b.text}
                            </div>
                        ))}
                    </div>
                </section>

                {/* ── How It Works ──────────────────────────────────────────────── */}
                <section id="how-it-works" className="section">
                    <div className="container">
                        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
                            <p className="t-label">Architecture</p>
                            <h2 className="t-h1" style={{ marginTop: "0.5rem" }}>How Continuum works</h2>
                        </div>
                        <div className="grid-3">
                            {[
                                { step: "01", title: "Connect your siloes", body: "Authorise GitHub, Gmail, and YouTube with read-only OAuth. We request only the minimum scopes needed — nothing more.", icon: "🔗" },
                                { step: "02", title: "Agents harvest & purify", body: "Self-correcting LangGraph agents ingest data, scrub PII, validate tool outputs, and enforce recursion limits to prevent runaway costs.", icon: "🤖" },
                                { step: "03", title: "Knowledge synthesised", body: "GPT-4o synthesises cross-platform insights into your sovereign knowledge graph — indexed in your private vector namespace.", icon: "🧠" },
                                { step: "04", title: "Review & Rewind", body: "Every synthesis is a checkpoint. Disagree with an insight? Rewind the agent state to any prior snapshot in one click.", icon: "↩️" },
                                { step: "05", title: "Human-in-the-Loop", body: "If confidence is below 70%, the agent refuses to guess and routes the task to you for review — preventing hallucinated insights.", icon: "👁️" },
                                { step: "06", title: "Admin Control Plane", body: "Monitor agent health, token burn rates, and ingestion success in a real-time dashboard. Know exactly what's happening.", icon: "📊" },
                            ].map((card) => (
                                <div key={card.step} className="card card-body fade-in-up">
                                    <div style={{ fontSize: "2rem", marginBottom: "0.75rem" }}>{card.icon}</div>
                                    <p className="t-label" style={{ marginBottom: "0.4rem" }}>Step {card.step}</p>
                                    <h3 className="t-h3" style={{ marginBottom: "0.5rem" }}>{card.title}</h3>
                                    <p className="t-body" style={{ fontSize: "0.875rem" }}>{card.body}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* ── CTA Banner ──────────────────────────────────────────────── */}
                <section className="section" style={{ paddingTop: "4rem", paddingBottom: "6rem" }}>
                    <div className="container" style={{ textAlign: "center" }}>
                        <div className="card card-body" style={{ maxWidth: 640, margin: "0 auto", padding: "3rem", background: "linear-gradient(135deg, rgba(15,163,177,0.08) 0%, rgba(123,97,255,0.08) 100%)" }}>
                            <h2 className="t-h1" style={{ marginBottom: "1rem" }}>
                                Ready to own your data?
                            </h2>
                            <p className="t-body" style={{ marginBottom: "2rem" }}>
                                Set up in under 5 minutes. Cancel any time.
                            </p>
                            <Link href="/onboarding" className="btn btn-primary btn-lg">
                                Begin onboarding →
                            </Link>
                        </div>
                    </div>
                </section>
            </main>
        </>
    );
}
