import json
from pathlib import Path

PERSONAS_PATH = Path(__file__).parent.parent / "data" / "personas.json"

def load_personas() -> list[dict]:
    """Load all personas from the mock AA dataset."""
    with open(PERSONAS_PATH, "r") as f:
        return json.load(f)

def get_customer_data(customer_id: str) -> dict:
    """
    Simulates an Account Aggregator data pull for one customer.
    In production, this would call the AA's FIU endpoint with a consent token.
    Returns the customer's full financial snapshot, or raises if not found.
    """
    personas = load_personas()
    for persona in personas:
        if persona["customer_id"]==customer_id:
            return persona
    raise ValueError(f"No customer found with id: {customer_id}")

if __name__ == "__main__":
    data = get_customer_data("CUST_1001")
    print(data["name"], data["wellness_score"])