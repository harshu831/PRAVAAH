def calculate_flood_risk(rainfall, soil_moisture, river_level):
    """
    Calculate a simple flood risk score from 0 to 100.
    """

    rainfall_score = min(rainfall / 100, 1) * 30
    soil_score = min(soil_moisture / 100, 1) * 30
    river_score = min(river_level / 10, 1) * 40

    risk_score = rainfall_score + soil_score + river_score

    return round(risk_score, 2)


def get_risk_state(risk_score):
    """
    Convert the numerical risk score into a meaningful state.
    """

    if risk_score < 25:
        return "Stable"

    elif risk_score < 50:
        return "Vulnerable"

    elif risk_score < 75:
        return "Critical"

    else:
        return "Hazard"