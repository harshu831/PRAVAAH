import random

import numpy as np
from sklearn.ensemble import RandomForestRegressor


FEATURE_NAMES = [
    "Rainfall",
    "Soil Moisture",
    "River Level",
    "Temperature",
    "Humidity",
    "Rainfall Change",
    "River Level Change",
    "Risk Trend"
]


def calculate_target_risk(
    rainfall,
    soil_moisture,
    river_level,
    temperature,
    humidity,
    rainfall_change,
    river_change,
    risk_trend
):
    """
    Synthetic training target for the prototype.

    This deliberately includes environmental change and
    momentum so the AI learns more than a static formula.
    """

    rainfall_component = (
        min(rainfall / 120, 1) * 28
    )

    soil_component = (
        min(soil_moisture / 100, 1) * 20
    )

    river_component = (
        min(river_level / 10, 1) * 32
    )

    rain_change_component = (
        max(rainfall_change, 0) / 30 * 8
    )

    river_change_component = (
        max(river_change, 0) / 2 * 8
    )

    trend_component = (
        max(risk_trend, 0) / 15 * 4
    )

    humidity_component = (
        max(humidity - 60, 0) / 40 * 2
    )

    risk = (
        rainfall_component
        + soil_component
        + river_component
        + rain_change_component
        + river_change_component
        + trend_component
        + humidity_component
    )

    noise = random.uniform(-3, 3)

    return max(
        0,
        min(100, risk + noise)
    )


def generate_training_data(samples=3000):

    X = []
    y = []

    for _ in range(samples):

        rainfall = random.uniform(0, 120)
        soil_moisture = random.uniform(0, 100)
        river_level = random.uniform(0, 10)
        temperature = random.uniform(15, 45)
        humidity = random.uniform(20, 100)

        rainfall_change = random.uniform(-30, 30)
        river_change = random.uniform(-2, 2)
        risk_trend = random.uniform(-15, 15)

        target = calculate_target_risk(
            rainfall,
            soil_moisture,
            river_level,
            temperature,
            humidity,
            rainfall_change,
            river_change,
            risk_trend
        )

        X.append([
            rainfall,
            soil_moisture,
            river_level,
            temperature,
            humidity,
            rainfall_change,
            river_change,
            risk_trend
        ])

        y.append(target)

    return np.array(X), np.array(y)


def train_model():

    X, y = generate_training_data()

    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    return model


def predict_ai_risk(
    model,
    rainfall,
    soil_moisture,
    river_level,
    temperature,
    humidity,
    rainfall_change=0,
    river_change=0,
    risk_trend=0,
    memory_adjustment=0
):

    features = [[
        rainfall,
        soil_moisture,
        river_level,
        temperature,
        humidity,
        rainfall_change,
        river_change,
        risk_trend
    ]]

    prediction = model.predict(features)[0]

    prediction += memory_adjustment

    prediction = max(
        0,
        min(100, prediction)
    )

    return round(
        float(prediction),
        2
    )


def get_feature_importance(model):

    importances = model.feature_importances_

    results = []

    for name, importance in zip(
        FEATURE_NAMES,
        importances
    ):

        results.append({
            "Feature": name,
            "Importance": round(
                float(importance) * 100,
                2
            )
        })

    results.sort(
        key=lambda x: x["Importance"],
        reverse=True
    )

    return results


def calculate_feature_contribution(
    rainfall,
    soil_moisture,
    river_level,
    temperature,
    humidity,
    rainfall_change=0,
    river_change=0,
    risk_trend=0
):

    values = {
        "Rainfall": max(rainfall, 0) / 120 * 28,
        "Soil Moisture": max(soil_moisture, 0) / 100 * 20,
        "River Level": max(river_level, 0) / 10 * 32,
        "Rainfall Change": max(rainfall_change, 0) / 30 * 8,
        "River Level Change": max(river_change, 0) / 2 * 8,
        "Risk Trend": max(risk_trend, 0) / 15 * 4,
        "Humidity": max(humidity - 60, 0) / 40 * 2,
        "Temperature": 0
    }

    total = sum(values.values())

    if total <= 0:
        return []

    results = []

    for name, value in values.items():

        results.append({
            "Feature": name,
            "Contribution": round(
                value / total * 100,
                1
            )
        })

    results.sort(
        key=lambda x: x["Contribution"],
        reverse=True
    )

    return results


def get_ai_risk_state(risk_score):

    if risk_score < 25:
        return "Stable"

    elif risk_score < 50:
        return "Vulnerable"

    elif risk_score < 75:
        return "Critical"

    return "Hazard"