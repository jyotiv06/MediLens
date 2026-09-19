import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from difflib import SequenceMatcher, get_close_matches
from mangum import Mangum
import time

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

matcher = MedicineMatcher(dataframe=df)

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
    request_start = time.perf_counter()
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
        medicine_names = df[name_col].astype(str).tolist()

        best_matches = get_close_matches(
            query,
            medicine_names,
            n=1,
            cutoff=FUZZY_SUGGEST_THRESHOLD / 100
        )

        if best_matches:
            best_match_name = best_matches[0]
            best_match_score = (
                SequenceMatcher(
                    None,
                    query.lower(),
                    best_match_name.lower()
                ).ratio() * 100
            )

            if best_match_score >= FUZZY_AUTO_THRESHOLD:
                match_row = df[df[name_col].astype(str) == best_match_name]

            elif best_match_score >= FUZZY_SUGGEST_THRESHOLD:
                raise HTTPException(
                    status_code=300,
                    detail={
                        "type": "AMBIGUOUS",
                        "message": f"No exact match for '{query}'.",
                        "suggestion": best_match_name,
                        "suggestionScore": round(best_match_score, 1)
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
        pipeline_start = time.perf_counter()
        result = matcher.full_search_pipeline(
            query_brand=brand_name_val,
            query_salt=target_salt,
            query_strength=target_strength,
            query_form=target_form,
            exclude_id=row.get('id'),
            queried_price=queried_price_val
        )
        print(
            f"[TIMING] candidate lookup: "
            f"{time.perf_counter() - pipeline_start:.3f}s"
        )
        result['queriedBrandDetails'] = {
            "name": brand_name_val,
            "price": queried_price_val,
            "salt": target_salt,
            "strength": target_strength,
            "dosageForm": target_form
        }
        print(
            f"[TIMING] total request: "
            f"{time.perf_counter() - request_start:.3f}s"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

handler = Mangum(app)