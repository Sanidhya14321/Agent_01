# Continuum — The Zero-Loss Knowledge Bridge

> **Autonomous Digital Estate Platform** — synthesises GitHub, Gmail, and YouTube into a private, cost-controlled knowledge graph.

## 🗂️ Monorepo Structure

```
continuum-monorepo/
├── apps/
│   ├── web/            # Next.js 14 — Connection Hub, Dashboard, Admin Control Plane
│   └── agent-hub/      # FastAPI + LangGraph — Self-Correcting Harvester
├── packages/
│   ├── database/       # Prisma schema + Supabase SQL migrations
│   ├── security/       # PII masker, OAuth helpers, AES-256 encryption
│   └── observability/  # OpenTelemetry tracer + cost meters
└── infra/
    ├── docker-compose.yml
    └── k8s/
```

## 🚀 Quick Start (Dev)

```bash
# 1. Copy env file and fill in your API keys
cp .env.example .env

# 2. Start all services
cd infra && docker-compose up -d

# 3. Run migrations
cd ../packages/database && npm run migrate

# 4. Open the app
open http://localhost:3000
```

## 🤖 Agentic Guardrails

| Guardrail | Implementation |
|---|---|
| Recursion Limits | `max_iterations=5` via LangGraph `RecursionLimit` |
| Purification Node | Validates tool output + masks PII before any LLM call |
| Confidence Scoring | If score < 0.7 → HITL queue (no hallucinated insights) |
| State Rollback | LangGraph `MemorySaver` checkpointer + `/rewind` endpoint |
| Rate-Limit Retry | Exponential back-off (3 attempts) in `ingest_node` |

## 🔐 Privacy Architecture

- **Least Privilege OAuth**: GitHub `repo:read` + `user:email` only; Gmail `metadata` only (no body)
- **PII Anonymiser**: Names, emails, card numbers, SSNs replaced with `[TOKEN]` before LLM
- **Sovereign Storage**: Every vector embedding in `user_{id}` namespace; Supabase Row-Level Security enforced
- **AES-256 Encryption**: OAuth tokens encrypted at rest with key-rotation support

## 📊 Admin Control Plane

Navigate to `/admin`:
- **Token Heatmap** — Recharts Treemap showing which agents burn the most tokens
- **Agent Health Table** — success rates, HITL counts, avg iterations per source
- **Quota Monitor** — per-user daily token cap (default 50k tokens / $5/month)

## 🛠️ Environment Variables

See `.env.example` for full list. Required:
- `OPENAI_API_KEY` — GPT-4o synthesiser
- `DATABASE_URL` — Supabase Postgres
- `REDIS_URL` — BullMQ queue backend
- `GITHUB_CLIENT_ID/SECRET` — GitHub OAuth
- `GOOGLE_CLIENT_ID/SECRET` — Gmail + YouTube OAuth
- `NEXTAUTH_SECRET` — NextAuth.js session signing
- `ENCRYPTION_KEY_CURRENT` — AES-256 key for OAuth token storage

## 📡 API Endpoints (Agent Hub)

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/harvest` | Enqueue a harvest job |
| `GET` | `/status/{job_id}` | Poll job status |
| `GET` | `/status/stream/{job_id}` | SSE live status stream |
| `POST` | `/rewind/{job_id}` | Restore to a checkpoint |
| `GET` | `/rewind/{job_id}/history` | List all checkpoints |
| `GET` | `/admin/health` | Agent health per source |
| `GET` | `/admin/heatmap` | Token burn heatmap |
| `GET` | `/admin/users/{id}/quota` | Per-user token quota |
