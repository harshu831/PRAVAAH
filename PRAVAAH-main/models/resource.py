
import math
import networkx as nx


# ============================================================
# VALIDATION HELPERS
# ============================================================

def _number(name, value, minimum=None, maximum=None):
    """Convert a value to a finite float and validate bounds."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number.") from None

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")

    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}.")

    return value


def _usable_road_graph(graph):
    """Return a copy containing only accessible roads."""
    if graph is None:
        return None

    usable = graph.copy()

    for start, end, data in list(usable.edges(data=True)):
        if data.get("accessible", True) is False:
            usable.remove_edge(start, end)

    return usable


# ============================================================
# PRIORITY CALCULATION
# ============================================================

def calculate_priority(
    exposure,
    vulnerability,
    accessibility,
    time_to_critical=None,
    cascade_severity=0,
):
    """Calculate a heuristic rescue-priority score from 0 to 100."""
    exposure = _number("exposure", exposure, 0, 1)
    vulnerability = _number("vulnerability", vulnerability, 0, 1)
    accessibility = _number("accessibility", accessibility, 0, 1)
    cascade_severity = _number("cascade_severity", cascade_severity, 0)

    exposure_score = exposure * 35
    vulnerability_score = vulnerability * 30
    accessibility_score = (1 - accessibility) * 15

    if time_to_critical is None:
        urgency_score = 0
    else:
        time_to_critical = _number("time_to_critical", time_to_critical)

        if time_to_critical <= 0:
            urgency_score = 15
        elif time_to_critical <= 2:
            urgency_score = 13
        elif time_to_critical <= 5:
            urgency_score = 10
        elif time_to_critical <= 10:
            urgency_score = 6
        else:
            urgency_score = 2

    cascade_score = min(cascade_severity / 20, 1) * 5

    priority = (
        exposure_score
        + vulnerability_score
        + accessibility_score
        + urgency_score
        + cascade_score
    )

    return round(min(max(priority, 0), 100), 2)


def get_priority_level(priority):
    """Convert a priority score into a readable level."""
    priority = _number("priority", priority, 0, 100)

    if priority >= 75:
        return "CRITICAL"
    if priority >= 50:
        return "HIGH"
    if priority >= 25:
        return "MEDIUM"
    return "LOW"


# ============================================================
# DISTANCE
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate straight-line GPS distance in kilometres."""
    lat1 = _number("lat1", lat1, -90, 90)
    lat2 = _number("lat2", lat2, -90, 90)
    lon1 = _number("lon1", lon1, -180, 180)
    lon2 = _number("lon2", lon2, -180, 180)

    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    a = min(max(a, 0), 1)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(earth_radius * c, 2)


# ============================================================
# ROAD NETWORK
# ============================================================

def create_road_network(locations):
    """
    Build a NetworkX road graph.

    Expected keys:
        villages, shelters, roads

    Roads use start/end coordinate pairs and may specify
    accessible=False when blocked.
    """
    graph = nx.Graph()

    for village in locations.get("villages", []):
        graph.add_node(
            village["name"],
            latitude=_number(
                "village latitude", village["latitude"], -90, 90
            ),
            longitude=_number(
                "village longitude", village["longitude"], -180, 180
            ),
            node_type="village",
        )

    for shelter in locations.get("shelters", []):
        graph.add_node(
            shelter["name"],
            latitude=_number(
                "shelter latitude", shelter["latitude"], -90, 90
            ),
            longitude=_number(
                "shelter longitude", shelter["longitude"], -180, 180
            ),
            node_type="shelter",
        )

    for road in locations.get("roads", []):
        start_lat, start_lon = road["start"]
        end_lat, end_lon = road["end"]

        start_node = _find_nearest_node(graph, start_lat, start_lon)
        end_node = _find_nearest_node(graph, end_lat, end_lon)

        if (
            start_node is None
            or end_node is None
            or start_node == end_node
        ):
            continue

        distance = haversine_distance(
            graph.nodes[start_node]["latitude"],
            graph.nodes[start_node]["longitude"],
            graph.nodes[end_node]["latitude"],
            graph.nodes[end_node]["longitude"],
        )

        graph.add_edge(
            start_node,
            end_node,
            distance=distance,
            road_name=road.get("name", "Unnamed road"),
            accessible=bool(road.get("accessible", True)),
        )

    return graph


