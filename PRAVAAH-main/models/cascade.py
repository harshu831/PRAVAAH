
import networkx as nx
from math import isfinite


# --------------------------------------------------
# 1. CREATE DISASTER CASCADE GRAPH
# --------------------------------------------------

def create_cascade_graph():
    """
    Create a directed graph representing possible
    cascading disaster events.

    Probabilities and delays are prototype assumptions,
    not validated real-world forecasts.
    """

    graph = nx.DiGraph()

    nodes = {
        "Heavy Rainfall": 3,
        "River Rise": 4,
        "Flooding": 5,
        "Road Blockage": 4,
        "Village Isolation": 5,
        "Communication Failure": 4,
        "Rescue Delay": 5,
    }

    for node, severity in nodes.items():
        graph.add_node(node, severity=severity)

    edges = [
        ("Heavy Rainfall", "River Rise", 0.80, 1),
        ("River Rise", "Flooding", 0.85, 1),
        ("Flooding", "Road Blockage", 0.70, 1),
        ("Road Blockage", "Village Isolation", 0.75, 2),
        (
            "Village Isolation",
            "Communication Failure",
            0.50,
            2,
        ),
        (
            "Communication Failure",
            "Rescue Delay",
            0.80,
            1,
        ),
    ]

    for source, target, probability, delay in edges:
        graph.add_edge(
            source,
            target,
            probability=probability,
            delay=delay,
        )

    return graph


# --------------------------------------------------
# 2. VALIDATE INPUTS
# --------------------------------------------------

def _validate_number(name, value):
    """Convert an input to a finite float."""

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{name} must be a number."
        ) from None

    if not isfinite(value):
        raise ValueError(
            f"{name} must be a finite number."
        )

    return value


# --------------------------------------------------
# 3. PREDICT CASCADING EVENTS
# --------------------------------------------------

def predict_cascade(
    graph,
    risk_score,
    rainfall,
    river_level,
    confidence=100,
):
    """
    Estimate downstream cascade events.

    Returns a list of dictionaries containing:
        event: predicted event name
        probability: heuristic probability estimate
        delay: earliest estimated delay from an active
               starting hazard, in graph-defined time units

    These estimates are not calibrated probabilities.
    """

    risk_score = _validate_number(
        "risk_score", risk_score
    )
    rainfall = _validate_number(
        "rainfall", rainfall
    )
    river_level = _validate_number(
        "river_level", river_level
    )
    confidence = _validate_number(
        "confidence", confidence
    )

    if not 0 <= risk_score <= 100:
        raise ValueError(
            "risk_score must be between 0 and 100."
        )

    if rainfall < 0 or river_level < 0:
        raise ValueError(
            "Rainfall and river level cannot be negative."
        )

    if not 0 <= confidence <= 100:
        raise ValueError(
            "confidence must be between 0 and 100."
        )

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError(
            "The cascade graph must be a directed "
            "acyclic graph (DAG)."
        )

    # Identify active hazards using prototype thresholds.
    active_nodes = set()

    if rainfall >= 45 and "Heavy Rainfall" in graph:
        active_nodes.add("Heavy Rainfall")

    if river_level >= 4 and "River Rise" in graph:
        active_nodes.add("River Rise")

    if risk_score >= 45 and "Flooding" in graph:
        active_nodes.add("Flooding")

    if not active_nodes:
        return []

    # Heuristic adjustment factors.
    confidence_factor = max(confidence, 30) / 100

    risk_factor = (
        0.75 + min(risk_score / 100, 1) * 0.35
    )

    # Initialise propagation state.
    probabilities = {
        node: 0.0
        for node in graph.nodes
    }

    delays = {
        node: float("inf")
        for node in graph.nodes
    }

    # Active hazards are treated as already present.
    for node in active_nodes:
        probabilities[node] = 1.0
        delays[node] = 0

    # Topological order ensures that upstream nodes
    # are processed before downstream nodes.
    for current_node in nx.topological_sort(graph):

        current_probability = probabilities[current_node]

        if current_probability <= 0:
            continue

        for next_node in graph.successors(current_node):

            edge = graph[current_node][next_node]

            base_probability = _validate_number(
                "edge probability",
                edge.get("probability"),
            )

            edge_delay = _validate_number(
                "edge delay",
                edge.get("delay"),
            )

            if not 0 <= base_probability <= 1:
                raise ValueError(
                    f"Invalid probability for "
                    f"{current_node} -> {next_node}."
                )

            if edge_delay < 0 or not edge_delay.is_integer():
                raise ValueError(
                    f"Delay for {current_node} -> "
                    f"{next_node} must be a nonnegative "
                    "integer."
                )

            adjusted_probability = min(
                base_probability
                * risk_factor
                * confidence_factor,
                0.99,
            )

            path_probability = (
                current_probability
                * adjusted_probability
            )

            # Combine incoming path estimates using
            # an independence assumption. This is a
            # heuristic, not a calibrated probability.
            previous_probability = probabilities[next_node]

            probabilities[next_node] = 1 - (
                (1 - previous_probability)
                * (1 - path_probability)
            )

            # Keep the earliest estimated arrival delay.
            candidate_delay = (
                delays[current_node] + edge_delay
            )

            delays[next_node] = min(
                delays[next_node],
                candidate_delay,
            )

    # Build results, excluding starting hazards.
    predicted_events = []

    for node in graph.nodes:

        if node in active_nodes:
            continue

        probability = probabilities[node]

        if probability <= 0:
            continue

        predicted_events.append({
            "event": node,
            "probability": round(
                probability, 3
            ),
            "delay": int(delays[node]),
        })

    # Sort by earliest arrival, then highest estimate.
    predicted_events.sort(
        key=lambda event: (
            event["delay"],
            -event["probability"],
        )
    )

    return predicted_events


