def calculate_risk_trend(history):
    """
    Calculate how quickly the flood risk is changing.
    """

    if len(history) < 2:
        return 0

    previous = history[-2]["risk_score"]
    current = history[-1]["risk_score"]

    trend = current - previous

    return round(trend, 2)


def get_precursor_status(trend):
    """
    Interpret the direction and speed of risk change.
    """

    if trend <= 0:
        return "Improving"

    elif trend < 5:
        return "Slowly Increasing"

    elif trend < 10:
        return "Rapidly Increasing"

    else:
        return "Extremely Rapid Increase"


def estimate_time_to_threshold(
    current_risk,
    risk_trend,
    threshold
):
    """
    Estimate how many simulation steps are needed
    to reach a particular risk threshold.
    """

    if current_risk >= threshold:
        return 0

    if risk_trend <= 0:
        return None

    remaining_risk = threshold - current_risk

    steps = remaining_risk / risk_trend

    return round(steps, 1)