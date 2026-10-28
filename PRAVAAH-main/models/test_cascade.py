
import unittest

from cascade import (
    create_cascade_graph,
    predict_cascade,
    calculate_cascade_severity,
)


class CascadeTests(unittest.TestCase):

    def setUp(self):
        self.graph = create_cascade_graph()

    def test_heavy_rain_reaches_downstream_events(self):
        events = predict_cascade(
            self.graph,
            risk_score=80,
            rainfall=70,
            river_level=6,
        )

        names = {event["event"] for event in events}

        self.assertIn("Road Blockage", names)
        self.assertIn("Village Isolation", names)
        self.assertIn("Rescue Delay", names)

    def test_no_active_hazard_returns_no_events(self):
        events = predict_cascade(
            self.graph,
            risk_score=10,
            rainfall=10,
            river_level=1,
        )

        self.assertEqual(events, [])

    def test_event_delays_are_nonnegative(self):
        events = predict_cascade(
            self.graph,
            risk_score=80,
            rainfall=70,
            river_level=6,
        )

        for event in events:
            self.assertGreaterEqual(event["delay"], 0)

    def test_invalid_confidence_is_rejected(self):
        with self.assertRaises(ValueError):
            predict_cascade(
                self.graph,
                risk_score=80,
                rainfall=70,
                river_level=6,
                confidence=150,
            )

    def test_severity_is_nonnegative(self):
        events = predict_cascade(
            self.graph,
            risk_score=80,
            rainfall=70,
            river_level=6,
        )

        severity = calculate_cascade_severity(
            self.graph,
            events,
        )

        self.assertGreaterEqual(severity, 0)


if __name__ == "__main__":
    unittest.main()
