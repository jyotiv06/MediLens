from normalizer import normalize_salt, normalize_strength, normalize_dosage_form

class MedicineVerifier:
    @staticmethod
    def verify_candidate(input_salt: str, input_strength: str, input_form: str, candidate: dict) -> dict:
        cand_salt_raw = candidate.get('salt', '')
        cand_strength = candidate.get('strength', '')
        cand_form = candidate.get('dosageForm', '')

        # Normalize inputs
        norm_input_salt = normalize_salt(input_salt)
        norm_input_strength = normalize_strength(input_strength)
        norm_input_form = normalize_dosage_form(input_form)

        # Check if candidate salt string already embeds the strength (common in scrapers)
        cand_salt_normalized = normalize_salt(cand_salt_raw)
        
        # Salt match: check if base names match
        salt_match = norm_input_salt.lower() in cand_salt_normalized.lower() and bool(norm_input_salt)
        
        # Strength match: check if strength is explicitly in candidate strength OR embedded in candidate salt
        strength_match = (
            norm_input_strength in normalize_strength(cand_strength) or 
            norm_input_strength.lower() in cand_salt_raw.lower()
        )

        # Form match
        form_match = (norm_input_form == normalize_dosage_form(cand_form))

        is_valid = salt_match and strength_match and form_match

        return {
            "candidate_id": candidate.get('id'),
            "candidate_brand": candidate.get('brandName'),
            "checks": {
                "salt": "✓" if salt_match else "✗",
                "strength": "✓" if strength_match else "✗",
                "dosageForm": "✓" if form_match else "✗"
            },
            "status": "PASS" if is_valid else "REJECT"
        }