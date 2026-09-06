from simulation.flood_simulator import (
    simulate_flood,
    get_village_impacts
)


def calculate_baseline_exposure(
    locations,
    impacts,
    rainfall,
    river_level
):
    """
    Estimate the population exposed to the disaster.

    First uses villages actually identified as flooded by the
    Digital Twin. If no village is flooded, a smaller planning
    exposure is estimated from environmental hazard pressure.
    """

    exposed_population = 0

    for village in impacts:

        if village["flooded"]:

            exposed_population += int(
                village["population"]
                * village["vulnerability"]
            )

    # If the flood simulator produces no flooded village,
    # estimate a planning exposure from environmental pressure.
    #
    # This keeps the counterfactual useful during lower-intensity
    # demonstration scenarios without claiming actual casualties.
    if exposed_population == 0:

        rainfall_pressure = min(
            rainfall / 100,
            1.0
        )

        river_pressure = min(
            river_level / 10,
            1.0
        )

        hazard_pressure = (
            rainfall_pressure * 0.55
            + river_pressure * 0.45
        )

        for village in locations["villages"]:

            village_exposure = int(
                village["population"]
                * village["vulnerability"]
                * hazard_pressure
            )

            exposed_population += village_exposure

    return exposed_population


def evaluate_strategy(
    locations,
    rainfall,
    river_level,
    evacuation_lead_minutes,
    available_boats,
    road_failures,
    communication_failures
):
    """
    Evaluate one response strategy under the same disaster conditions.

    The flood itself does not change between strategies.
    The response changes the estimated human impact.
    """

    # ---------------------------------------------------------
    # 1. Simulate the underlying disaster
    # ---------------------------------------------------------

    result = simulate_flood(
        rainfall=rainfall,
        river_level=river_level,
        steps=4,
        road_failures=road_failures,
        communication_failures=communication_failures
    )

    impacts = get_village_impacts(
        locations,
        result
    )

    # ---------------------------------------------------------
    # 2. Determine baseline exposed population
    # ---------------------------------------------------------

    exposed_population = calculate_baseline_exposure(
        locations,
        impacts,
        rainfall,
        river_level
    )

    # ---------------------------------------------------------
    # 3. Calculate strategy-specific benefits
    # ---------------------------------------------------------

    # Earlier evacuation provides the largest benefit because
    # people have more time to move before conditions worsen.
    evacuation_reduction = min(
        evacuation_lead_minutes * 0.012,
        0.60
    )

    # Only boats beyond the baseline allocation should count
    # as the "extra boat" benefit.
    #
    # The baseline number of boats is assumed to be 2 in this
    # prototype. This can later be replaced by dynamic allocation.
    baseline_boats = 2

    extra_boats = max(
        0,
        available_boats - baseline_boats
    )

    boat_reduction = min(
        extra_boats * 0.08,
        0.20
    )

    # ---------------------------------------------------------
    # 4. Account for infrastructure failures
    # ---------------------------------------------------------

    infrastructure_penalty = min(
        road_failures * 0.05
        + communication_failures * 0.03,
        0.30
    )

    # ---------------------------------------------------------
    # 5. Calculate total response benefit
    # ---------------------------------------------------------

    total_reduction = (
        evacuation_reduction
        + boat_reduction
        - infrastructure_penalty
    )

    total_reduction = max(
        0,
        min(total_reduction, 0.75)
    )

    adjusted_exposure = int(
        exposed_population
        * (1 - total_reduction)
    )

    adjusted_exposure = max(
        0,
        adjusted_exposure
    )

    # ---------------------------------------------------------
    # 6. Calculate people protected
    # ---------------------------------------------------------

    people_protected = max(
        0,
        exposed_population - adjusted_exposure
    )

    if exposed_population > 0:

        protection_rate = (
            people_protected
            / exposed_population
        ) * 100

    else:

        protection_rate = 0

    # ---------------------------------------------------------
    # 7. Estimate evacuation time
    # ---------------------------------------------------------

    evacuation_time = max(
        15,
        75
        - evacuation_lead_minutes * 0.45
        - extra_boats * 7
    )

    # Infrastructure failures slow response.
    evacuation_time += (
        road_failures * 5
        + communication_failures * 3
    )

    # ---------------------------------------------------------
    # 8. Estimate isolation duration
    # ---------------------------------------------------------

    isolation_duration = max(
        0,
        road_failures * 15
        + communication_failures * 10
        - evacuation_lead_minutes * 0.25
        - extra_boats * 4
    )

    # ---------------------------------------------------------
    # 9. Return results
    # ---------------------------------------------------------

    return {
        "exposed_population":
            adjusted_exposure,

        "people_protected":
            people_protected,

        "protection_rate":
            round(protection_rate, 1),

        "evacuation_time":
            round(evacuation_time, 1),

        "isolation_duration":
            round(isolation_duration, 1),

        "flooded_cells":
            result["flooded_cells"],

        "communication_coverage":
            result["communication_coverage"],

        "road_access":
            result["road_access"]
    }


def compare_scenarios(
    locations,
    rainfall,
    river_level,
    road_failures,
    communication_failures,
    available_boats
):
    """
    Compare three alternative response strategies.
    """

    scenarios = []

    # =========================================================
    # 1. CURRENT RESPONSE
    # =========================================================

    current = evaluate_strategy(
        locations=locations,
        rainfall=rainfall,
        river_level=river_level,
        evacuation_lead_minutes=0,
        available_boats=available_boats,
        road_failures=road_failures,
        communication_failures=communication_failures
    )

    current["strategy"] = "Current Response"

    scenarios.append(current)

    # =========================================================
    # 2. EVACUATE 30 MINUTES EARLIER
    # =========================================================

    early = evaluate_strategy(
        locations=locations,
        rainfall=rainfall,
        river_level=river_level,
        evacuation_lead_minutes=30,
        available_boats=available_boats,
        road_failures=road_failures,
        communication_failures=communication_failures
    )

    early["strategy"] = "Evacuate 30 Min Earlier"

    scenarios.append(early)

    # =========================================================
    # 3. REPOSITION EXTRA BOAT
    # =========================================================

    repositioned = evaluate_strategy(
        locations=locations,
        rainfall=rainfall,
        river_level=river_level,
        evacuation_lead_minutes=10,
        available_boats=available_boats + 1,
        road_failures=road_failures,
        communication_failures=communication_failures
    )

    repositioned["strategy"] = "Reposition Extra Boat"

    scenarios.append(repositioned)

    return scenarios