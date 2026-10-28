
from math import isfinite


# Maximum contribution of each environmental signal.
WEIGHTS = {
    "rainfall": 30,
    "soil_moisture": 30,
    "river_level": 40,
}

# Reference scales used by the current prototype.
MAX_VALUES = {
    "rainfall": 100,
    "soil_moisture": 100,
    "river_level": 10,
}


def _validate_reading(name, value):
    """Validate a reading while allowing missing sensor data."""

    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{name} must be a number or None."
        ) from None

    if not isfinite(value):
        raise ValueError(
            f"{name} must be a finite number."
        )

    if value < 0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    return min(value, MAX_VALUES[name])


def get_risk_state(risk_score):
    """Convert a risk score into a descriptive state."""

    if not isfinite(float(risk_score)):
        raise ValueError("Risk score must be finite.")

    if risk_score < 25:
        return "Stable"
    elif risk_score < 50:
        return "Vulnerable"
    elif risk_score < 75:
        return "Critical"
    else:
        return "Hazard"


def calculate_flood_risk_details(
    rainfall,
    soil_moisture,
    river_level,
):
    """
    Calculate a weighted flood-risk index.

    Missing readings are excluded and the remaining weights
    are normalized. This is a prototype index, not a calibrated
    flood probability or a validated forecasting model.
    """

    readings = {
        "rainfall": _validate_reading("rainfall", rainfall),
        "soil_moisture": _validate_reading(
            "soil_moisture", soil_moisture
        ),
        "river_level": _validate_reading(
            "river_level", river_level
        ),
    }

    available = {
        name: value
        for name, value in readings.items()
        if value is not None
    }

    if not available:
        raise ValueError(
            "At least one valid environmental reading is required."
        )

    available_weight = sum(
        WEIGHTS[name] for name in available
    )

    contributions = {
        name: round(
            (value / MAX_VALUES[name]) * WEIGHTS[name],
            2,
        )
        for name, value in available.items()
    }

    # Preserve the original score when all readings are present.
    raw_score = sum(contributions.values())

    risk_score = round(
        raw_score * 100 / available_weight,
        2,
    )

    coverage_percent = available_weight

    if coverage_percent == 100:
        data_quality = "Complete"
        confidence_label = "All three signals available"
    elif coverage_percent >= 60:
        data_quality = "Partial"
        confidence_label = "Some signals missing"
    else:
        data_quality = "Limited"
        confidence_label = "Insufficient signal coverage"

    missing_signals = [
        name for name, value in readings.items()
        if value is None
    ]

    return {
        "risk_score": risk_score,
        "risk_state": get_risk_state(risk_score),
        "contributions": contributions,
        "data_quality": data_quality,
        "coverage_percent": coverage_percent,
        "missing_signals": missing_signals,
        "confidence_label": confidence_label,
        "is_simulated": True,
    }


def calculate_flood_risk(
    rainfall,
    soil_moisture,
    river_level,
):
    """
    Backwards-compatible function returning a numeric score.
    """

    result = calculate_flood_risk_details(
        rainfall,
        soil_moisture,
        river_level,
    )

    return result["risk_score"]
