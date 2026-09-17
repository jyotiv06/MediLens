def calculate_pricing_and_savings(branded_price: float, alternative_price: float) -> dict:
    """
    Calculates price difference and percentage savings safely,
    handling missing, zero, or invalid prices.
    """
    try:
        b_price = float(branded_price)
        a_price = float(alternative_price)
    except (TypeError, ValueError):
        return {
            "brandedPrice": branded_price,
            "alternativePrice": alternative_price,
            "potentialDifference": 0.0,
            "potentialSavings": 0.0,
            "status": "Invalid price data"
        }

    # Handle zero or negative branded price to prevent division by zero
    if b_price <= 0:
        return {
            "brandedPrice": b_price,
            "alternativePrice": a_price,
            "potentialDifference": max(0.0, b_price - a_price),
            "potentialSavings": 0.0,
            "status": "Zero/Negative base price"
        }

    potential_difference = round(b_price - a_price, 2)
    potential_savings = round((potential_difference / b_price) * 100, 2)

    return {
        "brandedPrice": b_price,
        "alternativePrice": a_price,
        "potentialDifference": potential_difference,
        "potentialSavings": potential_savings,
        "status": "SUCCESS"
    }

def evaluate_match_confidence(verification_checks: dict, fuzzy_score: float) -> dict:
    """
    Computes match confidence and enforces abstention logic:
    - HIGH confidence -> show result
    - LOW confidence -> don't guess (abstain)
    """
    salt_pass = verification_checks.get("salt") == "✓"
    strength_pass = verification_checks.get("strength") == "✓"
    form_pass = verification_checks.get("dosageForm") == "✓"

    # Base confidence calculation weighting deterministic checks + fuzzy score
    score = 0.0
    if salt_pass: score += 50.0
    if strength_pass: score += 30.0
    if form_pass: score += 10.0
    score += min(10.0, (fuzzy_score / 100.0) * 10.0)

    confidence_pct = round(score, 1)

    # Abstention Threshold: Must pass all three core checks and have high score
    is_high_confidence = salt_pass and strength_pass and form_pass and (confidence_pct >= 85.0)

    if is_high_confidence:
        action = "SHOW_RESULT"
        status_message = "HIGH confidence — match verified."
    else:
        action = "ABSTAIN"
        status_message = "LOW confidence — abstaining to avoid misidentification."

    return {
        "confidenceScore": f"{confidence_pct}%",
        "checks": {
            "activeIngredient": verification_checks.get("salt"),
            "strength": verification_checks.get("strength"),
            "dosageForm": verification_checks.get("dosageForm")
        },
        "confidenceLevel": "HIGH" if is_high_confidence else "LOW",
        "action": action,
        "message": status_message
    }

if __name__ == "__main__":
    # Test Pricing & Savings
    print("--- Testing Pricing Calculation ---")
    print(calculate_pricing_and_savings(150.00, 45.50))

    # Test High vs Low Confidence
    print("\n--- Testing High Confidence ---")
    checks_pass = {"salt": "✓", "strength": "✓", "dosageForm": "✓"}
    print(evaluate_match_confidence(checks_pass, 95.0))

    print("\n--- Testing Low Confidence (Abstention) ---")
    checks_fail = {"salt": "✓", "strength": "✗", "dosageForm": "✓"}
    print(evaluate_match_confidence(checks_fail, 40.0))