def _find_nearest_node(graph, latitude, longitude):
    """Find the graph node nearest to a GPS coordinate."""
    if graph.number_of_nodes() == 0:
        return None

    nearest_node = None
    nearest_distance = float("inf")

    for node, data in graph.nodes(data=True):
        distance = haversine_distance(
            latitude,
            longitude,
            data["latitude"],
            data["longitude"],
        )

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_node = node

    return nearest_node


# ============================================================
# ACCESSIBILITY
# ============================================================

def calculate_accessibility(graph, village_name):
    """Estimate accessibility from 0 to 1 using road connectivity."""
    if graph is None or village_name not in graph:
        return 0.0

    usable = _usable_road_graph(graph)

    shelters = [
        node
        for node, data in usable.nodes(data=True)
        if data.get("node_type") == "shelter"
    ]

    if not shelters:
        return 0.5

    reachable_distances = []

    for shelter in shelters:
        try:
            distance = nx.shortest_path_length(
                usable,
                source=village_name,
                target=shelter,
                weight="distance",
            )
            reachable_distances.append(distance)
        except nx.NetworkXNoPath:
            continue

    if not reachable_distances:
        return 0.0

    shortest_distance = min(reachable_distances)

    if shortest_distance <= 1:
        distance_score = 1.0
    elif shortest_distance <= 2:
        distance_score = 0.9
    elif shortest_distance <= 4:
        distance_score = 0.75
    elif shortest_distance <= 6:
        distance_score = 0.60
    elif shortest_distance <= 10:
        distance_score = 0.45
    else:
        distance_score = 0.30

    degree = usable.degree(village_name)

    if degree >= 3:
        connectivity_score = 1.0
    elif degree == 2:
        connectivity_score = 0.85
    elif degree == 1:
        connectivity_score = 0.65
    else:
        connectivity_score = 0.30

    return round(
        min(max(
            distance_score * 0.65 + connectivity_score * 0.35,
            0,
        ), 1),
        2,
    )


# ============================================================
# RESCUE DEMAND
# ============================================================

def calculate_rescue_demand(population, exposure, vulnerability):
    """Estimate the number of people who may need assistance."""
    population = _number("population", population, 0)
    exposure = _number("exposure", exposure, 0, 1)
    vulnerability = _number("vulnerability", vulnerability, 0, 1)

    exposed_population = population * exposure
    vulnerability_factor = 0.5 + 0.5 * vulnerability

    return max(0, round(exposed_population * vulnerability_factor))


# ============================================================
# REQUIRED RESOURCE TYPES
# ============================================================

def get_required_resource_types(
    exposure,
    accessibility,
    rescue_demand,
):
    """Suggest resource types based on exposure and demand."""
    exposure = _number("exposure", exposure, 0, 1)
    accessibility = _number("accessibility", accessibility, 0, 1)
    rescue_demand = _number("rescue_demand", rescue_demand, 0)

    if rescue_demand <= 0:
        return []

    required_types = []

    if accessibility < 0.50 or exposure >= 0.75:
        required_types.append("Boat")

    required_types.append("Rescue Team")

    if exposure >= 0.60 or rescue_demand >= 100:
        required_types.append("Ambulance")

    return required_types


# ============================================================
# TRAVEL TIME
# ============================================================

def calculate_travel_time(
    distance_km,
    accessibility=1.0,
    base_speed_kmh=30,
):
    """Estimate travel time in minutes."""
    distance_km = _number("distance_km", distance_km, 0)
    accessibility = _number("accessibility", accessibility, 0, 1)
    base_speed_kmh = _number("base_speed_kmh", base_speed_kmh, 5)

    effective_speed = base_speed_kmh * max(accessibility, 0.10)

    return round(distance_km / effective_speed * 60, 1)


# ============================================================
# RESOURCE RECOMMENDATION
# ============================================================

def recommend_resource(
    resources,
    required_types,
    village,
    locations,
    accessibility=1.0,
):
    """Return the nearest available matching resource."""
    candidates = []

    for resource in resources:
        if not resource.get("available", False):
            continue

        resource_type = resource.get("type")

        if required_types and resource_type not in required_types:
            continue

        source_name = resource.get("location")

        source = next(
            (
                shelter
                for shelter in locations.get("shelters", [])
                if shelter["name"] == source_name
            ),
            None,
        )

        if source is None:
            continue

        distance = haversine_distance(
            source["latitude"],
            source["longitude"],
            village["latitude"],
            village["longitude"],
        )

        candidates.append({
            "resource": resource,
            "distance": distance,
            "travel_time": calculate_travel_time(
                distance, accessibility
            ),
        })

    if not candidates:
        return None

    return min(candidates, key=lambda item: item["travel_time"])


