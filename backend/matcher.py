import os
import pandas as pd
from rapidfuzz import process, fuzz
from normalizer import normalize_brand, normalize_salt
from verifier import MedicineVerifier
from analyzer import evaluate_match_confidence, calculate_pricing_and_savings

PROCESSED_FILE = "../data/processed/medicines_processed.csv"

class MedicineMatcher:
    def __init__(self):
        if os.path.exists(PROCESSED_FILE):
            self.df = pd.read_csv(PROCESSED_FILE)
        else:
            self.df = pd.DataFrame(columns=['id', 'brandName', 'salt', 'strength', 'dosageForm', 'price'])

    def full_search_pipeline(self, query_brand: str, query_salt: str, query_strength: str, query_form: str):
        """
        Executes the complete production pipeline for any searched medicine:
        1. Candidate Retrieval & Verification
        2. Confidence Scoring & Abstention Logic
        3. Price Comparison & Potential Savings Calculation
        """
        if self.df.empty:
            return {"error": "Dataset is empty."}

        candidates = self.df.to_dict(orient="records")
        results = []

        for cand in candidates:
            # 1. Fuzzy match score on brand name
            fuzzy_score = fuzz.WRatio(query_brand, cand['brandName'])
            
            # Skip low-relevance candidates early to save processing
            if fuzzy_score < 40:
                continue

            # 2. Deterministic Verification
            verification = MedicineVerifier.verify_candidate(
                input_salt=query_salt,
                input_strength=query_strength,
                input_form=query_form,
                candidate=cand
            )

            # 3. Confidence Evaluation & Abstention Rule
            confidence_eval = evaluate_match_confidence(verification["checks"], fuzzy_score)

            # 4. Pricing & Savings (Assuming a baseline branded price for comparison, e.g., 100.0)
            # In production, this compares the scanned brand price vs alternative price
            baseline_branded_price = 100.0 
            pricing = calculate_pricing_and_savings(baseline_branded_price, cand['price'])

            results.append({
                "brandName": cand['brandName'],
                "salt": cand['salt'],
                "strength": cand['strength'],
                "dosageForm": cand['dosageForm'],
                "price": cand['price'],
                "verification": verification,
                "confidence": confidence_eval,
                "pricing": pricing
            })

        # Filter only those that passed HIGH confidence (abstaining from low confidence guesses)
        actionable_results = [r for r in results if r["confidence"]["action"] == "SHOW_RESULT"]

        return {
            "query": {"brand": query_brand, "salt": query_salt, "strength": query_strength, "dosageForm": query_form},
            "total_candidates_evaluated": len(results),
            "actionable_matches_count": len(actionable_results),
            "matches": actionable_results[:5] # Return top 5 actionable matches
        }

if __name__ == "__main__":
    matcher = MedicineMatcher()
    print("Running full production pipeline across all 11,501 medicines for: 'Dolo 650'")
    
    output = matcher.full_search_pipeline(
        query_brand="Dolo 650",
        query_salt="Paracetamol",
        query_strength="650 mg",
        query_form="Tablet"
    )
    
    print(f"Total Evaluated Candidates: {output['total_candidates_evaluated']}")
    print(f"Actionable High-Confidence Matches: {output['actionable_matches_count']}")
    if output['matches']:
        print("\nTop Match Example:")
        top = output['matches'][0]
        print(f"- Brand: {top['brandName']}")
        print(f"- Confidence: {top['confidence']['confidenceScore']} ({top['confidence']['confidenceLevel']})")
        print(f"- Action: {top['confidence']['action']}")
        print(f"- Savings vs Baseline: {top['pricing']['potentialSavings']}%")