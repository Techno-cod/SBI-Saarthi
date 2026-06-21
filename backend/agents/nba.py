import os
import json
from anthropic import Anthropic

USE_LIVE_API = False  # flip to True once you have credits / are ready to demo

client = Anthropic() if USE_LIVE_API else None


def build_nba_prompt(behavior_summary: dict) -> str:
    """Builds the prompt for the NBA agent, given a behavior summary."""
    return f"""You are the Next Best Action Agent in SBI Saarthi, an agentic banking engagement system.

Customer: {behavior_summary['name']}
Wellness Score: {behavior_summary['wellness_score']}/100 (trend: {behavior_summary['wellness_trend']})
Financially stressed: {behavior_summary['is_financially_stressed']}
Loan burden: {behavior_summary['loan_burden_pct']}%
Digital activity score: {behavior_summary['digital_activity_score']}
Language preference: {behavior_summary['language_pref']}
Detected signals: {', '.join(behavior_summary['signals'])}

Choose ONE action: Sell, Advise, Educate, Defer, Escalate, Do Nothing

Rules:
- If financially stressed is True: NEVER Sell. Prefer Escalate or Do Nothing.
- If digital activity score < 0.15: prefer voice channel.
- If healthy financial signals with a clear product gap: Sell is appropriate.

Respond ONLY with valid JSON:
{{"action": "...", "reason": "...", "channel": "...", "marketing_suppressed": true/false}}"""


def get_mock_decision(behavior_summary: dict) -> dict:
    """
    Rule-based fallback that mimics what the LLM would decide.
    Used when USE_LIVE_API is False, or if the live call fails.

    Mirrors the same rules given to the LLM in build_nba_prompt, so the
    mock and live modes should usually agree on the obvious cases.
    """
    name = behavior_summary["name"]
    stressed = behavior_summary["is_financially_stressed"]
    digital_score = behavior_summary["digital_activity_score"]
    loan_burden = behavior_summary["loan_burden_pct"]
    trend = behavior_summary["wellness_trend"]
    signals = behavior_summary["signals"]
    has_unused_digital_features = any(
        "unused" in s.lower() or "never used" in s.lower() or "zero transactions" in s.lower()
        for s in signals
    )

    # Rule 1: financial stress always wins -> never sell, escalate instead
    if stressed:
        return {
            "action": "Escalate",
            "reason": (
                f"{name}'s loan burden is {loan_burden}% of monthly inflow and their "
                f"wellness score trend is '{trend}'. This indicates financial stress, "
                f"so no products are pitched. Routing to a human Relationship Manager "
                f"for a proactive wellness check instead."
            ),
            "channel": "Human RM",
            "marketing_suppressed": True,
        }

    # Rule 2: customer already has digital features but isn't using them ->
    # nudge adoption, don't sell a new product
    if has_unused_digital_features:
        return {
            "action": "Educate",
            "reason": (
                f"{name} already has digital banking features set up but the detected "
                f"signals show they aren't being used. The right intervention is a "
                f"contextual nudge to drive adoption of what they already have access "
                f"to, not a new product pitch."
            ),
            "channel": "In-app notification",
            "marketing_suppressed": False,
        }

    # Rule 3: very low digital activity and no existing unused features ->
    # reach them by voice in their own language with a simple, relevant product
    if digital_score < 0.15:
        return {
            "action": "Sell",
            "reason": (
                f"{name} has very low digital activity ({digital_score}), so a voice "
                f"call in their preferred language is more effective than an app "
                f"notification. Financial signals show no stress, so a simple, "
                f"relevant product nudge is appropriate."
            ),
            "channel": "Voice call (regional language)",
            "marketing_suppressed": False,
        }

    # Rule 4: healthy customer with no stress and no special channel need ->
    # standard sell via app
    return {
        "action": "Sell",
        "reason": (
            f"{name} shows no signs of financial stress and has reasonable digital "
            f"activity ({digital_score}). A relevant product recommendation via "
            f"in-app notification is appropriate."
        ),
        "channel": "In-app notification",
        "marketing_suppressed": False,
    }


def decide_next_action(behavior_summary: dict) -> dict:
    """Main entrypoint: returns an NBA decision dict, live or mocked."""
    if not USE_LIVE_API:
        return get_mock_decision(behavior_summary)

    prompt = build_nba_prompt(behavior_summary)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    return json.loads(text)


if __name__ == "__main__":
    # Quick manual test across all 4 personas
    from agents.behavior import analyze_behavior

    for cid in ["CUST_1001", "CUST_1002", "CUST_1003", "CUST_1004"]:
        summary = analyze_behavior(cid)
        decision = decide_next_action(summary)
        print(f"{summary['name']:20s} -> {decision['action']:10s} | "
              f"channel: {decision['channel']:28s} | suppressed: {decision['marketing_suppressed']}")