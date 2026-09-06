def calculate_uncertainty(
    sensor_count,
    missing_sensors,
    data_age,
    coverage,
    risk_trend=0,
    blind_zone=False
):

    if sensor_count <= 0:
        return 0

    missing_ratio = (
        missing_sensors / sensor_count
    )

    missing_penalty = (
        missing_ratio * 35
    )

    freshness_penalty = (
        min(data_age / 60, 1) * 25
    )

    coverage_penalty = (
        (1 - coverage) * 25
    )

    trend_penalty = (
        min(abs(risk_trend) / 15, 1) * 5
    )

    blind_zone_penalty = (
        10 if blind_zone else 0
    )

    uncertainty = (
        missing_penalty
        + freshness_penalty
        + coverage_penalty
        + trend_penalty
        + blind_zone_penalty
    )

    confidence = 100 - uncertainty

    return round(
        max(0, min(100, confidence)),
        2
    )


def get_confidence_status(confidence):

    if confidence >= 80:
        return "High Confidence"

    elif confidence >= 60:
        return "Moderate Confidence"

    elif confidence >= 40:
        return "Low Confidence"

    return "Very Low Confidence"


def detect_blind_zone(
    sensor_count,
    missing_sensors,
    coverage
):

    if sensor_count <= 0:
        return True

    missing_ratio = (
        missing_sensors / sensor_count
    )

    return (
        missing_ratio >= 0.5
        or coverage < 0.5
    )


def get_uncertainty_message(confidence):

    if confidence >= 80:
        return "Sensor network is providing strong environmental visibility."

    elif confidence >= 60:
        return "Some uncertainty exists, but the system has usable situational awareness."

    elif confidence >= 40:
        return "Prediction confidence is reduced. Additional sensing is recommended."

    return "Environmental visibility is poor. Treat predictions as high-uncertainty signals."