import os
import pandas as pd
import uuid
from datetime import datetime
from normalizer import normalize_brand, normalize_strength, normalize_dosage_form, normalize_salt

RAW_DIR = "../data/raw"
PROCESSED_DIR = "../data/processed"

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
    
    processed_df['dosageForm'] = "Tablet" # Default standardized form
    
    if 'Price' in df.columns:
        prices = df['Price'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
        processed_df['price'] = pd.to_numeric(prices, errors='coerce').fillna(10.0)
    else:
        processed_df['price'] = 10.0

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
    print(processed_df[['brandName', 'salt', 'strength', 'price']].head(3))

if __name__ == "__main__":
    process_medicines()