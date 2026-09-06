NORMAL = "Normal"
DEGRADED = "Degraded"
EMERGENCY = "Emergency"
ISOLATED = "Isolated"


def determine_system_mode(
    sensor_health,
    communication_available,
    cloud_available,
    gps_available
):
    if (
        not communication_available
        and not cloud_available
        and not gps_available
    ):
        return ISOLATED

    if (
        not communication_available
        or sensor_health < 40
    ):
        return EMERGENCY

    if (
        sensor_health < 80
        or not cloud_available
        or not gps_available
    ):
        return DEGRADED

    return NORMAL


def calculate_retained_capability(mode):
    values = {
        NORMAL: 100,
        DEGRADED: 80,
        EMERGENCY: 55,
        ISOLATED: 35
    }

    return values.get(mode, 0)