# --------------------------------------------------
# 4. CALCULATE CASCADE SEVERITY
# --------------------------------------------------

def calculate_cascade_severity(
    graph,
    predicted_events,
):
    """
    Calculate a weighted severity index.

    This is a severity indicator, not a probability
    of disaster or an empirically validated score.
    """

    severity = 0.0

    for event in predicted_events:

        node = event.get("event")

        if node not in graph:
            raise ValueError(
                f"Unknown event in prediction: {node}"
            )

        probability = _validate_number(
            "event probability",
            event.get("probability"),
        )

        if not 0 <= probability <= 1:
            raise ValueError(
                "Event probability must be between 0 and 1."
            )

        node_severity = _validate_number(
            "node severity",
            graph.nodes[node].get("severity"),
        )

        if node_severity < 0:
            raise ValueError(
                f"Severity for {node} cannot be negative."
            )

        severity += node_severity * probability

    return round(severity, 2)


# --------------------------------------------------
# 5. RANK VILLAGES BY EXPOSURE
# --------------------------------------------------

def assign_cascade_to_locations(
    locations,
    risk_score,
):
    """
    Estimate relative village exposure using the
    overall risk score and each village's vulnerability.

    Vulnerability must be between 0 and 1.
    """

    risk_score = _validate_number(
        "risk_score", risk_score
    )

    if not 0 <= risk_score <= 100:
        raise ValueError(
            "risk_score must be between 0 and 100."
        )

    if not isinstance(locations, dict):
        raise ValueError(
            "locations must be a dictionary."
        )

    villages = locations.get("villages")

    if not isinstance(villages, list):
        raise ValueError(
            "locations must contain a 'villages' list."
        )

    affected_villages = []

    for village in villages:

        if not isinstance(village, dict):
            raise ValueError(
                "Each village must be a dictionary."
            )

        if "name" not in village:
            raise ValueError(
                "Each village must have a name."
            )

        vulnerability = _validate_number(
            f"vulnerability for {village['name']}",
            village.get("vulnerability"),
        )

        if not 0 <= vulnerability <= 1:
            raise ValueError(
                f"Vulnerability for {village['name']} "
                "must be between 0 and 1."
            )

        exposure = (
            risk_score / 100
        ) * vulnerability

        affected_villages.append({
            "name": village["name"],
            "population": village.get("population"),
            "vulnerability": vulnerability,
            "exposure": round(exposure, 2),
        })

    affected_villages.sort(
        key=lambda village: village["exposure"],
        reverse=True,
    )

    return affected_villages
