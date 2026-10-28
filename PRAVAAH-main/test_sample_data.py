"""Basic structural checks for the illustrative synthetic sample CSV."""
import csv
from pathlib import Path
import unittest

CSV_PATH = (
    Path(__file__).resolve().parent
    / "sample_environmental_readings.csv"
)

REQUIRED_COLUMNS = {
    "soil_moisture_pct", "river_level_m", "temperature_c", "humidity_pct", "data_source"
}

class SampleDataTests(unittest.TestCase):
    def test_sample_csv_has_required_columns_and_rows(self):
        with CSV_PATH.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self.assertTrue(REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])))
            rows = list(reader)
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(row["data_source"] == "synthetic_example" for row in rows))

if __name__ == "__main__":
    unittest.main()
