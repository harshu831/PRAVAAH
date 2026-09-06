import json
import os
from datetime import datetime


MEMORY_FILE = "data/disaster_memory.json"


def load_events():

    if not os.path.exists(
        MEMORY_FILE
    ):
        return []

    try:

        with open(
            MEMORY_FILE,
            "r"
        ) as file:

            return json.load(file)

    except (
        json.JSONDecodeError,
        FileNotFoundError
    ):

        return []


def save_event(event):

    os.makedirs(
        "data",
        exist_ok=True
    )

    events = load_events()

    event["event_id"] = (
        datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    event["timestamp"] = (
        datetime.now().isoformat()
    )

    events.append(event)

    with open(
        MEMORY_FILE,
        "w"
    ) as file:

        json.dump(
            events,
            file,
            indent=4
        )


def normalized_difference(
    a,
    b,
    maximum
):

    if maximum <= 0:
        return 0

    return abs(
        a - b
    ) / maximum


def find_similar_events(
    rainfall,
    river_level,
    risk_score,
    limit=5
):

    events = load_events()

    scored = []

    for event in events:

        rain_diff = normalized_difference(
            rainfall,
            event.get(
                "rainfall",
                0
            ),
            120
        )

        river_diff = normalized_difference(
            river_level,
            event.get(
                "river_level",
                0
            ),
            10
        )

        risk_diff = normalized_difference(
            risk_score,
            event.get(
                "risk_score",
                0
            ),
            100
        )

        distance = (
            rain_diff * 0.35
            + river_diff * 0.30
            + risk_diff * 0.35
        )

        similarity = (
            1 - min(distance, 1)
        ) * 100

        scored.append({
            "event": event,
            "similarity": round(
                similarity,
                1
            )
        })

    scored.sort(
        key=lambda x:
            x["similarity"],
        reverse=True
    )

    return scored[:limit]


def calculate_memory_adjustment(
    similar_events,
    current_risk
):

    if not similar_events:
        return 0

    strong_matches = [
        item
        for item in similar_events
        if item["similarity"] >= 65
    ]

    if not strong_matches:
        return 0

    weighted_sum = 0
    weight_total = 0

    for item in strong_matches:

        event = item["event"]

        historical_risk = float(
            event.get(
                "risk_score",
                current_risk
            )
        )

        similarity = (
            item["similarity"]
            / 100
        )

        weighted_sum += (
            historical_risk
            * similarity
        )

        weight_total += similarity

    if weight_total == 0:
        return 0

    historical_average = (
        weighted_sum
        / weight_total
    )

    difference = (
        historical_average
        - current_risk
    )

    adjustment = (
        difference * 0.15
    )

    return round(
        max(-5, min(5, adjustment)),
        2
    )