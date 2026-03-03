import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
    title: "Continuum — The Zero-Loss Knowledge Bridge",
    description:
        "Continuum synthesises your GitHub, Gmail, and YouTube data into an autonomous knowledge graph that surfaces insights, audits spending, and preserves intellectual capital.",
    keywords: ["AI", "knowledge graph", "autonomous agents", "LangGraph", "digital estate"],
    authors: [{ name: "Continuum" }],
    openGraph: {
        title: "Continuum — The Zero-Loss Knowledge Bridge",
        description: "Autonomous synthesis across your digital siloes.",
        type: "website",
    },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body>{children}</body>
        </html>
    );
}
