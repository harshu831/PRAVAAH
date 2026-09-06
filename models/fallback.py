def emergency_fallback(risk_score):
    if risk_score >= 75:
        return (
            "Issue local emergency warning and "
            "begin immediate evacuation preparation."
        )

    elif risk_score >= 50:
        return (
            "Prepare evacuation resources and "
            "increase local monitoring."
        )

    elif risk_score >= 25:
        return (
            "Increase monitoring frequency and "
            "verify vulnerable locations."
        )

    else:
        return (
            "Continue normal environmental monitoring."
        )