# ============================================================
# ALLOCATION SCORE
# ============================================================

def calculate_allocation_score(
    priority,
    accessibility,
    resource_capacity,
    rescue_demand,
    travel_time,
):
    """Score resource suitability from 0 to 100."""
    priority = _number("priority", priority, 0, 100)
    accessibility = _number("accessibility", accessibility, 0, 1)
    resource_capacity = _number("resource_capacity", resource_capacity, 0)
    rescue_demand = _number("rescue_demand", rescue_demand, 0)
    travel_time = _number("travel_time", travel_time, 0)

    priority_score = priority / 100 * 40
    accessibility_score = accessibility * 20

    if rescue_demand > 0:
        capacity_score = min(resource_capacity / rescue_demand, 1) * 20
    else:
        capacity_score = 0

    travel_score = max(0, 20 - min(travel_time, 20))

    score = (
        priority_score
        + accessibility_score
        + capacity_score
        + travel_score
    )

    return round(min(max(score, 0), 100), 2)


# ============================================================
# RESOURCE EFFICIENCY
# ============================================================

def calculate_resource_efficiency(
    allocated_resources,
    people_supported,
):
    """Return a normalized utilization score from 0 to 100."""
    allocated_resources = _number(
        "allocated_resources", allocated_resources, 0
    )
    people_supported = _number("people_supported", people_supported, 0)

    if allocated_resources <= 0:
        return 0

    people_per_resource = people_supported / allocated_resources

    return round(min(max(people_per_resource / 10 * 100, 0), 100), 2)


# ============================================================
# RESOURCE ALLOCATION
# ============================================================

def allocate_resources(villages, resources, graph, risk_score):
    """
    Allocate available resources to villages in priority order.

    Each resource is assigned at most once. A village may receive
    multiple resources. Remaining demand is tracked separately
    for each village.

    Returns a flat list compatible with the existing dashboard.
    """
    allocations = []
    risk_score = _number("risk_score", risk_score, 0, 100)

    if not villages:
        return allocations

    usable_graph = _usable_road_graph(graph)

    available_resources = [
        resource.copy()
        for resource in (resources or [])
        if resource.get("available", False)
    ]

    village_records = []
    seen_names = set()

    for village in villages:
        name = village["name"]

        if name in seen_names:
            raise ValueError(
                f"Duplicate village name '{name}'. Village names must be unique."
            )
        seen_names.add(name)

        exposure = _number(
            "exposure",
            village.get("exposure", risk_score / 100),
            0, 1,
        )
        vulnerability = _number(
            "vulnerability", village.get("vulnerability", 0), 0, 1
        )
        population = _number(
            "population", village.get("population", 0), 0
        )

        if "accessibility" in village:
            accessibility = _number(
                "accessibility", village["accessibility"], 0, 1
            )
        else:
            accessibility = calculate_accessibility(usable_graph, name)

        demand = village.get("rescue_demand")

        if demand is None:
            demand = calculate_rescue_demand(
                population, exposure, vulnerability
            )
        else:
            demand = _number("rescue_demand", demand, 0)

        demand = int(math.ceil(demand))

        cascade_severity = _number(
            "cascade_severity", village.get("cascade_severity", 0), 0
        )

        priority = village.get("priority")

        if priority is None:
            priority = calculate_priority(
                exposure=exposure,
                vulnerability=vulnerability,
                accessibility=accessibility,
                time_to_critical=village.get("time_to_critical"),
                cascade_severity=cascade_severity,
            )
        else:
            priority = _number("priority", priority, 0, 100)

        village_records.append({
            "village": village,
            "name": name,
            "exposure": exposure,
            "vulnerability": vulnerability,
            "population": population,
            "accessibility": accessibility,
            "demand": demand,
            "remaining_demand": demand,
            "priority": priority,
        })

    village_records.sort(
        key=lambda item: item["priority"],
        reverse=True,
    )

    for record in village_records:
        village = record["village"]

        if record["remaining_demand"] <= 0:
            allocations.append({
                "village": record["name"],
                "resource": "None",
                "resource_type": "None",
                "capacity": 0,
                "travel_time": None,
                "covered_people": 0,
                "remaining_demand": 0,
                "allocation_score": 0,
                "status": "No Demand",
            })
            continue

        while record["remaining_demand"] > 0:
            required_types = get_required_resource_types(
                record["exposure"],
                record["accessibility"],
                record["remaining_demand"],
            )

            candidates = []

            for resource in available_resources:
                if not resource.get("available", False):
                    continue

                source = resource.get("location")

                if (
                    usable_graph is None
                    or source not in usable_graph
                    or record["name"] not in usable_graph
                ):
                    continue

                try:
                    distance = nx.shortest_path_length(
                        usable_graph,
                        source=source,
                        target=record["name"],
                        weight="distance",
                    )
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

                capacity = _number(
                    "resource capacity",
                    resource.get("capacity", 0),
                    0,
                )

                if capacity <= 0:
                    continue

                travel_time = calculate_travel_time(
                    distance,
                    record["accessibility"],
                )

                score = calculate_allocation_score(
                    priority=record["priority"],
                    accessibility=record["accessibility"],
                    resource_capacity=capacity,
                    rescue_demand=record["remaining_demand"],
                    travel_time=travel_time,
                )

                candidates.append({
                    "resource": resource,
                    "capacity": capacity,
                    "distance": distance,
                    "travel_time": travel_time,
                    "score": score,
                    "preferred": (
                        resource.get("type") in required_types
                    ),
                })

            if not candidates:
                break

            # Prefer suitable resource types when any are reachable.
            preferred = [
                item for item in candidates if item["preferred"]
            ]

            if preferred:
                candidates = preferred

            best = max(
                candidates,
                key=lambda item: (
                    item["score"],
                    -item["travel_time"],
                ),
            )

            resource = best["resource"]
            capacity = best["capacity"]

            covered_people = min(
                int(math.floor(capacity)),
                record["remaining_demand"],
            )

            record["remaining_demand"] = max(
                0,
                record["remaining_demand"] - covered_people,
            )

            allocations.append({
                "village": record["name"],
                "resource": resource.get("name", "Unnamed resource"),
                "resource_type": resource.get("type", "Unknown"),
                "capacity": capacity,
                "travel_time": best["travel_time"],
                "covered_people": covered_people,
                "remaining_demand": record["remaining_demand"],
                "allocation_score": best["score"],
                "status": "Allocated",
            })

            # A resource is assigned only once.
            available_resources.remove(resource)

        if record["remaining_demand"] > 0:
            allocations.append({
                "village": record["name"],
                "resource": "None Available",
                "resource_type": "None",
                "capacity": 0,
                "travel_time": None,
                "covered_people": 0,
                "remaining_demand": record["remaining_demand"],
                "allocation_score": 0,
                "status": "Unmet Demand",
            })

    return allocations


