from agents.aa_ingestion import get_customer_data

STRESS_LOAN_BURDEN_THRESHOLD = 50  # % of inflow going to EMIs
STRESS_WELLNESS_DROP_THRESHOLD = 15  # points dropped to count as "sharp decline"

def analyze_behavior(customer_id: str) -> dict:
    """
    Reads a customer's AA data and produces a behavior summary:
    - whether they show signs of financial stress
    - their wellness score trend (up/down/flat)
    - the detected signals and key metrics, ready for the NBA agent
    """
    customer = get_customer_data(customer_id)

    # TODO 1: wellness trend
    current = customer["wellness_score"]
    previous = customer["wellness_score_prev"]
    if current > previous:
        wellness_trend = "up"
    elif current < previous:
        wellness_trend = "down"
    else:
        wellness_trend = "flat"

    # TODO 2: financial stress flag
    loan_burden = customer["metrics"]["loan_burden_pct"]
    wellness_drop = previous - current  # positive number if score fell
    is_financially_stressed = (
        loan_burden > STRESS_LOAN_BURDEN_THRESHOLD
        or wellness_drop > STRESS_WELLNESS_DROP_THRESHOLD
    )

    # TODO 3: summary dict
    return {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "wellness_score": current,
        "wellness_trend": wellness_trend,
        "is_financially_stressed": is_financially_stressed,
        "loan_burden_pct": loan_burden,
        "signals": customer["signals"],
        "digital_activity_score": customer["digital_activity_score"],
        "language_pref": customer["language_pref"],
    }


if __name__ == "__main__":
    result = analyze_behavior("CUST_1003")  # Priya — should show stress
    print(result)