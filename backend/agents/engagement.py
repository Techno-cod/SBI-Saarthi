"""
Engagement Agent

Generates the actual message (or internal RM note, for Escalate/Do Nothing)
that gets delivered to the customer. Uses simple per-action templates so
this works fully offline with zero API cost. A live LLM mode can be added
later the same way nba.py supports one, by swapping generate_message's
body for a Claude API call.
"""

PRODUCT_LABELS = {
    "loan": "a lower-rate loan balance transfer",
    "insurance": "a suitable insurance plan",
    "deposit": "a recurring deposit",
    "investment": "an investment option suited to your goals",
}


def _guess_product_label(behavior_summary: dict) -> str:
    signals_text = " ".join(behavior_summary["signals"]).lower()
    if "loan" in signals_text or "interest" in signals_text:
        return PRODUCT_LABELS["loan"]
    if "insurance" in signals_text:
        return PRODUCT_LABELS["insurance"]
    if "investment" in signals_text or "mutual fund" in signals_text:
        return PRODUCT_LABELS["investment"]
    return PRODUCT_LABELS["deposit"]


def generate_message(behavior_summary: dict, final_decision: dict) -> dict:
    """
    Takes the final decision (post-compliance, post-channel) and generates
    the actual outbound message or internal note.
    Returns the decision dict with a new 'message' field added.
    """
    result = dict(final_decision)
    name = behavior_summary["name"]
    action = result["action"]
    channel = result.get("channel", "None")

    if action == "Sell":
        product = _guess_product_label(behavior_summary)
        if channel == "Voice call (regional language)":
            message = (
                f"Namaste {name} ji! Hum dekh rahe hain ki aapke liye {product} "
                f"faydemand ho sakta hai. Kya hum iske baare mein aapko zyada "
                f"jaankari de sakte hain?"
            )
        else:
            message = (
                f"Hi {name}, based on your recent activity we think {product} "
                f"could genuinely help you. Want to take a quick look?"
            )

    elif action == "Advise":
        if behavior_summary.get("customer_id") == "CUST_1002":
            message = (
                "नमस्ते! हम SBI सारथी बोलत बानी। रउरा खाता में हाल ही में सरकारी योजना के "
                "पैसा जमा भइल बा। बधाई हो! अगर रउरा चाहीं, त एह पैसा के सुरक्षित बचत खातिर "
                "हर महीना छोट-छोट किस्त में रिकरिंग डिपॉजिट शुरू कर सकत बानी। अधिक जानकारी "
                "खातिर नजदीकी SBI शाखा से संपर्क करीं। धन्यवाद।"
            )
        else:
            message = (
                f"Hi {name}, we noticed some patterns in your finances worth a look. "
                f"We're not pitching anything today — just sharing a quick tip that "
                f"might help you plan better. Want to see it?"
            )

    elif action == "Educate":
        message = (
            f"Hi {name}, did you know you can do this in seconds right from your "
            f"app, without a branch visit? Tap below and we'll walk you through it."
        )

    elif action == "Defer":
        message = (
            f"[Internal note] No outreach to {name} this cycle. Revisit in 30 days "
            f"once their current financial situation settles."
        )

    elif action == "Escalate":
        message = (
            f"[Internal RM note] {name} (ID: {behavior_summary['customer_id']}) is "
            f"showing signs of financial stress. Loan burden: "
            f"{behavior_summary['loan_burden_pct']}%. Wellness trend: "
            f"{behavior_summary['wellness_trend']}. Recommend a proactive wellness "
            f"call to discuss restructuring options. Do NOT pitch new products."
        )

    else:  # Do Nothing
        message = (
            f"[Internal note] No action taken for {name} this cycle. "
            f"{result.get('reason', '')}"
        )

    result["message"] = message
    return result


if __name__ == "__main__":
    from agents.behavior import analyze_behavior
    from agents.nba import decide_next_action
    from agents.compliance import check_compliance
    from agents.channel import select_channel

    for cid in ["CUST_1001", "CUST_1002", "CUST_1003", "CUST_1004"]:
        summary = analyze_behavior(cid)
        nba_decision = decide_next_action(summary)
        compliance_result = check_compliance(cid, summary, nba_decision)
        channeled_decision = select_channel(summary, compliance_result["decision"])
        final = generate_message(summary, channeled_decision)

        print(f"\n--- {summary['name']} ---")
        print(f"Action:  {final['action']}")
        print(f"Channel: {final['channel']}")
        print(f"Message: {final['message']}")