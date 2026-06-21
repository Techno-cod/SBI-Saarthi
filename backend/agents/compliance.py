"""
Compliance & Consent Agent

Sits between the NBA Agent and the Channel Selection Agent. Its job is to
validate that the NBA Agent's decision is actually allowed to proceed:
- Does the customer's AA consent scope cover the recommended product type?
- Has this customer already been contacted too many times recently
  (frequency cap)?
- Are there any hard "never contact" rules being violated (e.g. trying to
  Sell to a financially stressed customer, which should never happen if
  the NBA agent is working correctly, but compliance double-checks anyway)?

If a check fails, this agent can either BLOCK the action entirely or
DOWNGRADE it to a safer action (e.g. Sell -> Advise).
"""

# Product categories mapped to the consent scope they require.
# In a real AA integration these would come from the consent artifact;
# here we hardcode a simple mock scope per persona for demo purposes.
PRODUCT_CONSENT_REQUIREMENTS = {
    "loan": "LOAN",
    "insurance": "INSURANCE",
    "investment": "INVESTMENT",
    "deposit": "DEPOSIT",
}

# Mock consent scopes per customer (in a real system this comes from the
# AA consent artifact, not hardcoded). Default scope covers the basics.
MOCK_CONSENT_SCOPES = {
    "CUST_1001": ["DEPOSIT", "LOAN", "INVESTMENT", "INSURANCE"],
    "CUST_1002": ["DEPOSIT"],  # Ramkhelawan has NOT consented to insurance data
    "CUST_1003": ["DEPOSIT", "LOAN"],
    "CUST_1004": ["DEPOSIT", "INVESTMENT"],
}

MAX_OUTREACH_PER_WEEK = 2

# Mock: how many times we've already reached out to each customer this week.
# In a real system this would be a database query.
MOCK_OUTREACH_COUNT_THIS_WEEK = {
    "CUST_1001": 0,
    "CUST_1002": 1,
    "CUST_1003": 0,
    "CUST_1004": 0,
}


def check_compliance(customer_id: str, behavior_summary: dict, nba_decision: dict) -> dict:
    """
    Validates an NBA decision against compliance rules.

    Returns a dict with the (possibly modified) decision plus a compliance
    report explaining what was checked and what happened.
    """
    checks = []
    final_decision = dict(nba_decision)  # copy, so we can safely modify it
    blocked = False

    consent_scope = MOCK_CONSENT_SCOPES.get(customer_id, ["DEPOSIT"])
    outreach_count = MOCK_OUTREACH_COUNT_THIS_WEEK.get(customer_id, 0)

    # --- Check 1: hard safety rule, never sell to a stressed customer ---
    if behavior_summary["is_financially_stressed"] and final_decision["action"] == "Sell":
        checks.append({
            "check": "Stress override",
            "passed": False,
            "detail": "NBA recommended Sell to a financially stressed customer. "
                       "Downgrading to Escalate.",
        })
        final_decision["action"] = "Escalate"
        final_decision["channel"] = "Human RM"
        final_decision["marketing_suppressed"] = True
        final_decision["reason"] = (
            "Compliance override: original action was blocked because the customer "
            "shows signs of financial stress. Escalated to a human Relationship Manager."
        )
    else:
        checks.append({
            "check": "Stress override",
            "passed": True,
            "detail": "No conflict between financial stress status and recommended action.",
        })

    # --- Check 2: frequency cap ---
    if outreach_count >= MAX_OUTREACH_PER_WEEK and final_decision["action"] not in ("Escalate", "Do Nothing"):
        checks.append({
            "check": "Frequency cap",
            "passed": False,
            "detail": f"Customer already contacted {outreach_count} times this week "
                      f"(limit: {MAX_OUTREACH_PER_WEEK}). Blocking further outreach.",
        })
        final_decision["action"] = "Do Nothing"
        final_decision["channel"] = "None"
        final_decision["marketing_suppressed"] = True
        final_decision["reason"] = (
            f"Compliance override: outreach frequency cap reached for this week "
            f"({outreach_count}/{MAX_OUTREACH_PER_WEEK}). No further contact today."
        )
        blocked = True
    else:
        checks.append({
            "check": "Frequency cap",
            "passed": True,
            "detail": f"Outreach count this week: {outreach_count}/{MAX_OUTREACH_PER_WEEK}. Within limit.",
        })

    # --- Check 3: consent scope (only relevant if a product is being sold) ---
    if final_decision["action"] == "Sell":
        # crude keyword match against the customer's detected signals/loan type
        # to figure out what product category is implied
        signals_text = " ".join(behavior_summary["signals"]).lower()
        if "loan" in signals_text or "interest" in signals_text:
            required_scope = "LOAN"
        elif "insurance" in signals_text:
            required_scope = "INSURANCE"
        else:
            required_scope = "DEPOSIT"

        if required_scope not in consent_scope:
            checks.append({
                "check": "Consent scope",
                "passed": False,
                "detail": f"Customer has not consented to share '{required_scope}' data. "
                          f"Downgrading from Sell to Advise (generic guidance only).",
            })
            final_decision["action"] = "Advise"
            final_decision["reason"] = (
                f"Compliance override: a product recommendation was planned, but the "
                f"customer's AA consent scope does not include '{required_scope}'. "
                f"Downgraded to general financial guidance with no specific product named."
            )
        else:
            checks.append({
                "check": "Consent scope",
                "passed": True,
                "detail": f"Consent scope includes '{required_scope}'. Product recommendation permitted.",
            })
    else:
        checks.append({
            "check": "Consent scope",
            "passed": True,
            "detail": "No product recommendation in this action, consent scope check not applicable.",
        })

    all_passed = all(c["passed"] for c in checks)

    return {
        "decision": final_decision,
        "compliance_checks": checks,
        "compliance_ok": all_passed,
        "blocked": blocked,
    }


if __name__ == "__main__":
    from agents.behavior import analyze_behavior
    from agents.nba import decide_next_action

    for cid in ["CUST_1001", "CUST_1002", "CUST_1003", "CUST_1004"]:
        summary = analyze_behavior(cid)
        nba_decision = decide_next_action(summary)
        result = check_compliance(cid, summary, nba_decision)

        print(f"\n--- {summary['name']} ---")
        print(f"NBA proposed:      {nba_decision['action']}")
        print(f"Final action:      {result['decision']['action']}")
        print(f"Compliance ok:     {result['compliance_ok']}")
        for c in result["compliance_checks"]:
            status = "PASS" if c["passed"] else "FLAG"
            print(f"  [{status}] {c['check']}: {c['detail']}")