# ============================================================
# ALLOCATION SUMMARY
# ============================================================

def summarize_allocation(allocation_results):
    """
    Summarize allocations without double-counting remaining demand.

    Allocation rows for one village contain successive snapshots
    of its remaining demand. The final row for that village is
    authoritative.
    """
    if not allocation_results:
        return {
            "allocated_count": 0,
            "unmet_count": 0,
            "total_capacity": 0,
            "covered_people": 0,
            "remaining_demand": 0,
            "efficiency": 0,
        }

    allocated_rows = [
        item for item in allocation_results
        if item.get("status") == "Allocated"
    ]

    unmet_rows = [
        item for item in allocation_results
        if item.get("status") == "Unmet Demand"
    ]

    # Count actual assigned resources.
    allocated_count = len(allocated_rows)

    # Count distinct villages with unmet demand.
    unmet_villages = {
        item.get("village")
        for item in unmet_rows
        if item.get("village") is not None
    }
    unmet_count = len(unmet_villages)

    total_capacity = sum(
        _number("capacity", item.get("capacity", 0), 0)
        for item in allocated_rows
    )

    covered_people = sum(
        _number("covered_people", item.get("covered_people", 0), 0)
        for item in allocated_rows
    )

    # IMPORTANT: overwrite the value as rows are traversed.
    # The final row for each village contains its final demand.
    remaining_by_village = {}

    for item in allocation_results:
        village = item.get("village")

        if village is None:
            continue

        remaining_by_village[village] = _number(
            "remaining_demand",
            item.get("remaining_demand", 0),
            0,
        )

    remaining_demand = sum(remaining_by_village.values())

    efficiency = calculate_resource_efficiency(
        allocated_count,
        covered_people,
    )

    return {
        "allocated_count": allocated_count,
        "unmet_count": unmet_count,
        "total_capacity": round(total_capacity, 2),
        "covered_people": round(covered_people, 2),
        "remaining_demand": round(remaining_demand, 2),
        "efficiency": efficiency,
    }
