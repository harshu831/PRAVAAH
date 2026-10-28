import folium


def get_risk_color(exposure):
    if exposure >= 0.60:
        return "red"
    elif exposure >= 0.30:
        return "orange"
    else:
        return "green"


def get_risk_label(exposure):
    if exposure >= 0.60:
        return "HIGH RISK"
    elif exposure >= 0.30:
        return "MEDIUM RISK"
    else:
        return "LOWER RISK"


def create_map(locations, village_risks=None):

    center_lat = 28.668
    center_lon = 77.464

    disaster_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13
    )

    # --------------------------------------------------------
    # VILLAGES
    # --------------------------------------------------------

    risk_lookup = {}

    if village_risks:

        for village in village_risks:

            risk_lookup[village["name"]] = village

    for village in locations["villages"]:

        village_name = village["name"]

        risk_info = risk_lookup.get(
            village_name,
            {}
        )

        exposure = risk_info.get(
            "exposure",
            0
        )

        priority = risk_info.get(
            "priority",
            0
        )

        accessibility = risk_info.get(
            "accessibility",
            0
        )

        rescue_demand = risk_info.get(
            "rescue_demand",
            0
        )

        risk_color = get_risk_color(
            exposure
        )

        risk_label = get_risk_label(
            exposure
        )

        popup_html = f"""
        <b>{village_name}</b><br>
        <br>
        Population: {village["population"]}<br>
        Vulnerability: {village["vulnerability"] * 100:.0f}%<br>
        Exposure: {exposure * 100:.1f}%<br>
        Priority Score: {priority:.1f}<br>
        Accessibility: {accessibility * 100:.0f}%<br>
        Rescue Demand: {rescue_demand}<br>
        <b>Status: {risk_label}</b>
        """

        folium.CircleMarker(
            location=[
                village["latitude"],
                village["longitude"]
            ],
            radius=12,
            color=risk_color,
            fill=True,
            fill_color=risk_color,
            fill_opacity=0.75,
            popup=folium.Popup(
                popup_html,
                max_width=300
            ),
            tooltip=(
                f"{village_name} | "
                f"{risk_label}"
            )
        ).add_to(disaster_map)

    # --------------------------------------------------------
    # SHELTERS
    # --------------------------------------------------------

    for shelter in locations["shelters"]:

        popup_html = f"""
        <b>{shelter["name"]}</b><br>
        Type: Emergency Shelter<br>
        Capacity: {shelter["capacity"]} people
        """

        folium.Marker(
            location=[
                shelter["latitude"],
                shelter["longitude"]
            ],
            popup=folium.Popup(
                popup_html,
                max_width=250
            ),
            tooltip=shelter["name"],
            icon=folium.Icon(
                icon="plus",
                prefix="fa"
            )
        ).add_to(disaster_map)

    # --------------------------------------------------------
    # SENSORS
    # --------------------------------------------------------

    for sensor in locations["sensors"]:

        folium.CircleMarker(
            location=[
                sensor["latitude"],
                sensor["longitude"]
            ],
            radius=6,
            popup=sensor["name"],
            tooltip=sensor["name"],
            fill=True,
            fill_opacity=0.9
        ).add_to(disaster_map)

    # --------------------------------------------------------
    # ROADS
    # --------------------------------------------------------

    for road in locations["roads"]:

        folium.PolyLine(
            locations=[
                road["start"],
                road["end"]
            ],
            weight=4,
            tooltip=road["name"]
        ).add_to(disaster_map)

    # --------------------------------------------------------
    # MAP LEGEND
    # --------------------------------------------------------

    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        width: 180px;
        background-color: white;
        border: 2px solid grey;
        z-index: 9999;
        font-size: 14px;
        padding: 10px;
        border-radius: 8px;
    ">
        <b>PRAVAAH Risk Map</b><br><br>

        <span style="
            display:inline-block;
            width:12px;
            height:12px;
            background:red;
            border-radius:50%;
        "></span>
        High Risk<br><br>

        <span style="
            display:inline-block;
            width:12px;
            height:12px;
            background:orange;
            border-radius:50%;
        "></span>
        Medium Risk<br><br>

        <span style="
            display:inline-block;
            width:12px;
            height:12px;
            background:green;
            border-radius:50%;
        "></span>
        Lower Risk<br><br>

        ✚ Emergency Shelter<br>
        ● Environmental Sensor
    </div>
    """

    disaster_map.get_root().html.add_child(
        folium.Element(
            legend_html
        )
    )

    return disaster_map