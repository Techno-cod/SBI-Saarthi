"""
Channel Selection Agent

By the time this agent runs, Compliance has already settled on a final
action and often already implies a channel (e.g. Escalate -> Human RM).
This agent's job is to confirm the channel choice, and apply one extra
layer of logic: even for actions where Compliance didn't set a channel,
pick the best one based on the customer's digital activity score and
language preference.
"""

VOICE_THRESHOLD = 0.15


def select_channel(behavior_summary: dict, decision: dict) -> dict:
    """
    Finalizes the delivery channel for a given decision.
    Returns the decision dict with a confirmed 'channel' field and a
    short note explaining why that channel was chosen.
    """
    final = dict(decision)
    action = final["action"]

    # Actions that already have a fixed, non-negotiable channel
    if action == "Escalate":
        final["channel"] = "Human RM"
        final["channel_reason"] = "Escalations always route to a human Relationship Manager."
        return final

    if action == "Do Nothing":
        final["channel"] = "None"
        final["channel_reason"] = "No action taken, no channel needed."
        return final

    if action == "Educate":
        # Educate nudges walk the customer through a feature inside the app
        # (e.g. "tap here to pay your bill"), so they only make sense as an
        # in-app, interactive notification — never a voice call.
        final["channel"] = "In-app notification"
        final["channel_reason"] = (
            "Educate actions are interactive, step-by-step app walkthroughs, "
            "so they must be delivered in-app regardless of digital activity score."
        )
        return final

    # For everything else (Sell, Advise, Defer), choose based on
    # digital activity score and language preference
    digital_score = behavior_summary["digital_activity_score"]
    language = behavior_summary["language_pref"]

    if digital_score < VOICE_THRESHOLD:
        final["channel"] = "Voice call (regional language)"
        final["channel_reason"] = (
            f"Digital activity score is {digital_score}, below the {VOICE_THRESHOLD} "
            f"threshold. A voice call in {language} will reach this customer far more "
            f"reliably than an app notification."
        )
    else:
        final["channel"] = "In-app notification"
        final["channel_reason"] = (
            f"Digital activity score is {digital_score}, above the {VOICE_THRESHOLD} "
            f"threshold. Customer is comfortable with the app, so an in-app "
            f"notification is the most natural channel."
        )

    return final


if __name__ == "__main__":
    from agents.behavior import analyze_behavior
    from agents.nba import decide_next_action
    from agents.compliance import check_compliance

    for cid in ["CUST_1001", "CUST_1002", "CUST_1003", "CUST_1004"]:
        summary = analyze_behavior(cid)
        nba_decision = decide_next_action(summary)
        compliance_result = check_compliance(cid, summary, nba_decision)
        final_decision = select_channel(summary, compliance_result["decision"])

        print(f"{summary['name']:20s} -> {final_decision['action']:10s} | "
              f"channel: {final_decision['channel']}")