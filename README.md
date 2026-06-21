# SBI Saarthi — An Agentic Next Best Action Engine for Inclusive Banking

**SBI Hackathon @ HackCulture | Theme: Agentic AI & Emerging Tech | Problem Statement 3: Digital Engagement**

SBI Saarthi is a multi-agent AI system that proactively engages SBI customers based on their real-time financial behavior, life events, and complete financial picture (accessed via the RBI Account Aggregator framework, with consent). Unlike rule-based marketing engines or always-on chatbots, Saarthi's core is a **Next Best Action (NBA) Agent** that decides — for every customer, every time — whether to **Sell, Advise, Educate, Defer, Escalate, or do nothing at all**. Every decision is checked against compliance rules, routed through the right channel (in-app, voice call in a regional language, or a human Relationship Manager), and logged with a full, auditable reasoning trail.

## Why this matters

Most engagement engines optimize for one thing: push a product, increase conversion. Saarthi is built around a different question: **what does this specific customer actually need right now — and is now even the right time to reach out at all?**

A financially healthy customer gets a relevant, well-timed product nudge. A customer who already has a feature but isn't using it gets a digital adoption nudge, not a sales pitch. A customer showing signs of financial stress gets **zero marketing** — instead, Saarthi suppresses outreach and escalates them to a human Relationship Manager for a proactive wellness conversation. That restraint is deliberate, and it's the part of the system we're proudest of.

## Architecture

```
AA Data Ingestion Agent
        ↓
Behavior & Life-Event Detection Agent
        ↓
Next Best Action (NBA) Agent  ← the core decision-maker
        ↓
Compliance & Consent Agent    ← approves, downgrades, or blocks the action
        ↓
Channel Selection Agent       ← app, voice call, or human RM
        ↓
Engagement Agent              ← generates the actual message
        ↓
Explainability Agent          ← logs the full reasoning chain
```

Each stage is a separate, independently testable Python module under `backend/agents/`. The `orchestrator.py` runs the full pipeline for a given customer and assembles a step-by-step explainability log, exactly as shown in the architecture above.

### Agent responsibilities

| Agent | Role |
|---|---|
| **AA Ingestion** | Simulates an Account Aggregator data pull — a customer's accounts, loans, and investments across multiple banks, scoped to what they've actually consented to share |
| **Behavior & Life-Event Detection** | Derives a Financial Wellness Score, wellness trend, and a financial-stress flag from the raw data |
| **Next Best Action (NBA)** | Decides the single best action for this customer right now: Sell, Advise, Educate, Defer, Escalate, or Do Nothing |
| **Compliance & Consent** | Validates the NBA decision against AA consent scope and outreach frequency caps — can downgrade or block an action before it ever reaches the customer |
| **Channel Selection** | Picks the delivery channel (in-app notification, regional-language voice call, or human RM) based on the customer's digital activity and the nature of the action |
| **Engagement** | Generates the actual customer-facing message, or an internal note for the relationship management team when the action is Escalate or Do Nothing |

The NBA Agent supports two modes: a deterministic rule-based mock mode (used for development, zero API cost) and a live Claude API mode for real LLM reasoning, toggled with a single flag in `agents/nba.py`.

## Demo personas

The prototype ships with four realistic personas to demonstrate the full range of NBA decisions:

- **Anita Sharma** (Lucknow, urban salaried) — healthy finances, high-interest loan elsewhere → **Sell** (balance transfer), in-app
- **Ramkhelawan Yadav** (Bihar, Jan Dhan account holder) — low digital activity, no insurance consent on file → **Advise**, voice call in Bhojpuri
- **Priya Mehta** (Mumbai, financially stressed) — 62% EMI burden, wellness score dropped from 61 to 34 → **Escalate**, marketing suppressed, routed to a human RM
- **Karthik Iyer** (Chennai, digital non-adopter) — has the app and UPI but hasn't used them in 90 days → **Educate**, in-app walkthrough nudge

## Tech stack

- **Backend**: Python, FastAPI
- **Agent reasoning**: rule-based mock mode by default; Claude API (Anthropic) for live LLM reasoning
- **Frontend**: React (Vite)
- **Data**: Mock Account Aggregator dataset (`backend/data/personas.json`), modeled loosely on the real AA FIP/FIU data-sharing structure

## Running it locally

**Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend runs at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

Open the frontend in your browser, select a persona from the left panel, and click **Run Saarthi Agents** to see the full pipeline execute live, with a step-by-step explainability log.

## Roadmap

This prototype focuses on Digital Engagement (Problem Statement 3), but the same agent architecture is designed to extend to:
- **Customer Acquisition** — a conversational onboarding agent reusing the same NBA/Compliance/Channel pipeline for new-to-bank leads
- **Digital Adoption** — the Educate action path generalized into a full adaptive in-app tutorial system

