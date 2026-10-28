
import unittest

from risk_model import (
    calculate_flood_risk,
    calculate_flood_risk_details,
    get_risk_state,
)


class RiskModelTests(unittest.TestCase):

    def test_original_score_is_preserved(self):
        score = calculate_flood_risk(50, 50, 5)
        self.assertEqual(score, 50.0)

    def test_zero_risk(self):
        score = calculate_flood_risk(0, 0, 0)
        self.assertEqual(score, 0.0)

    def test_maximum_risk(self):
        score = calculate_flood_risk(100, 100, 10)
        self.assertEqual(score, 100.0)

    def test_missing_sensor_is_reported(self):
        result = calculate_flood_risk_details(
            50, None, 5
        )

        self.assertEqual(result["data_quality"], "Partial")
        self.assertEqual(
            result["missing_signals"],
            ["soil_moisture"],
        )
        self.assertEqual(result["coverage_percent"], 70)

    def test_all_missing_readings_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_flood_risk_details(None, None, None)

    def test_negative_readings_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_flood_risk(-1, 50, 5)

    def test_risk_states(self):
        self.assertEqual(get_risk_state(10), "Stable")
        self.assertEqual(get_risk_state(30), "Vulnerable")
        self.assertEqual(get_risk_state(60), "Critical")
        self.assertEqual(get_risk_state(90), "Hazard")


if __name__ == "__main__":
    unittest.main()
