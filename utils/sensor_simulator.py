import random


# Initial environmental conditions
environment = {
    "rainfall": 10.0,
    "soil_moisture": 35.0,
    "river_level": 2.0,
    "temperature": 30.0,
    "humidity": 60.0
}


def generate_sensor_data():
    global environment

    # Simulate rainfall changing over time
    rainfall_change = random.uniform(-10, 20)

    environment["rainfall"] += rainfall_change

    # Keep rainfall within realistic prototype limits
    environment["rainfall"] = max(
        0,
        min(environment["rainfall"], 120)
    )

    # Soil responds to rainfall
    if environment["rainfall"] > 40:
        environment["soil_moisture"] += 4
    else:
        environment["soil_moisture"] -= 1

    environment["soil_moisture"] = max(
        0,
        min(environment["soil_moisture"], 100)
    )

    # River responds to rainfall and soil saturation
    river_increase = (
        environment["rainfall"] / 100
        + environment["soil_moisture"] / 500
    )

    environment["river_level"] += river_increase

    # Small natural decrease when conditions are dry
    if environment["rainfall"] < 20:
        environment["river_level"] -= 0.15

    environment["river_level"] = max(
        0,
        min(environment["river_level"], 10)
    )

    # Temperature changes slowly
    environment["temperature"] += random.uniform(-1, 1)

    environment["temperature"] = max(
        15,
        min(environment["temperature"], 45)
    )

    # Humidity responds somewhat to rainfall
    if environment["rainfall"] > 40:
        environment["humidity"] += 3
    else:
        environment["humidity"] -= 1

    environment["humidity"] = max(
        20,
        min(environment["humidity"], 100)
    )

    return {
        "rainfall": round(environment["rainfall"], 2),
        "soil_moisture": round(environment["soil_moisture"], 2),
        "river_level": round(environment["river_level"], 2),
        "temperature": round(environment["temperature"], 2),
        "humidity": round(environment["humidity"], 2)
    }

def generate_sensor_health():

    total_sensors = 10

    missing_sensors = random.randint(0, 4)

    coverage = random.uniform(0.4, 1.0)

    data_age = random.uniform(0, 90)

    return {
        "total_sensors": total_sensors,
        "missing_sensors": missing_sensors,
        "coverage": round(coverage, 2),
        "data_age": round(data_age, 1)
    }