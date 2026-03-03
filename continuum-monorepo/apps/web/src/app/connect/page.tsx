"use client";
import { useState } from "react";
import Link from "next/link";

const INTEGRATIONS = [
    {
        id: "github",
        name: "GitHub",
        icon: "🐙",
        description: "Harvest repo names, commit messages, and language stats",
        scopes: ["repo (read-only)", "user:email"],
        color: "#c9d1d9",
        bg: "rgba(201,209,217,0.06)",
    },
    {
        id: "gmail",
        name: "Gmail",
        icon: "📧",
        description: "Harvest email subjects and senders to find receipts and invoices",
        scopes: ["gmail.metadata"],
        color: "#EA4335",
        bg: "rgba(234,67,53,0.06)",
    },
    {
        id: "youtube",
        name: "YouTube",
        icon: "▶️",
        description: "Harvest liked video titles and subscription channels",
        scopes: ["youtube.readonly"],
        color: "#FF0000",
        bg: "rgba(255,0,0,0.06)",
    },
];

type ConnectionState = Record<string, "idle" | "connecting" | "connected">;

export default function ConnectPage() {
    const [connections, setConnections] = useState<ConnectionState>({
        github: "idle",
        gmail: "idle",
        youtube: "idle",
    });
    const [harvesting, setHarvesting] = useState<string | null>(null);

    const handleConnect = (id: string) => {
        setConnections((prev) => ({ ...prev, [id]: "connecting" }));
        // In production: redirect to OAuth URL from /api/auth/{provider}
        setTimeout(() => {
            setConnections((prev) => ({ ...prev, [id]: "connected" }));
        }, 1500);
    };

    const handleHarvest = async (id: string) => {
        setHarvesting(id);
        try {
            await fetch(`${process.env.NEXT_PUBLIC_AGENT_HUB_URL || "http://localhost:8000"}/harvest`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: "demo-user", source: id }),
            });
        } catch (_) { }
        setTimeout(() => setHarvesting(null), 3000);
    };

    const connectedCount = Object.values(connections).filter((v) => v === "connected").length;

    return (
        <>
            <nav className="nav">
                <div className="nav-inner">
                    <Link href="/" className="nav-logo">Continu<span>um</span></Link>
                    <div className="nav-links">
                        <Link href="/dashboard" className="nav-link">Dashboard</Link>
                        <Link href="/admin" className="nav-link">Admin</Link>
                    </div>
                </div>
            </nav>

            <main className="container section" style={{ maxWidth: 800 }}>
                <div style={{ marginBottom: "2.5rem" }}>
                    <p className="t-label">Connection Hub</p>
                    <h1 className="t-h1" style={{ marginTop: "0.5rem", marginBottom: "0.75rem" }}>
                        Connect your integrations
                    </h1>
                    <p className="t-body">
                        Each card shows the exact OAuth scopes we request. No surprises.{" "}
                        {connectedCount > 0 && (
                            <span className="badge badge-success" style={{ marginLeft: "0.5rem" }}>
                                {connectedCount} connected
                            </span>
                        )}
                    </p>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                    {INTEGRATIONS.map((integration) => {
                        const state = connections[integration.id];
                        const isConnected = state === "connected";
                        const isConnecting = state === "connecting";

                        return (
                            <div
                                key={integration.id}
                                className="card card-body"
                                style={{
                                    background: isConnected ? integration.bg : undefined,
                                    borderColor: isConnected ? `${integration.color}30` : undefined,
                                    padding: "1.5rem",
                                }}
                            >
                                <div className="flex justify-between items-center" style={{ flexWrap: "wrap", gap: "1rem" }}>
                                    <div className="flex items-center" style={{ gap: "1rem" }}>
                                        <div style={{
                                            width: 52, height: 52, borderRadius: 14,
                                            background: integration.bg, border: `1px solid ${integration.color}20`,
                                            display: "flex", alignItems: "center", justifyContent: "center",
                                            fontSize: "1.5rem", flexShrink: 0,
                                        }}>
                                            {integration.icon}
                                        </div>
                                        <div>
                                            <div className="flex items-center" style={{ gap: "0.5rem", marginBottom: "0.25rem" }}>
                                                <h3 className="t-h3">{integration.name}</h3>
                                                {isConnected && <span className="badge badge-success">✓ Connected</span>}
                                            </div>
                                            <p className="t-body" style={{ fontSize: "0.85rem", marginBottom: "0.5rem" }}>
                                                {integration.description}
                                            </p>
                                            <div className="flex" style={{ gap: "0.4rem", flexWrap: "wrap" }}>
                                                {integration.scopes.map((s) => (
                                                    <span key={s} className="badge badge-muted">{s}</span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex" style={{ gap: "0.5rem" }}>
                                        {isConnected && (
                                            <button
                                                className="btn btn-outline btn-sm"
                                                onClick={() => handleHarvest(integration.id)}
                                                disabled={harvesting === integration.id}
                                            >
                                                {harvesting === integration.id ? "⚡ Harvesting…" : "⚡ Harvest now"}
                                            </button>
                                        )}
                                        <button
                                            className={`btn btn-sm ${isConnected ? "btn-ghost" : "btn-primary"}`}
                                            onClick={() => !isConnected && handleConnect(integration.id)}
                                            disabled={isConnecting || isConnected}
                                            style={{ minWidth: 110 }}
                                        >
                                            {isConnecting ? "Connecting…" : isConnected ? "✓ Connected" : `Connect ${integration.name}`}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {connectedCount > 0 && (
                    <div style={{ marginTop: "2rem", textAlign: "center" }}>
                        <Link href="/dashboard" className="btn btn-primary btn-lg">
                            View my knowledge graph →
                        </Link>
                    </div>
                )}
            </main>
        </>
    );
}
