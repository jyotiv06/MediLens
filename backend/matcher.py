import os
import pandas as pd
from normalizer import normalize_salt, normalize_strength, normalize_dosage_form
from verifier import MedicineVerifier
from analyzer import evaluate_match_confidence, calculate_pricing_and_savings
from rapidfuzz import fuzz

# Resolve relative to this file, not the current working directory, so `uvicorn`
# doesn't break depending on which folder it's launched from.
DEFAULT_DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "medicines_processed.csv"
)

class MedicineMatcher:
    def __init__(self, dataset_path=DEFAULT_DATASET_PATH):
        self.df = pd.read_csv(dataset_path)
        self.df['clean_salt'] = self.df['salt'].astype(str).apply(normalize_salt)
        self.df['clean_strength'] = self.df['strength'].astype(str).apply(normalize_strength)
        self.df['clean_form'] = self.df['dosageForm'].astype(str).apply(normalize_dosage_form)

    def full_search_pipeline(self, query_brand: str, query_salt: str, query_strength: str,
                              query_form: str, exclude_id: str = None):
        norm_query_form = str(normalize_dosage_form(query_form)).lower()

        # Filter candidates by matching dosage form and strict salt matching
        norm_query_salt = normalize_salt(query_salt)
        candidates = self.df[
            (self.df['clean_form'].astype(str).str.lower() == norm_query_form) &
            (self.df['clean_salt'].str.lower() == norm_query_salt.lower())
        ]

        # Fallback if strict salt match is empty: fall back to all rows of same form
        if candidates.empty:
            candidates = self.df[self.df['clean_form'].astype(str).str.lower() == norm_query_form]

        # Never let the queried medicine appear as its own "alternative"
        if exclude_id is not None:
            candidates = candidates[candidates['id'] != exclude_id]

        total_evaluated = len(candidates)
        actionable_matches = []
        baseline_price = candidates['price'].median() if not candidates.empty else 100.0

        for _, cand in candidates.iterrows():
            cand_dict = {
                "id": cand.get('id'),
                "brandName": cand.get('brandName', 'Unknown'),
                "salt": cand.get('salt', ''),
                "strength": cand.get('strength', ''),
                "dosageForm": cand.get('dosageForm', ''),
                "price": float(cand.get('price', 10.0))
            }

            # Call verifier matching verifier.py signature: verify_candidate(input_salt, input_strength, input_form, candidate)
            verification = MedicineVerifier.verify_candidate(
                query_salt,
                query_strength,
                query_form,
                cand_dict
            )

            if isinstance(verification, dict) and verification.get("status") == "PASS":
                # Compute fuzzy score between query brand and candidate brand name
                fuzz_score = float(fuzz.ratio(query_brand.lower(), str(cand_dict['brandName']).lower()))

                # Call analyzer matching analyzer.py signature: evaluate_match_confidence(verification_checks, fuzzy_score)
                confidence = evaluate_match_confidence(verification.get("checks", {}), fuzz_score)

                if confidence.get("action") == "SHOW_RESULT":
                    alt_price = cand_dict["price"]
                    pricing = calculate_pricing_and_savings(baseline_price, alt_price)

                    actionable_matches.append({
                        "brandName": cand_dict["brandName"],
                        "salt": cand_dict["salt"],
                        "strength": cand_dict["strength"],
                        "dosageForm": cand_dict["dosageForm"],
                        "price": alt_price,
                        "verification": verification,
                        "confidence": confidence,
                        "pricing": pricing
                    })

        # Sort actionable matches by lowest price
        actionable_matches = sorted(actionable_matches, key=lambda x: x['price'])

        return {
            "query": {
                "brand": query_brand,
                "salt": query_salt,
                "strength": query_strength,
                "dosageForm": query_form
            },
            "total_candidates_evaluated": total_evaluated,
            "actionable_matches_count": len(actionable_matches),
            "matches": actionable_matches[:5]
        }