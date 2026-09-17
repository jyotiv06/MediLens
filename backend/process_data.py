import os
import pandas as pd
import uuid
from datetime import datetime

RAW_DIR = "../data/raw"
PROCESSED_DIR = "../data/processed"

def process_medicines():
    raw_file = os.path.join(RAW_DIR, "Medicine_Details.csv")
    if not os.path.exists(raw_file):
        print(f"❌ Raw file not found at {raw_file}.")
        return

    print("🔄 Reading 11k Medicine Details dataset...")
    df = pd.read_csv(raw_file)
    print(f"Total raw rows loaded: {len(df)}")

    # 1. Drop rows with missing names or composition
    df = df.dropna(subset=['Medicine Name', 'Composition'])

    processed_df = pd.DataFrame()
    
    # 2. Map columns to strict schema requirements
    processed_df['id'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
    processed_df['brandName'] = df['Medicine Name'].str.strip().str.title()
    processed_df['salt'] = df['Composition'].str.strip().str.title()
    processed_df['strength'] = "N/A"
    processed_df['dosageForm'] = "Tablet/Capsule"
    processed_df['packSize'] = "Standard Pack"
    
    # Robust price cleaning: remove ₹, Rs, commas, etc. and convert safely
    if 'Price' in df.columns:
        prices = df['Price'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
        processed_df['price'] = pd.to_numeric(prices, errors='coerce').fillna(10.0) # default fallback price if missing
    else:
        processed_df['price'] = 10.0

    processed_df['source'] = df['Manufacturer'] if 'Manufacturer' in df.columns else "1mg Scraped"
    processed_df['sourceDate'] = datetime.today().strftime('%Y-%m-%d')

    # 3. Deduplicate
    initial_count = len(processed_df)
    processed_df = processed_df.drop_duplicates(subset=['brandName', 'salt'])
    print(f"🧹 Cleaned data: Removed {initial_count - len(processed_df)} duplicates.")

    # 4. Save output
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    output_file = os.path.join(PROCESSED_DIR, "medicines_processed.csv")
    processed_df.to_csv(output_file, index=False)
    
    print(f"✅ Success! Processed dataset saved to {output_file}")
    print(f"Total processed rows: {len(processed_df)}")
    print(processed_df.head(3))

if __name__ == "__main__":
    process_medicines()