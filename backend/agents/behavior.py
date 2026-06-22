"""
Behavior & Life-Event Detection Agent

Reads a customer's AA data and produces a behavior summary including:
- Financial Wellness Score breakdown (four sub-scores, 25 points each)
- Wellness trend (up / down / flat)
- Financial stress flag
- Detected signals and key metrics
"""

from agents.aa_ingestion import get_customer_data

STRESS_LOAN_BURDEN_THRESHOLD = 50   # % of inflow going to EMIs
STRESS_WELLNESS_DROP_THRESHOLD = 15  # points dropped to count as "sharp decline"


def _score_savings_trend(customer: dict) -> dict:
    """
    Up to 25 points based on wellness score trend direction and magnitude.
    Proxy for savings health since we don't have month-by-month data in mock.
    """
    current = customer["wellness_score"]
    previous = customer["wellness_score_prev"]
    drop = previous - current

    if drop > 20:
        score = 4
        label = "Sharply declining"
    elif drop > 10:
        score = 8
        label = "Declining"
    elif drop > 0:
        score = 12
        label = "Slightly declining"
    elif drop == 0:
        score = 16
        label = "Stable"
    elif drop > -10:
        score = 20
        label = "Improving"
    else:
        score = 25
        label = "Strongly improving"

    return {"score": score, "max": 25, "label": label}


def _score_debt_burden(customer: dict) -> dict:
    """
    Up to 25 points. Lower loan burden % = higher score.
    """
    burden = customer["metrics"]["loan_burden_pct"]

    if burden >= 60:
        score = 2
        label = f"{burden}% of inflow — critical"
    elif burden >= 50:
        score = 6
        label = f"{burden}% of inflow — high"
    elif burden >= 35:
        score = 12
        label = f"{burden}% of inflow — moderate"
    elif burden >= 20:
        score = 18
        label = f"{burden}% of inflow — manageable"
    elif burden > 0:
        score = 22
        label = f"{burden}% of inflow — low"
    else:
        score = 25
        label = "No loan burden"

    return {"score": score, "max": 25, "label": label}


def _score_investments(customer: dict) -> dict:
    """
    Up to 25 points based on whether the customer has any investment products.
    """
    investments = customer["metrics"].get("investments", "None").lower()
    accounts = customer.get("accounts", [])

    has_mutual_fund = any(
        "mutual fund" in a.get("type", "").lower() or "sip" in a.get("type", "").lower()
        for a in accounts
    )
    has_fd = any("fixed deposit" in a.get("type", "").lower() or "fd" in a.get("type", "").lower() for a in accounts)
    has_rd = any("recurring deposit" in a.get("type", "").lower() for a in accounts)

    if has_mutual_fund and (has_fd or has_rd):
        score = 25
        label = "Diversified — MF + deposits"
    elif has_mutual_fund:
        score = 20
        label = "Mutual fund holdings"
    elif has_fd:
        score = 18
        label = "Fixed deposit only"
    elif has_rd:
        score = 14
        label = "Recurring deposit only"
    elif investments != "none":
        score = 14
        label = "Some investments"
    else:
        score = 4
        label = "No investments"

    return {"score": score, "max": 25, "label": label}


def _score_emergency_cover(customer: dict) -> dict:
    """
    Up to 25 points based on months of emergency cover.
    """
    months = customer["metrics"].get("emergency_cover_months", 0)

    if months >= 6:
        score = 25
        label = f"{months} months — strong"
    elif months >= 3:
        score = 18
        label = f"{months} months — adequate"
    elif months >= 1:
        score = 10
        label = f"{months} months — low"
    else:
        score = 3
        label = f"{round(months, 1)} months — critical"

    return {"score": score, "max": 25, "label": label}


def analyze_behavior(customer_id: str) -> dict:
    """
    Reads a customer's AA data and produces a behavior summary including
    the Financial Wellness Score breakdown.
    """
    customer = get_customer_data(customer_id)

    current = customer["wellness_score"]
    previous = customer["wellness_score_prev"]

    if current > previous:
        wellness_trend = "up"
    elif current < previous:
        wellness_trend = "down"
    else:
        wellness_trend = "flat"

    loan_burden = customer["metrics"]["loan_burden_pct"]
    wellness_drop = previous - current
    is_financially_stressed = (
        loan_burden > STRESS_LOAN_BURDEN_THRESHOLD
        or wellness_drop > STRESS_WELLNESS_DROP_THRESHOLD
    )

    # Compute the four sub-scores
    breakdown = {
        "savings_trend": _score_savings_trend(customer),
        "debt_burden": _score_debt_burden(customer),
        "investments": _score_investments(customer),
        "emergency_cover": _score_emergency_cover(customer),
    }

    # Cross-check: sum of sub-scores should roughly match wellness_score
    # (in a real system these would be the source of truth;
    #  here we use the persona's pre-set wellness_score and the breakdown
    #  is an explanatory decomposition, not recomputed from scratch)
    computed_total = sum(v["score"] for v in breakdown.values())

    return {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "wellness_score": current,
        "wellness_score_prev": previous,
        "wellness_trend": wellness_trend,
        "wellness_breakdown": breakdown,
        "wellness_computed_total": computed_total,
        "is_financially_stressed": is_financially_stressed,
        "loan_burden_pct": loan_burden,
        "signals": customer["signals"],
        "digital_activity_score": customer["digital_activity_score"],
        "language_pref": customer["language_pref"],
    }


if __name__ == "__main__":
    for cid in ["CUST_1001", "CUST_1002", "CUST_1003", "CUST_1004"]:
        result = analyze_behavior(cid)
        print(f"\n--- {result['name']} (Wellness: {result['wellness_score']}/100) ---")
        for key, val in result["wellness_breakdown"].items():
            bar = "█" * val["score"] + "░" * (val["max"] - val["score"])
            print(f"  {key:20s} {val['score']:2d}/25  {bar}  {val['label']}")
        print(f"  {'computed total':20s} {result['wellness_computed_total']}/100")