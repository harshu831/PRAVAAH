def get_locations():
    villages = [
        {
            "name": "Village A",
            "latitude": 28.6692,
            "longitude": 77.4538,
            "population": 1200,
            "vulnerability": 0.85
        },
        {
            "name": "Village B",
            "latitude": 28.6750,
            "longitude": 77.4680,
            "population": 800,
            "vulnerability": 0.65
        },
        {
            "name": "Village C",
            "latitude": 28.6600,
            "longitude": 77.4750,
            "population": 1500,
            "vulnerability": 0.45
        }
    ]

    shelters = [
        {
            "name": "Shelter 1",
            "latitude": 28.6800,
            "longitude": 77.4600,
            "capacity": 500
        },
        {
            "name": "Shelter 2",
            "latitude": 28.6550,
            "longitude": 77.4650,
            "capacity": 700
        }
    ]

    sensors = [
        {
            "name": "Sensor 1",
            "latitude": 28.6700,
            "longitude": 77.4550
        },
        {
            "name": "Sensor 2",
            "latitude": 28.6750,
            "longitude": 77.4700
        },
        {
            "name": "Sensor 3",
            "latitude": 28.6600,
            "longitude": 77.4680
        }
    ]

    roads = [
        {
            "name": "Road A",
            "start": (28.6692, 77.4538),
            "end": (28.6800, 77.4600)
        },
        {
            "name": "Road B",
            "start": (28.6750, 77.4680),
            "end": (28.6550, 77.4650)
        },
        {
            "name": "Road C",
            "start": (28.6600, 77.4750),
            "end": (28.6550, 77.4650)
        },
        {
            "name": "Road D",
            "start": (28.6800, 77.4600),
            "end": (28.6550, 77.4650)
        }
    ]

    resources = [
        {
            "name": "Rescue Team 1",
            "type": "Rescue Team",
            "capacity": 25,
            "available": True,
            "location": "Shelter 1"
        },
        {
            "name": "Boat 1",
            "type": "Boat",
            "capacity": 20,
            "available": True,
            "location": "Shelter 2"
        },
        {
            "name": "Ambulance 1",
            "type": "Ambulance",
            "capacity": 4,
            "available": True,
            "location": "Shelter 1"
        },
        {
            "name": "Boat 2",
            "type": "Boat",
            "capacity": 15,
            "available": True,
            "location": "Shelter 2"
        }
    ]

    return {
        "villages": villages,
        "shelters": shelters,
        "sensors": sensors,
        "roads": roads,
        "resources": resources
    }