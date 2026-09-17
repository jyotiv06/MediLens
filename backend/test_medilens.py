import unittest
from normalizer import normalize_brand, normalize_strength, normalize_dosage_form, normalize_salt
from verifier import MedicineVerifier
from analyzer import evaluate_match_confidence, calculate_pricing_and_savings
from matcher import MedicineMatcher

class TestMediLensCoreEngine(unittest.TestCase):

    def setUp(self):
        self.matcher = MedicineMatcher()

    def test_1_exact_medicine(self):
        """✓ exact medicine"""
        norm = normalize_brand("Dolo 650")
        self.assertEqual(norm, "Dolo 650")

    def test_2_spelling_variation(self):
        """✓ spelling variation / fuzzy match"""
        result = self.matcher.full_search_pipeline("Paracetmol 650", "Paracetamol", "650 mg", "Tablet")
        self.assertGreaterEqual(result["actionable_matches_count"], 0)

    def test_3_formatting_variation(self):
        """✓ formatting variation (hyphens, spaces)"""
        self.assertEqual(normalize_brand("DOLO-650"), "Dolo 650")
        self.assertEqual(normalize_strength("500 MG"), "500 mg")

    def test_4_correct_strength(self):
        """✓ correct strength"""
        cand = {"salt": "Paracetamol (650Mg)", "strength": "650 mg", "dosageForm": "Tablet"}
        res = MedicineVerifier.verify_candidate("Paracetamol", "650 mg", "Tablet", cand)
        self.assertEqual(res["checks"]["strength"], "✓")

    def test_5_wrong_strength(self):
        """✓ wrong strength (should reject)"""
        cand = {"salt": "Paracetamol (500Mg)", "strength": "500 mg", "dosageForm": "Tablet"}
        res = MedicineVerifier.verify_candidate("Paracetamol", "650 mg", "Tablet", cand)
        self.assertEqual(res["status"], "REJECT")

    def test_6_correct_dosage_form(self):
        """✓ correct dosage form"""
        self.assertEqual(normalize_dosage_form("tablet"), "Tablet")
        self.assertEqual(normalize_dosage_form("TAB"), "Tablet")

    def test_7_wrong_dosage_form(self):
        """✓ wrong dosage form"""
        form1 = normalize_dosage_form("Tablet")
        form2 = normalize_dosage_form("Syrup")
        self.assertNotEqual(form1, form2)

    def test_8_unknown_medicine(self):
        """✓ unknown medicine / abstention"""
        result = self.matcher.full_search_pipeline("Xyzabc123NonExistent", "UnknownSalt", "999 mg", "Tablet")
        self.assertEqual(result["actionable_matches_count"], 0)

    def test_9_low_confidence(self):
        """✓ low confidence (abstain)"""
        checks = {"salt": "✓", "strength": "✗", "dosageForm": "✓"}
        eval_res = evaluate_match_confidence(checks, 30.0)
        self.assertEqual(eval_res["action"], "ABSTAIN")

    def test_10_missing_price(self):
        """✓ missing/invalid price safety handle"""
        pricing = calculate_pricing_and_savings("invalid", None)
        self.assertEqual(pricing["potentialSavings"], 0.0)

    def test_11_price_calculation(self):
        """✓ price calculation"""
        pricing = calculate_pricing_and_savings(100.0, 40.0)
        self.assertEqual(pricing["potentialDifference"], 60.0)
        self.assertEqual(pricing["potentialSavings"], 60.0)

if __name__ == "__main__":
    unittest.main()