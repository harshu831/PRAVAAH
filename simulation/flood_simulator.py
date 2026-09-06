GRID_SIZE = 8

ELEVATION_GRID = [
    [0.90, 0.85, 0.80, 0.78, 0.82, 0.88, 0.92, 0.95],
    [0.80, 0.72, 0.65, 0.60, 0.62, 0.70, 0.82, 0.90],
    [0.72, 0.60, 0.52, 0.45, 0.47, 0.55, 0.68, 0.80],
    [0.65, 0.52, 0.40, 0.30, 0.32, 0.42, 0.55, 0.72],
    [0.62, 0.48, 0.35, 0.22, 0.25, 0.38, 0.52, 0.70],
    [0.68, 0.55, 0.42, 0.31, 0.34, 0.45, 0.58, 0.74],
    [0.76, 0.65, 0.55, 0.48, 0.50, 0.58, 0.70, 0.82],
    [0.88, 0.80, 0.72, 0.68, 0.70, 0.76, 0.84, 0.92]
]

VILLAGE_CELLS = {
    "Village A": (3, 3),
    "Village B": (4, 5),
    "Village C": (5, 2)
}


def get_neighbors(row, col):

    neighbors = []

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    for dr, dc in directions:

        nr = row + dr
        nc = col + dc

        if (
            0 <= nr < GRID_SIZE
            and 0 <= nc < GRID_SIZE
        ):
            neighbors.append(
                (nr, nc)
            )

    return neighbors


def simulate_flood(
    rainfall,
    river_level,
    steps=4,
    road_failures=0,
    communication_failures=0
):

    rainfall_factor = min(
        rainfall / 120,
        1
    )

    river_factor = min(
        river_level / 10,
        1
    )

    hazard = (
        rainfall_factor * 0.55
        + river_factor * 0.45
    )

    grid = [
        [0 for _ in range(GRID_SIZE)]
        for _ in range(GRID_SIZE)
    ]

    seed_cells = [
        (3, 3),
        (4, 3),
        (4, 4)
    ]

    if hazard >= 0.25:

        for row, col in seed_cells:
            grid[row][col] = 1

    for step in range(steps):

        new_grid = [
            row[:]
            for row in grid
        ]

        step_pressure = (
            hazard
            * (1 + step * 0.06)
        )

        for row in range(GRID_SIZE):

            for col in range(GRID_SIZE):

                elevation = (
                    ELEVATION_GRID[row][col]
                )

                flooded_neighbors = 0

                for nr, nc in get_neighbors(
                    row,
                    col
                ):

                    if grid[nr][nc] == 1:
                        flooded_neighbors += 1

                neighbor_effect = (
                    flooded_neighbors * 0.09
                )

                flood_pressure = (
                    step_pressure
                    + neighbor_effect
                )

                if flood_pressure > (
                    elevation + 0.16
                ):

                    new_grid[row][col] = 1

        grid = new_grid

    flooded_cells = sum(
        sum(row)
        for row in grid
    )

    total_cells = (
        GRID_SIZE * GRID_SIZE
    )

    flood_ratio = (
        flooded_cells / total_cells
    )

    communication_coverage = max(
        0,
        100 - communication_failures * 25
    )

    road_access = max(
        0,
        100 - road_failures * 25
    )

    return {
        "grid": grid,
        "flooded_cells": flooded_cells,
        "flood_ratio": round(
            flood_ratio,
            2
        ),
        "blocked_roads": road_failures,
        "road_access": road_access,
        "communication_coverage":
            communication_coverage,
        "hazard_index": round(
            hazard,
            2
        )
    }


def get_village_impacts(
    locations,
    simulation_result
):

    impacts = []

    grid = simulation_result["grid"]

    for village in locations["villages"]:

        cell = VILLAGE_CELLS.get(
            village["name"]
        )

        flooded = False

        if cell:

            row, col = cell

            flooded = (
                grid[row][col] == 1
            )

        impacts.append({
            "name": village["name"],
            "population":
                village["population"],
            "vulnerability":
                village["vulnerability"],
            "flooded": flooded
        })

    return impacts