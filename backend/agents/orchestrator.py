"""
Orchestrator

Runs the full SBI Saarthi agent pipeline for one customer, in order:

  AA Ingestion -> Behavior -> NBA -> Compliance -> Channel -> Engagement

and assembles an explainability log along the way, recording what each
agent did and why. This is the single entrypoint the API layer (and
eventually the frontend) calls — everything else in agents/ is an
internal building block.
"""

from datetime import datetime

from agents.aa_ingestion import get_customer_data
from agents.behavior import analyze_behavior
from agents.nba import decide_next_action
from agents.compliance import check_compliance
from agents.channel import select_channel
from agents.engagement import generate_message


def _log_step(log: list, agent: str, message: str) -> None:
    """Appends one timestamped step to the explainability log."""
    log.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "agent": agent,
        "message": message,
    })


def run_saarthi(customer_id: str) -> dict:
    """
    Runs the full agent pipeline for one customer and returns a single
    result dict containing:
      - the customer's raw AA snapshot
      - the behavior summary
      - the final decision (action, channel, message, etc.)
      - the full explainability log
    """
    log = []

    # 1. AA Ingestion
    customer = get_customer_data(customer_id)
    _log_step(
        log, "AA Ingestion Agent",
        f"Retrieved {len(customer['accounts'])} accounts for {customer['name']} "
        f"under consented AA scope."
    )

    # 2. Behavior & Life-Event Detection
    behavior_summary = analyze_behavior(customer_id)
    _log_step(
        log, "Behavior Agent",
        f"Wellness score {behavior_summary['wellness_score']}/100 "
        f"(trend: {behavior_summary['wellness_trend']}). "
        f"Financially stressed: {behavior_summary['is_financially_stressed']}."
    )

    # 3. Next Best Action
    nba_decision = decide_next_action(behavior_summary)
    _log_step(
        log, "NBA Agent",
        f"Decision: {nba_decision['action']}. Reason: {nba_decision['reason']}"
    )

    # 4. Compliance
    compliance_result = check_compliance(customer_id, behavior_summary, nba_decision)
    if compliance_result["compliance_ok"]:
        _log_step(log, "Compliance Agent", "All checks passed. Action approved as-is.")
    else:
        flagged = [c for c in compliance_result["compliance_checks"] if not c["passed"]]
        details = " | ".join(c["detail"] for c in flagged)
        _log_step(log, "Compliance Agent", f"Action modified. {details}")

    # 5. Channel Selection
    final_decision = select_channel(behavior_summary, compliance_result["decision"])
    _log_step(
        log, "Channel Agent",
        f"Channel: {final_decision['channel']}. {final_decision.get('channel_reason', '')}"
    )

    # 6. Engagement
    final_decision = generate_message(behavior_summary, final_decision)
    _log_step(log, "Engagement Agent", "Message generated and ready for delivery.")

    _log_step(log, "Explainability Agent", "Full reasoning chain logged and auditable.")

    return {
        "customer": customer,
        "behavior_summary": behavior_summary,
        "final_decision": final_decision,
        "compliance_checks": compliance_result["compliance_checks"],
        "explainability_log": log,
    }


if __name__ == "__main__":
    import json

    for cid in ["CUST_1001", "CUST_1002", "CUST_1003", "CUST_1004"]:
        result = run_saarthi(cid)
        print(f"\n{'='*60}")
        print(f"{result['customer']['name']}")
        print(f"{'='*60}")
        print(f"Action: {result['final_decision']['action']}")
        print(f"Channel: {result['final_decision']['channel']}")
        print(f"Message: {result['final_decision']['message']}")
        print(f"\nExplainability log:")
        for step in result["explainability_log"]:
            print(f"  [{step['timestamp']}] {step['agent']}: {step['message']}")