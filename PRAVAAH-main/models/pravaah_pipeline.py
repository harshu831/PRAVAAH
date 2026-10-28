
"""PRAVAAH integration pipeline.

Combines environmental risk, sensor confidence, and
disaster cascade analysis.

Outputs are prototype estimates, not validated forecasts.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from models.risk_model import (
    calculate_flood_risk_details,
    get_risk_state,
)
from models.uncertainty import (
    calculate_uncertainty,
    detect_blind_zone,
    get_confidence_status,
    get_uncertainty_message,
)
from models.cascade import (
    create_cascade_graph,
    predict_cascade,
    calculate_cascade_severity,
)


def _validate_nonnegative(name: str, value: Any) -> float:
    """Validate a finite, nonnegative numeric value."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{name} must be a finite number."
        ) from None

    if not isfinite(number) or number < 0:
        raise ValueError(
            f"{name} must be finite and nonnegative."
        )

    return number


def assess_environment(
    readings: dict[str, Any],
    *,
    data_age: float = 0,
    risk_trend: float = 0,
) -> dict[str, Any]:
    """Assess environmental risk, confidence, and cascade events."""

    if not isinstance(readings, dict):
        raise TypeError("readings must be a dictionary.")

    data_age = _validate_nonnegative("data_age", data_age)

    try:
        risk_trend = float(risk_trend)
    except (TypeError, ValueError):
        raise ValueError(
            "risk_trend must be a finite number."
        ) from None

    if not isfinite(risk_trend):
        raise ValueError("risk_trend must be a finite number.")

    rainfall = readings.get(
        "rainfall", readings.get("rainfall_mm")
    )
    soil_moisture = readings.get(
        "soil_moisture",
        readings.get("soil_moisture_percent"),
    )
    river_level = readings.get(
        "river_level", readings.get("river_level_m")
    )

    # The risk model validates readings and reports missing signals.
    details = calculate_flood_risk_details(
        rainfall,
        soil_moisture,
        river_level,
    )

    risk_score = details["risk_score"]
    risk_state = get_risk_state(risk_score)

    sensor_count = 3
    missing_sensors = len(details["missing_signals"])
    coverage = details["coverage_percent"] / 100.0

    blind_zone = detect_blind_zone(
        sensor_count=sensor_count,
        missing_sensors=missing_sensors,
        coverage=coverage,
    )

    confidence = calculate_uncertainty(
        sensor_count=sensor_count,
        missing_sensors=missing_sensors,
        data_age=data_age,
        coverage=coverage,
        risk_trend=risk_trend,
        blind_zone=blind_zone,
    )

    # Cascade prediction requires both rainfall and river level.
    # Skip it when either required sensor is missing.
    cascade_graph = create_cascade_graph()
    cascade_events = []
    cascade_severity = 0.0

    if rainfall is not None and river_level is not None:
        cascade_events = predict_cascade(
            graph=cascade_graph,
            risk_score=risk_score,
            rainfall=float(rainfall),
            river_level=float(river_level),
            confidence=confidence,
        )

        cascade_severity = calculate_cascade_severity(
            cascade_graph,
            cascade_events,
        )

        cascade_status = (
            "Completed"
            if cascade_events
            else "No active cascade events detected"
        )
    else:
        cascade_status = (
            "Skipped: rainfall or river-level reading missing"
        )

    return {
        "location": readings.get("location", "Unknown"),
        "risk_score": risk_score,
        "risk_state": risk_state,
        "risk_details": details,
        "confidence": confidence,
        "confidence_status": get_confidence_status(confidence),
        "uncertainty_message": get_uncertainty_message(confidence),
        "blind_zone": blind_zone,
        "sensor_count": sensor_count,
        "missing_sensors": missing_sensors,
        "coverage_percent": details["coverage_percent"],
        "data_age": data_age,
        "risk_trend": risk_trend,
        "cascade_events": cascade_events,
        "cascade_severity": cascade_severity,
        "cascade_status": cascade_status,
        "data_source": readings.get("data_source", "simulated"),
        "is_simulated": details["is_simulated"],
    }
