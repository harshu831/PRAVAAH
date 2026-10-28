
import unittest

from models.pravaah_pipeline import assess_environment


class PipelineTests(unittest.TestCase):

    def test_complete_readings(self):
        result = assess_environment({
            "rainfall": 50,
            "soil_moisture": 50,
            "river_level": 5,
            "location": "Test Village",
        })

        self.assertEqual(result["risk_score"], 50.0)
        self.assertEqual(result["risk_state"], "Critical")
        self.assertEqual(result["coverage_percent"], 100)
        self.assertEqual(result["missing_sensors"], 0)
        self.assertIsInstance(result["cascade_events"], list)
        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 100)

    def test_missing_rainfall_skips_cascade(self):
        result = assess_environment({
            "rainfall": None,
            "soil_moisture": 50,
            "river_level": 5,
        })

        self.assertEqual(result["missing_sensors"], 1)
        self.assertEqual(result["cascade_events"], [])
        self.assertIn("Skipped", result["cascade_status"])

    def test_missing_soil_moisture_is_reported(self):
        result = assess_environment({
            "rainfall": 50,
            "soil_moisture": None,
            "river_level": 5,
        })

        self.assertIn(
            "soil_moisture",
            result["risk_details"]["missing_signals"],
        )
        self.assertLess(result["coverage_percent"], 100)

    def test_stale_data_reduces_confidence(self):
        readings = {
            "rainfall": 50,
            "soil_moisture": 50,
            "river_level": 5,
        }

        fresh = assess_environment(readings, data_age=0)
        stale = assess_environment(readings, data_age=60)

        self.assertLess(
            stale["confidence"],
            fresh["confidence"],
        )

    def test_invalid_data_age_is_rejected(self):
        with self.assertRaises(ValueError):
            assess_environment(
                {
                    "rainfall": 50,
                    "soil_moisture": 50,
                    "river_level": 5,
                },
                data_age=-1,
            )

    def test_invalid_input_type_is_rejected(self):
        with self.assertRaises(TypeError):
            assess_environment([50, 50, 5])


if __name__ == "__main__":
    unittest.main()
