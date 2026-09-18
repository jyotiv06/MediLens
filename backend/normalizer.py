import re

def normalize_brand(name: str) -> str:
    if not isinstance(name, str):
        return ""
    # Replace hyphens/underscores with spaces (e.g., DOLO-650 -> DOLO 650)
    cleaned = re.sub(r'[-_]', ' ', name)
    # Collapse multiple spaces and Title Case
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned.title()

def normalize_strength(strength: str) -> str:
    if not isinstance(strength, str):
        return "N/A"
    # Standardize units: 500mg, 500 mg, 500 MG -> 500 mg
    match = re.search(r'(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg)', strength, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2).lower()}"
    return strength.strip().lower()

def normalize_dosage_form(form: str) -> str:
    if not isinstance(form, str):
        return "Tablet"
    form_lower = form.strip().lower()
    if 'tab' in form_lower:
        return 'Tablet'
    elif 'cap' in form_lower:
        return 'Capsule'
    elif 'syrup' in form_lower or 'suspension' in form_lower:
        return 'Syrup'
    elif 'inj' in form_lower:
        return 'Injection'
    return form.strip().title()

def normalize_salt(salt: str) -> str:
    if not isinstance(salt, str):
        return ""
    # Strip parenthetical strength annotations, e.g. "Paracetamol (500mg)" -> "Paracetamol".
    # Strength is verified separately (normalize_strength) — keeping it inside the salt
    # string caused tiny formatting drift ("500Mg" vs "500 Mg") to break exact-match
    # filtering and silently push rows into the unsafe fuzzy fallback path.
    cleaned = re.sub(r'\([^)]*\)', '', salt)
    # Clean and sort ingredients alphabetically for consistent matching (e.g., A + B == B + A)
    parts = [p.strip().title() for p in cleaned.split('+') if p.strip()]
    parts.sort()
    return ' + '.join(parts)

# --- Derive dosage form from the raw medicine name ---
# Fixes process_data.py hardcoding every row to "Tablet", which silently broke
# form-based verification for syrups, injections, capsules, etc.
FORM_KEYWORDS = [
    'tablet', 'capsule', 'syrup', 'suspension', 'injection',
    'cream', 'ointment', 'drop', 'gel', 'spray', 'lotion'
]

def extract_form_from_name(name: str) -> str:
    if not isinstance(name, str):
        return "Tablet"
    name_lower = name.lower()
    for kw in FORM_KEYWORDS:
        if kw in name_lower:
            return normalize_dosage_form(kw)
    return "Tablet"  # sane default when no form keyword is present in the name