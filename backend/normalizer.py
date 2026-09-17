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
    # Clean and sort ingredients alphabetically for consistent matching (e.g., A + B == B + A)
    parts = [p.strip().title() for p in salt.split('+')]
    parts.sort()
    return ' + '.join(parts)