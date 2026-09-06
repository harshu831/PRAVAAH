import networkx as nx


def create_cascade_graph():

    graph = nx.DiGraph()

    graph.add_node(
        "Heavy Rainfall",
        severity=3
    )

    graph.add_node(
        "River Rise",
        severity=4
    )

    graph.add_node(
        "Flooding",
        severity=5
    )

    graph.add_node(
        "Road Blockage",
        severity=4
    )

    graph.add_node(
        "Village Isolation",
        severity=5
    )

    graph.add_node(
        "Communication Failure",
        severity=4
    )

    graph.add_node(
        "Rescue Delay",
        severity=5
    )

    graph.add_edge(
        "Heavy Rainfall",
        "River Rise",
        probability=0.80,
        delay=1
    )

    graph.add_edge(
        "River Rise",
        "Flooding",
        probability=0.85,
        delay=1
    )

    graph.add_edge(
        "Flooding",
        "Road Blockage",
        probability=0.70,
        delay=1
    )

    graph.add_edge(
        "Road Blockage",
        "Village Isolation",
        probability=0.75,
        delay=2
    )

    graph.add_edge(
        "Village Isolation",
        "Communication Failure",
        probability=0.50,
        delay=2
    )

    graph.add_edge(
        "Communication Failure",
        "Rescue Delay",
        probability=0.80,
        delay=1
    )

    return graph


def predict_cascade(
    graph,
    risk_score,
    rainfall,
    river_level,
    confidence=100
):

    active_nodes = []

    if rainfall >= 45:
        active_nodes.append(
            "Heavy Rainfall"
        )

    if river_level >= 4:
        active_nodes.append(
            "River Rise"
        )

    if risk_score >= 45:
        active_nodes.append(
            "Flooding"
        )

    confidence_factor = (
        max(confidence, 30) / 100
    )

    predicted_events = []

    queue = [
        (node, 0)
        for node in active_nodes
    ]

    visited = set()

    while queue:

        current_node, current_delay = queue.pop(0)

        if current_node in visited:
            continue

        visited.add(current_node)

        for next_node in graph.successors(
            current_node
        ):

            base_probability = (
                graph[current_node][next_node]
                ["probability"]
            )

            risk_factor = (
                0.75
                + min(risk_score / 100, 1)
                * 0.35
            )

            adjusted_probability = (
                base_probability
                * risk_factor
                * confidence_factor
            )

            adjusted_probability = min(
                adjusted_probability,
                0.99
            )

            edge_delay = (
                graph[current_node][next_node]
                ["delay"]
            )

            total_delay = (
                current_delay
                + edge_delay
            )

            predicted_events.append({
                "event": next_node,
                "probability": round(
                    adjusted_probability,
                    3
                ),
                "delay": total_delay
            })

            queue.append(
                (next_node, total_delay)
            )

    return predicted_events


def calculate_cascade_severity(
    graph,
    predicted_events
):

    severity = 0

    for event in predicted_events:

        node = event["event"]

        node_severity = (
            graph.nodes[node]["severity"]
        )

        probability = event["probability"]

        severity += (
            node_severity
            * probability
        )

    return round(
        severity,
        2
    )


def assign_cascade_to_locations(
    locations,
    risk_score
):

    affected_villages = []

    for village in locations["villages"]:

        exposure = (
            risk_score / 100
            * village["vulnerability"]
        )

        affected_villages.append({
            "name": village["name"],
            "population": village["population"],
            "vulnerability": village["vulnerability"],
            "exposure": round(
                exposure,
                2
            )
        })

    affected_villages.sort(
        key=lambda x: x["exposure"],
        reverse=True
    )

    return affected_villages