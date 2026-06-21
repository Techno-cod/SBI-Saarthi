import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function scoreClass(score) {
  if (score >= 70) return "score-high";
  if (score >= 50) return "score-mid";
  return "score-low";
}

function scoreHex(score) {
  if (score >= 70) return "#3FB950";
  if (score >= 50) return "#E3B341";
  return "#F4845F";
}

function decisionClass(action) {
  const map = {
    Sell: "decision-sell",
    Advise: "decision-advise",
    Educate: "decision-educate",
    Defer: "decision-defer",
    Escalate: "decision-escalate",
    "Do Nothing": "decision-nothing",
  };
  return map[action] || "decision-nothing";
}

export default function App() {
  const [personas, setPersonas] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [visibleLogSteps, setVisibleLogSteps] = useState(0);

  // Load the persona list once on mount
  useEffect(() => {
    fetch(`${API_BASE}/personas`)
      .then((res) => res.json())
      .then(setPersonas)
      .catch(() => setError("Could not reach backend. Is uvicorn running on port 8000?"));
  }, []);

  const selectedPersona = personas.find((p) => p.customer_id === selectedId);

  async function runAgents() {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setVisibleLogSteps(0);

    try {
      const res = await fetch(`${API_BASE}/saarthi/${selectedId}`);
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const data = await res.json();
      setResult(data);

      // Animate the explainability log appearing step by step, like a
      // live agent pipeline running, instead of dumping it all at once.
      const totalSteps = data.explainability_log.length;
      for (let i = 1; i <= totalSteps; i++) {
        await new Promise((r) => setTimeout(r, 450));
        setVisibleLogSteps(i);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function selectPersona(id) {
    setSelectedId(id);
    setResult(null);
    setVisibleLogSteps(0);
    setError(null);
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-dot" />
          <div>
            <div className="logo-text">SBI Saarthi</div>
            <div className="logo-sub">Agentic Next Best Action Engine</div>
          </div>
        </div>
        <div className="header-badge">● LIVE BACKEND</div>
      </header>

      <div className="main">
        {/* LEFT: persona list */}
        <div className="panel left-panel">
          <div className="panel-header">Select Persona</div>
          {personas.length === 0 && !error && (
            <div className="placeholder">Loading personas…</div>
          )}
          {personas.map((p) => (
            <div
              key={p.customer_id}
              className={`persona-item ${selectedId === p.customer_id ? "active" : ""}`}
              onClick={() => selectPersona(p.customer_id)}
            >
              <span className={`persona-score ${scoreClass(p.wellness_score)}`}>
                {p.wellness_score}
              </span>
              <div className="persona-name">{p.name}</div>
              <div className="persona-tag">{p.location} · {p.language_pref}</div>
            </div>
          ))}
        </div>

        {/* CENTER: AA data snapshot */}
        <div className="panel center-panel">
          <div className="panel-header">AA Data Snapshot</div>
          {!selectedPersona && (
            <div className="placeholder">
              Select a customer persona to load their Account Aggregator data snapshot.
            </div>
          )}
          {selectedPersona && (
            <>
              <div className="wellness-bar">
                <div className="wellness-header">
                  <div>
                    <div className="wellness-label">Financial Wellness Score</div>
                    <div
                      className="wellness-score-big"
                      style={{ color: scoreHex(selectedPersona.wellness_score) }}
                    >
                      {selectedPersona.wellness_score}
                      <span style={{ fontSize: 14, color: "#6E7681" }}>/100</span>
                    </div>
                    <div
                      className="wellness-trend"
                      style={{
                        color:
                          selectedPersona.wellness_score >= selectedPersona.wellness_score_prev
                            ? "#3FB950"
                            : "#F4845F",
                      }}
                    >
                      {selectedPersona.wellness_score >= selectedPersona.wellness_score_prev ? "↑" : "↓"} from{" "}
                      {selectedPersona.wellness_score_prev} (prev. period)
                    </div>
                  </div>
                </div>
                <div className="wellness-gauge">
                  <div
                    className="wellness-fill"
                    style={{
                      width: `${selectedPersona.wellness_score}%`,
                      background: scoreHex(selectedPersona.wellness_score),
                    }}
                  />
                </div>
              </div>

              {result && (
                <div className="accounts-section">
                  <div className="section-label">Accounts (via AA consent)</div>
                  {result.customer.accounts.map((a, i) => (
                    <div className="account-row" key={i}>
                      <div>
                        <div className="account-bank">{a.bank} · {a.type}</div>
                        <div className="account-type">{a.detail}</div>
                      </div>
                      <div className={`account-amount ${a.interest_rate ? "account-rate" : ""}`}>
                        {a.amount}
                        {a.interest_rate ? ` · ${a.interest_rate}%` : ""}
                      </div>
                    </div>
                  ))}

                  <div className="section-label" style={{ marginTop: 14 }}>
                    Detected signals
                  </div>
                  {result.customer.signals.map((s, i) => (
                    <span className="signal-pill signal-warn" key={i}>
                      {s}
                    </span>
                  ))}
                </div>
              )}

              {!result && (
                <div className="placeholder">
                  Click <strong>Run Saarthi Agents</strong> to load this customer's full account data.
                </div>
              )}
            </>
          )}
        </div>

        {/* RIGHT: agent decision */}
        <div className="panel right-panel">
          <div className="panel-header">Agent Decision</div>
          <button
            className={`run-btn ${loading ? "loading" : ""}`}
            disabled={!selectedId || loading}
            onClick={runAgents}
          >
            {loading ? "Running agents…" : "▶ Run Saarthi Agents"}
          </button>

          {error && <div className="error-box">{error}</div>}

          {!result && !error && (
            <div className="placeholder">
              Run the agents to see the Next Best Action decision and generated engagement message.
            </div>
          )}

          {result && (
            <>
              <div className={`decision-box ${decisionClass(result.final_decision.action)}`}>
                <div className="decision-label">NBA Decision</div>
                <div className="decision-action">{result.final_decision.action}</div>
                <div className="decision-body">{result.final_decision.reason}</div>
              </div>

              {result.final_decision.marketing_suppressed && (
                <div className="decision-box decision-nothing" style={{ marginTop: 0 }}>
                  <div className="decision-label">Marketing</div>
                  <div className="decision-action" style={{ fontSize: 13 }}>
                    Suppressed
                  </div>
                </div>
              )}

              <div className="msg-box">
                <div className="channel-badge">⟶ {result.final_decision.channel}</div>
                <div className="msg-label">
                  {result.final_decision.action === "Escalate" ? "Internal RM note" : "Engagement message"}
                </div>
                <div className="msg-text">{result.final_decision.message}</div>
              </div>

              <div className="compliance-section">
                <div className="compliance-title">Compliance checks</div>
                {result.compliance_checks.map((c, i) => (
                  <div className="compliance-row" key={i}>
                    <span>{c.check}</span>
                    <span className={c.passed ? "compliance-check" : "compliance-block"}>
                      {c.passed ? "✓ Passed" : "✗ Flagged"}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* BOTTOM: explainability log */}
      <div className="log-panel">
        <div className="panel-header">Explainability Log</div>
        <div className="log-stream">
          {!result && <div className="log-empty">Waiting for agent run…</div>}
          {result &&
            result.explainability_log.slice(0, visibleLogSteps).map((step, i) => (
              <div className="log-line" key={i}>
                <span className="log-agent">{step.agent}</span>
                <span className="log-arrow">→</span>
                <span className="log-msg">{step.message}</span>
              </div>
            ))}
          {result && visibleLogSteps < result.explainability_log.length && (
            <span className="log-cursor" />
          )}
        </div>
      </div>
    </div>
  );
}