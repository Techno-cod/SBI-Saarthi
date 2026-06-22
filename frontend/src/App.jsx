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
  const [activeTab, setActiveTab] = useState("console");
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

      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === "console" ? "active" : ""}`}
          onClick={() => setActiveTab("console")}
        >
          Agent Console
        </button>
        <button
          className={`tab-btn ${activeTab === "impact" ? "active" : ""}`}
          onClick={() => setActiveTab("impact")}
        >
          Impact Dashboard
        </button>
      </div>

      {activeTab === "console" && (
      <>
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
  <div className="wellness-breakdown">
    <div className="section-label">Wellness score breakdown</div>
    {Object.entries(result.behavior_summary.wellness_breakdown).map(([key, val]) => {
      const labels = {
        savings_trend: "Savings trend",
        debt_burden: "Debt burden",
        investments: "Investment coverage",
        emergency_cover: "Emergency cover",
      };
      const pct = (val.score / val.max) * 100;
      const barColor = pct >= 72 ? "var(--green)" : pct >= 48 ? "var(--amber)" : "var(--coral)";
      return (
        <div className="breakdown-row" key={key}>
          <div className="breakdown-header">
            <span className="breakdown-label">{labels[key]}</span>
            <span className="breakdown-score" style={{ color: barColor }}>
              {val.score}<span style={{ color: "var(--text3)" }}>/{val.max}</span>
            </span>
          </div>
          <div className="breakdown-bar-bg">
            <div
              className="breakdown-bar-fill"
              style={{ width: `${pct}%`, background: barColor }}
            />
          </div>
          <div className="breakdown-detail">{val.label}</div>
        </div>
      );
    })}
  </div>
)}

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
      </>
      )}

      {activeTab === "impact" && <ImpactDashboard />}
    </div>
  );
}

function ImpactDashboard() {
  const [hoveredAction, setHoveredAction] = useState(null);

  const metrics = [
    {
      label: "App engagement rate",
      before: 22,
      after: 38,
      unit: "%",
      detail: "Customers actively using digital banking features monthly",
    },
    {
      label: "Cross-sell conversion",
      before: 3,
      after: 7.5,
      unit: "%",
      detail: "Product recommendations resulting in a completed action",
    },
    {
      label: "Rural digital outreach",
      before: 12,
      after: 16.8,
      unit: "%",
      detail: "Jan Dhan / low-digital-activity customers reached via any channel",
    },
  ];

  const actionDistribution = [
    { action: "Sell", pct: 38, color: "var(--green)", detail: "A relevant product is genuinely a good fit, with no signs of financial stress." },
    { action: "Advise", pct: 18, color: "var(--blue)", detail: "Customer gets general financial guidance, no specific product is pitched." },
    { action: "Educate", pct: 22, color: "var(--amber)", detail: "Customer already has a digital feature available but isn't using it — nudged toward adoption, not a sale." },
    { action: "Defer", pct: 9, color: "var(--purple)", detail: "Timing isn't right — re-evaluated automatically in a future cycle, no outreach sent now." },
    { action: "Escalate", pct: 8, color: "var(--red)", detail: "Signs of financial stress detected. Marketing is suppressed and the case is routed to a human Relationship Manager." },
    { action: "Do Nothing", pct: 5, color: "var(--text3)", detail: "Frequency cap reached or no meaningful signal — Saarthi deliberately stays silent this cycle." },
  ];

  const hovered = actionDistribution.find((a) => a.action === hoveredAction);

  return (
    <div className="impact-page">
      <div className="impact-hero">
        <div className="impact-hero-label">Projected impact across SBI's digital customer base</div>
        <div className="impact-hero-number">
          +25<span className="impact-hero-unit">%</span>
        </div>
        <div className="impact-hero-sub">average uplift in relevant product adoption, modeled from a 90-day simulated rollout</div>
      </div>

      <div className="impact-metrics-grid">
        {metrics.map((m, i) => (
          <div className="impact-metric-card" key={i}>
            <div className="impact-metric-label">{m.label}</div>
            <div className="impact-metric-row">
              <div className="impact-metric-before">
                <span className="impact-metric-tag">Before</span>
                <span className="impact-metric-value-small">{m.before}{m.unit}</span>
              </div>
              <div className="impact-metric-arrow">→</div>
              <div className="impact-metric-after">
                <span className="impact-metric-tag">After</span>
                <span className="impact-metric-value-big">{m.after}{m.unit}</span>
              </div>
            </div>
            <div className="impact-metric-detail">{m.detail}</div>
          </div>
        ))}
      </div>

      <div className="impact-section">
        <div className="impact-section-title">Next Best Action distribution</div>
        <div className="impact-section-sub">
          Across simulated customer interactions — note that 13% of decisions result in <strong>no marketing</strong> (Defer + Do Nothing), and a further 8% are escalated to a human Relationship Manager instead of being sold to.
        </div>
        <div className="action-bar">
          {actionDistribution.map((a, i) => (
            <div
              key={i}
              className={`action-bar-segment ${hoveredAction === a.action ? "hovered" : ""}`}
              style={{ width: `${a.pct}%`, background: a.color }}
              onMouseEnter={() => setHoveredAction(a.action)}
              onMouseLeave={() => setHoveredAction(null)}
            />
          ))}
        </div>

        <div className={`action-tooltip ${hovered ? "visible" : ""}`}>
          {hovered ? (
            <>
              <span className="action-tooltip-dot" style={{ background: hovered.color }} />
              <span className="action-tooltip-label">{hovered.action}</span>
              <span className="action-tooltip-pct">{hovered.pct}%</span>
              <span className="action-tooltip-detail">{hovered.detail}</span>
            </>
          ) : (
            <span className="action-tooltip-hint">Hover a segment for details</span>
          )}
        </div>

        <div className="action-legend">
          {actionDistribution.map((a, i) => (
            <span
              className={`action-legend-item ${hoveredAction === a.action ? "hovered" : ""}`}
              key={i}
              onMouseEnter={() => setHoveredAction(a.action)}
              onMouseLeave={() => setHoveredAction(null)}
            >
              <span className="action-legend-dot" style={{ background: a.color }} />
              {a.action} <span className="action-legend-pct">{a.pct}%</span>
            </span>
          ))}
        </div>
      </div>

      <div className="impact-footnote">
        Figures are projected estimates based on a simulated 90-day rollout across the four demo personas and comparable
        fintech financial-inclusion program benchmarks (RBI Digital Payments Index, NPCI UPI adoption reports). Intended to
        illustrate expected directional impact, not measured production results.
      </div>
    </div>
  );
}