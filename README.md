# ♾️ Continuum: The Zero-Loss Knowledge Bridge

Continuum is an autonomous digital estate platform designed to harvest scattered digital work—from **GitHub** commits and **YouTube** learnings to **Gmail** receipts—into a structured, living knowledge graph. 

Built with a **privacy-first** ethos, Continuum utilizes self-correcting LangGraph agents to synthesize insights while ensuring PII (Personally Identifiable Information) never leaves your local context and token spend stays under a strict ceiling.

---

## 🚀 Key Pillars

* **Self-Correcting Harvesters:** Powered by **LangGraph**, agents don't just "run"—they reason. They validate tool outputs, scrub PII, and self-correct before final synthesis.
* **Privacy-as-Code:** * **OAuth Least Privilege:** We request only the absolute minimum scopes (e.g., `gmail.metadata` vs `gmail.read`).
    * **PII Masking:** Sensitive strings are anonymized (e.g., `[USER_NAME]`) before hitting the LLM.
    * **Sovereign Namespaces:** Knowledge graphs live in isolated vector namespaces.
* **Agentic Guardrails:** * **Recursion Limits:** Strict 5-iteration cap to prevent infinite loops and "Agentic Traps."
    * **Human-in-the-Loop (HITL):** Automatic routing to review queues for low-confidence insights.
    * **State Rewind:** Full history check-pointing allows for manual state reversion.
* **Token Observability:** Real-time monitoring of "Token Burn" heatmaps and agent success rates.

---

## 🏗️ Architecture (Turborepo)

Continuum is built as a high-performance monorepo to ensure type safety and separation of concerns between the agentic "brain" and the user interface.

* **`apps/agent-hub`**: FastAPI backend hosting the LangGraph agent state machine.
* **`apps/web`**: Next.js 14 (App Router) frontend with a custom Shipt-inspired dark theme.
* **`packages/security`**: AES-256 token encryption and regex-based PII masking.
* **`packages/database`**: Shared Prisma ORM models with **pgvector** support.
* **`packages/observability`**: OpenTelemetry tracing for long-running agent jobs.

---

## 🛠️ Technical Logic: The Synthesis Loop

The core logic resides in the `Self-Correcting Harvester`. The agent follows a strict graph-based flow:

1.  **Ingest:** Fetch data from connected silos.
2.  **Purify:** Intercept raw data, validate schema, and scrub PII.
3.  **Synthesize:** Generate structured output with a confidence score.
4.  **Route:**
    * If Confidence $C \ge 0.7$: Commit to Knowledge Graph.
    * If Confidence $C < 0.7$: Trigger **HITL** queue for manual review.

---

## 🖥️ UI Walkthrough

### 01. Secure Onboarding
Transparency is our default. Users are shown exactly what the agents can and cannot see before any data is touched.
![Onboarding](https://github.com/Sanidhya14321/Agent_01/blob/main/Screenshot%20From%202026-03-03%2020-51-56.png)

### 02. Connection Hub
Granular control over integrations. Each card displays the exact OAuth scopes requested.
![Connection Hub](https://github.com/Sanidhya14321/Agent_01/blob/main/Screenshot%20From%202026-03-03%2020-52-24.png)

### 03. Synthesized Insights
View the "Living Knowledge Graph" in action, with confidence scores and source attribution.
![Dashboard](https://github.com/Sanidhya14321/Agent_01/blob/main/Screenshot%20From%202026-03-03%2020-52-39.png)

### 04. Admin Control Plane
Monitor the "Token Burn Heatmap" to see which services are consuming the most resources.
![Admin Dashboard](https://github.com/Sanidhya14321/Agent_01/blob/main/Screenshot%20From%202026-03-03%2020-52-46.png)
![Admin Dashboard](https://github.com/Sanidhya14321/Agent_01/blob/main/Screenshot%20From%202026-03-03%2020-53-00.png)


---

## 🚦 Getting Started

### Prerequisites
* Node.js 20+ & pnpm
* Python 3.11+
* Docker & Docker Compose
* Supabase (local or cloud) for **pgvector**

### Installation

1.  **Clone & Install:**
    ```bash
    git clone [https://github.com/your-username/continuum.git](https://github.com/your-username/continuum.git)
    cd continuum
    pnpm install
    ```

2.  **Spin up Infrastructure:**
    ```bash
    cd infra && docker-compose up -d
    ```

3.  **Run Migrations:**
    ```bash
    pnpm run migrate
    ```

4.  **Launch Dev Environment:**
    ```bash
    pnpm dev
    ```

---

## 📜 License
Distributed under the MIT License.
