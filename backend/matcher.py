import os
import pandas as pd
from rapidfuzz import process, fuzz
from normalizer import normalize_brand, normalize_salt
from verifier import MedicineVerifier

PROCESSED_FILE = "../data/processed/medicines_processed.csv"

class MedicineMatcher:
    def __init__(self):
        if os.path.exists(PROCESSED_FILE):
            self.df = pd.read_csv(PROCESSED_FILE)
        else:
            self.df = pd.DataFrame(columns=['id', 'brandName', 'salt', 'strength', 'dosageForm', 'price'])

    def search_and_verify(self, query_salt: str, query_strength: str, query_form: str, brand_query: str = None, limit: int = 10):
        """
        Performs fuzzy/normalized retrieval and then runs deterministic verification 
        across ALL candidates to filter out mismatches (e.g., wrong strength).
        """
        if self.df.empty:
            return {"match_type": "none", "verified_candidates": []}

        # 1. Retrieve candidates (using fuzzy matching on brand name or filtering by salt)
        candidates = self.df.to_dict(orient="records")
        
        verified_results = []
        for cand in candidates:
            # Run deterministic verification on EVERY candidate
            verification = MedicineVerifier.verify_candidate(
                input_salt=query_salt,
                input_strength=query_strength,
                input_form=query_form,
                candidate=cand
            )
            
            # Keep track of check results for all candidates
            cand_copy = cand.copy()
            cand_copy["verification"] = verification
            verified_results.append(cand_copy)

        # 2. Filter for those that passed deterministic verification
        passed_candidates = [c for c in verified_results if c["verification"]["status"] == "PASS"]

        return {
            "query": {"salt": query_salt, "strength": query_strength, "dosageForm": query_form},
            "total_evaluated": len(candidates),
            "total_passed": len(passed_candidates),
            "verified_candidates": passed_candidates
        }

if __name__ == "__main__":
    matcher = MedicineMatcher()
    print("Running verification across all 11,501 medicines for: Paracetamol 650 mg Tablet")
    
    # Test query input
    result = matcher.search_and_verify(
        query_salt="Paracetamol", 
        query_strength="650 mg", 
        query_form="Tablet"
    )
    
    print(f"Total Evaluated: {result['total_evaluated']}")
    print(f"Total Passed (Exact Match on Salt, Strength & Form): {result['total_passed']}")
    print("Sample Passed Candidates:")
    for cand in result['verified_candidates'][:3]:
        print(f"- {cand['brandName']} | Strength: {cand['strength']} | Status: {cand['verification']['status']}")