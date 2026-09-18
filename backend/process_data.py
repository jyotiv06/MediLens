import os
import re
import numpy as np
import pandas as pd
import uuid
from datetime import datetime
from normalizer import normalize_brand, normalize_strength, normalize_dosage_form, normalize_salt, extract_form_from_name

RAW_DIR = "../data/raw"
PROCESSED_DIR = "../data/processed"

# --- Synthetic pricing (ONLY used if the raw dataset has no real Price column) ---
# This is a disclosed placeholder so the demo's savings feature is non-trivial,
# NOT real market pricing. Document this in README > Limitations.
def synthesize_price(brand_name: str, salt: str, strength: str, rng) -> float:
    strength_num = 1.0
    m = re.search(r'(\d+(\.\d+)?)', str(strength))
    if m:
        strength_num = max(float(m.group(1)), 1.0)

    base = 2.0 + 0.03 * strength_num  # mild scaling with strength

    # Heuristic: if the brand name doesn't echo the salt name, treat it as a
    # "branded" listing and give it a price premium over generic-sounding ones.
    brand_first_word = str(brand_name).lower().split(' ')[0] if brand_name else ""
    is_branded = brand_first_word not in str(salt).lower()
    premium = rng.uniform(2.0, 4.5) if is_branded else rng.uniform(1.0, 1.5)

    noise = rng.uniform(0.9, 1.15)
    return round(base * premium * noise, 2)


def process_medicines():
    raw_file = os.path.join(RAW_DIR, "Medicine_Details.csv")
    if not os.path.exists(raw_file):
        print(f"Raw file not found at {raw_file}.")
        return

    print("Reading and normalizing dataset...")
    df = pd.read_csv(raw_file)
    df = df.dropna(subset=['Medicine Name', 'Composition'])

    processed_df = pd.DataFrame()

    processed_df['id'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]

    # Apply strict normalizers
    processed_df['brandName'] = df['Medicine Name'].apply(normalize_brand)
    processed_df['salt'] = df['Composition'].apply(normalize_salt)

    # Extract or infer strength if present in name/composition
    raw_strengths = df['Composition'].astype(str)
    processed_df['strength'] = raw_strengths.apply(normalize_strength)

    # Derive dosage form from the medicine name instead of hardcoding "Tablet"
    processed_df['dosageForm'] = df['Medicine Name'].astype(str).apply(extract_form_from_name)

    if 'Price' in df.columns:
        prices = df['Price'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
        processed_df['price'] = pd.to_numeric(prices, errors='coerce').fillna(10.0)
    else:
        print("WARNING: raw dataset has no 'Price' column — generating disclosed "
              "SYNTHETIC prices for demo purposes only (see README > Limitations).")
        rng = np.random.default_rng(42)  # fixed seed so prices are reproducible across runs
        processed_df['price'] = [
            synthesize_price(b, s, st, rng)
            for b, s, st in zip(processed_df['brandName'], processed_df['salt'], processed_df['strength'])
        ]

    processed_df['source'] = df['Manufacturer'] if 'Manufacturer' in df.columns else "1mg Scraped"
    processed_df['sourceDate'] = datetime.today().strftime('%Y-%m-%d')

    # Deduplicate on normalized fields
    initial_count = len(processed_df)
    processed_df = processed_df.drop_duplicates(subset=['brandName', 'salt'])
    print(f"Cleaned & Normalized: Removed {initial_count - len(processed_df)} duplicates.")

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    output_file = os.path.join(PROCESSED_DIR, "medicines_processed.csv")
    processed_df.to_csv(output_file, index=False)

    print(f"Success! Normalized dataset saved to {output_file}")
    print(processed_df[['brandName', 'salt', 'strength', 'dosageForm', 'price']].head(5))

if __name__ == "__main__":
    process_medicines()