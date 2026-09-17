import os
import pandas as pd
from rapidfuzz import process, fuzz
from normalizer import normalize_brand, normalize_salt

PROCESSED_FILE = "../data/processed/medicines_processed.csv"

class MedicineMatcher:
    def __init__(self):
        if os.path.exists(PROCESSED_FILE):
            self.df = pd.read_csv(PROCESSED_FILE)
        else:
            self.df = pd.DataFrame(columns=['id', 'brandName', 'salt', 'strength', 'dosageForm', 'price'])

    def search(self, query: str, limit: int = 5):
        """
        Tiered search pipeline:
        1. Exact match
        2. Normalized match
        3. Fuzzy candidate retrieval
        """
        if self.df.empty:
            return {"match_type": "none", "candidates": []}

        query_clean = query.strip()

        # 1. Exact Match (case-insensitive)
        exact_matches = self.df[self.df['brandName'].str.lower() == query_clean.lower()]
        if not exact_matches.empty:
            return {
                "match_type": "exact",
                "query": query,
                "candidates": exact_matches.to_dict(orient="records")
            }

        # 2. Normalized Match
        norm_query = normalize_brand(query_clean)
        norm_matches = self.df[self.df['brandName'].apply(normalize_brand) == norm_query]
        if not norm_matches.empty:
            return {
                "match_type": "normalized",
                "query": query,
                "candidates": norm_matches.to_dict(orient="records")
            }

        # 3. Fuzzy Candidate Retrieval
        # Note: Fuzzy matching only finds candidates. It does not declare medical equivalence.
        brand_choices = self.df['brandName'].tolist()
        fuzzy_results = process.extract(
            query_clean, 
            brand_choices, 
            scorer=fuzz.WRatio, 
            limit=limit
        )

        matched_indices = [res[2] for res in fuzzy_results if res[1] > 60] # threshold score > 60
        candidates = self.df.iloc[matched_indices].to_dict(orient="records")

        return {
            "match_type": "fuzzy_candidates",
            "query": query,
            "disclaimer": "Fuzzy matching only finds candidates. It does not declare medical equivalence.",
            "candidates": candidates
        }

if __name__ == "__main__":
    matcher = MedicineMatcher()
    print("Testing matcher with typo query: 'Paracetmol 650'")
    result = matcher.search("Paracetmol 650")
    print(result)