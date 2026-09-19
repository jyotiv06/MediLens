import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rapidfuzz import process, fuzz
from mangum import Mangum

from matcher import MedicineMatcher

app = FastAPI(title="MediLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    brand_name: str

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "medicines_processed.csv")
df = pd.read_csv(DATA_PATH)
name_col = "brandName"

matcher = MedicineMatcher()

FUZZY_AUTO_THRESHOLD = 90     
FUZZY_SUGGEST_THRESHOLD = 60  

@app.get("/")
def health_check():
    return {
        "status": "MediLens API is running",
        "medicines_loaded": len(df),
    }

@app.post("/api/search")
def search_alternatives(payload: SearchRequest):
    query = payload.brand_name.strip()
    query_lower = query.lower()

    match_row = pd.DataFrame()

    exact_matches = df[df[name_col].astype(str).str.lower() == query_lower]
    if not exact_matches.empty:
        match_row = exact_matches

    if match_row.empty:
        startswith_matches = df[df[name_col].astype(str).str.lower().str.startswith(query_lower)]
        if not startswith_matches.empty:
            startswith_matches = startswith_matches.loc[
                startswith_matches[name_col].astype(str).str.len().sort_values().index
            ]
            match_row = startswith_matches.iloc[[0]]

    if match_row.empty and 'salt' in df.columns:
        match_row = df[df['salt'].astype(str).str.lower().str.contains(query_lower, na=False)]

    if match_row.empty:
        best_match = process.extractOne(
            query, df[name_col].astype(str).tolist(), scorer=fuzz.ratio
        )
        if best_match and best_match[1] >= FUZZY_AUTO_THRESHOLD:
            match_row = df[df[name_col].astype(str) == best_match[0]]
        elif best_match and best_match[1] >= FUZZY_SUGGEST_THRESHOLD:
            raise HTTPException(
                status_code=300,
                detail={
                    "type": "AMBIGUOUS",
                    "message": f"No exact match for '{query}'.",
                    "suggestion": best_match[0],
                    "suggestionScore": round(best_match[1], 1)
                }
            )

    if match_row.empty:
        raise HTTPException(status_code=404, detail="We couldn't find this medicine. Please check the spelling or try a different brand name.")

    row = match_row.iloc[0]
    target_salt = row.get('salt', query)
    target_strength = row.get('strength', '650 mg')
    target_form = row.get('dosageForm', 'Tablet')
    brand_name_val = row.get(name_col, query)
    queried_price_val = float(row.get('price', 100.0))

    try:
        result = matcher.full_search_pipeline(
            query_brand=brand_name_val,
            query_salt=target_salt,
            query_strength=target_strength,
            query_form=target_form,
            exclude_id=row.get('id'),
            queried_price=queried_price_val
        )
        result['queriedBrandDetails'] = {
            "name": brand_name_val,
            "price": queried_price_val,
            "salt": target_salt,
            "strength": target_strength,
            "dosageForm": target_form
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

handler = Mangum(app)