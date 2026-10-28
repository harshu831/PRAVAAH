
import streamlit as st
import pandas as pd

from streamlit_folium import st_folium

from utils.sensor_simulator import (
    generate_sensor_data,
    generate_sensor_health,
)
from utils.location_data import get_locations
from utils.map import create_map

from models.risk_model import (
    calculate_flood_risk,
    get_risk_state,
)
from models.pravaah_pipeline import assess_environment

from models.precursor import (
    calculate_risk_trend,
    get_precursor_status,
    estimate_time_to_threshold,
)
from models.uncertainty import (
    calculate_uncertainty,
    get_confidence_status,
    detect_blind_zone,
)
from models.cascade import (
    create_cascade_graph,
    predict_cascade,
    calculate_cascade_severity,
    assign_cascade_to_locations,
)
from models.resource import (
    create_road_network,
    calculate_accessibility,
    calculate_rescue_demand,
    calculate_priority,
    get_priority_level,
    allocate_resources,
    summarize_allocation,
)
from models.failure import (
    determine_system_mode,
    calculate_retained_capability,
)
from models.fallback import emergency_fallback

from simulation.flood_simulator import (
    simulate_flood,
    get_village_impacts,
)
from models.counterfactual import compare_scenarios
from models.memory import (
    load_events,
    save_event,
    find_similar_events,
)
from models.ai_risk_model import (
    train_model,
    predict_ai_risk,
    get_ai_risk_state,
    get_feature_importance,
    calculate_feature_contribution,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PRAVAAH",
    page_icon="🌊",
    layout="wide",
)


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 20px;
    }
    .small-note {
        font-size: 0.85rem;
        color: #666;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">🌊 PRAVAAH</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    Predictive Resilience & Adaptive Vulnerability-Aware Alerting Hub
    </div>
    """,
    unsafe_allow_html=True,
)

st.write(
    "A failure-resilient environmental intelligence system for "
    "early hazard detection, uncertainty-aware prediction, "
    "cascading-risk analysis, resource allocation and disaster "
    "response planning."
)

st.divider()


# ============================================================
# SESSION STATE
# ============================================================

if "ai_model" not in st.session_state:
    st.session_state.ai_model = train_model()

if "history" not in st.session_state:
    st.session_state.history = []

if "latest_sensor_data" not in st.session_state:
    st.session_state.latest_sensor_data = None

if "latest_sensor_health" not in st.session_state:
    st.session_state.latest_sensor_health = None

if "event_saved" not in st.session_state:
    st.session_state.event_saved = False

if "twin_result" not in st.session_state:
    st.session_state.twin_result = None


# ============================================================
# LOAD LOCATIONS
# ============================================================

locations = get_locations()


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.header("⚙️ PRAVAAH Controls")
st.sidebar.subheader("🎬 Hackathon Demo Scenario")

scenario = st.sidebar.selectbox(
    "Select demonstration scenario",
    [
        "Live Environment",
        "🌧️ Heavy Rainfall",
        "🌊 Severe Flood",
        "📡 Sensor Blind Zone",
        "🚨 Infrastructure Failure",
        "💥 Cascading Disaster",
    ],
)

st.sidebar.caption(
    "Demonstration scenarios use controlled synthetic conditions."
)

st.sidebar.subheader("Failure Simulation")

communication_available = st.sidebar.checkbox(
    "Communication Available",
    value=True,
)

cloud_available = st.sidebar.checkbox(
    "Cloud Available",
    value=True,
)

gps_available = st.sidebar.checkbox(
    "GPS Available",
    value=True,
)

manual_sensor_failure = st.sidebar.slider(
    "Additional Sensor Failure",
    min_value=0,
    max_value=10,
    value=0,
)

st.sidebar.divider()
st.sidebar.subheader("Simulation")

run_simulation = st.sidebar.button(
    "🔄 Generate New Environmental Reading"
)

clear_history = st.sidebar.button(
    "🗑️ Clear Simulation History"
)

if clear_history:
    st.session_state.history = []
    st.session_state.latest_sensor_data = None
    st.session_state.latest_sensor_health = None
    st.session_state.event_saved = False
    st.session_state.twin_result = None
    st.rerun()


# ============================================================
# GENERATE ENVIRONMENTAL DATA
# ============================================================

if (
    run_simulation
    or st.session_state.latest_sensor_data is None
    or st.session_state.latest_sensor_health is None
):
    sensor_data = generate_sensor_data()
    sensor_health = generate_sensor_health()

    st.session_state.latest_sensor_data = dict(sensor_data)
    st.session_state.latest_sensor_health = dict(sensor_health)

else:
    sensor_data = dict(st.session_state.latest_sensor_data)
    sensor_health = dict(st.session_state.latest_sensor_health)

# Always modify a local copy. Scenario overrides should not
# contaminate the stored base sensor-health values.
sensor_health = dict(sensor_health)

sensor_health["missing_sensors"] = min(
    sensor_health["total_sensors"],
    max(
        0,
        int(sensor_health.get("missing_sensors", 0))
        + manual_sensor_failure,
    ),
)


# ============================================================
# EXTRACT ENVIRONMENTAL VARIABLES
# ============================================================

rainfall = float(sensor_data["rainfall"])
soil_moisture = float(sensor_data["soil_moisture"])
river_level = float(sensor_data["river_level"])
temperature = float(sensor_data["temperature"])
humidity = float(sensor_data["humidity"])


# ============================================================
# SCENARIO OVERRIDES
# ============================================================

scenario_message = ""

if scenario == "🌧️ Heavy Rainfall":
    rainfall = 75.0
    soil_moisture = 65.0
    river_level = 5.0
    temperature = 29.0
    humidity = 82.0

    scenario_message = (
        "Heavy rainfall is creating an emerging flood precursor."
    )

elif scenario == "🌊 Severe Flood":
    rainfall = 95.0
    soil_moisture = 82.0
    river_level = 7.5
    temperature = 31.0
    humidity = 88.0

    sensor_health["missing_sensors"] = min(
        sensor_health["total_sensors"], 4
    )
    sensor_health["coverage"] = 0.45
    sensor_health["data_age"] = 65.0

    scenario_message = (
        "Severe flood conditions with degraded sensor coverage."
    )

elif scenario == "📡 Sensor Blind Zone":
    rainfall = 80.0
    soil_moisture = 70.0
    river_level = 5.8
    temperature = 30.0
    humidity = 84.0

    sensor_health["missing_sensors"] = min(
        sensor_health["total_sensors"], 6
    )
    sensor_health["coverage"] = 0.35
    sensor_health["data_age"] = 75.0

    scenario_message = (
        "Dangerous environmental conditions coincide with "
        "severely degraded sensor coverage."
    )

elif scenario == "🚨 Infrastructure Failure":
    rainfall = 85.0
    soil_moisture = 75.0
    river_level = 6.5
    temperature = 30.0
    humidity = 86.0

    communication_available = False
    cloud_available = False

    scenario_message = (
        "Critical infrastructure dependencies have failed."
    )

elif scenario == "💥 Cascading Disaster":
    rainfall = 105.0
    soil_moisture = 88.0
    river_level = 8.2
    temperature = 32.0
    humidity = 92.0

    sensor_health["missing_sensors"] = min(
        sensor_health["total_sensors"], 5
    )
    sensor_health["coverage"] = 0.40
    sensor_health["data_age"] = 70.0

    communication_available = False
    cloud_available = False
    gps_available = False

    scenario_message = (
        "Multiple environmental and infrastructure failures "
        "are interacting."
    )

if scenario_message:
    st.warning(f"🎬 **Active Demo Scenario:** {scenario_message}")


# ============================================================
# SENSOR HEALTH
# ============================================================

total_sensors = max(
    0, int(sensor_health["total_sensors"])
)

missing_sensors = min(
    total_sensors,
    max(0, int(sensor_health["missing_sensors"])),
)

coverage = float(sensor_health["coverage"])
coverage = min(max(coverage, 0.0), 1.0)

data_age = max(0.0, float(sensor_health["data_age"]))


# ============================================================
# AI RISK AND RULE-BASED FALLBACK
# ============================================================

ai_risk_score = predict_ai_risk(
    st.session_state.ai_model,
    rainfall,
    soil_moisture,
    river_level,
    temperature,
    humidity,
)

ai_risk_state = get_ai_risk_state(ai_risk_score)

fallback_risk_score = calculate_flood_risk(
    rainfall,
    soil_moisture,
    river_level,
)

fallback_risk_state = get_risk_state(fallback_risk_score)

# The AI score remains the primary dashboard score.
risk_score = ai_risk_score
risk_state = ai_risk_state


# ============================================================
# RISK HISTORY
# ============================================================

current_record = {
    "rainfall": rainfall,
    "soil_moisture": soil_moisture,
    "river_level": river_level,
    "temperature": temperature,
    "humidity": humidity,
    "risk_score": risk_score,
}

if (
    not st.session_state.history
    or st.session_state.history[-1] != current_record
):
    st.session_state.history.append(current_record)

# Prevent an indefinitely growing in-memory history.
st.session_state.history = st.session_state.history[-200:]
history = st.session_state.history


# ============================================================
# RISK PRECURSOR
# ============================================================

risk_trend = calculate_risk_trend(history)
precursor_status = get_precursor_status(risk_trend)

time_to_critical = estimate_time_to_threshold(
    risk_score,
    risk_trend,
    75,
)


# ============================================================
# INTEGRATED PIPELINE
# ============================================================

pipeline_result = assess_environment(
    {
        "rainfall": rainfall,
        "soil_moisture": soil_moisture,
        "river_level": river_level,
        "location": "Simulated Monitoring Area",
        "data_source": "simulated",
    },
    data_age=data_age,
    risk_trend=risk_trend,
)


# ============================================================
# 1. ENVIRONMENTAL MONITORING
# ============================================================

st.header("1️⃣ Environmental Monitoring")

env1, env2, env3, env4, env5 = st.columns(5)

with env1:
    st.metric("Rainfall", f"{rainfall:.1f} mm")

with env2:
    st.metric("Soil Moisture", f"{soil_moisture:.1f}%")

with env3:
    st.metric("River Level", f"{river_level:.2f} m")

with env4:
    st.metric("Temperature", f"{temperature:.1f} °C")

with env5:
    st.metric("Humidity", f"{humidity:.1f}%")

st.caption(
    "Environmental readings are synthetic prototype data, "
    "not live measurements from field sensors."
)

st.divider()


# ============================================================
# 2. ENVIRONMENTAL RISK
# ============================================================

st.header("2️⃣ Environmental Risk")

risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)

with risk_col1:
    st.metric("AI Risk Score", f"{risk_score:.1f}/100")

with risk_col2:
    st.metric("Risk State", risk_state)

with risk_col3:
    st.metric("Risk Trend", f"{risk_trend:+.1f}")

with risk_col4:
    threshold_value = (
        "N/A"
        if time_to_critical is None
        else f"{time_to_critical} steps"
    )
    st.metric("Time to Critical", threshold_value)

if risk_state == "Hazard":
    st.error("🚨 HAZARD: High-risk conditions indicated.")
elif risk_state == "Critical":
    st.warning("⚠️ CRITICAL: Conditions require attention.")
elif risk_state == "Vulnerable":
    st.warning("🟡 VULNERABLE: Increase environmental monitoring.")
else:
    st.success("🟢 STABLE: Current simulated conditions are stable.")

st.write(f"**Risk Precursor:** {precursor_status}")

if time_to_critical is None:
    st.write(
        "**Estimated time to critical threshold:** "
        "Not currently estimable from the observed trend."
    )
else:
    st.write(
        f"**Estimated time to critical threshold:** "
        f"{time_to_critical} simulation steps."
    )

st.caption(
    "The AI model is a prototype Random Forest trained on "
    "synthetic scenarios. Its scores are not validated forecasts."
)

st.divider()


# ============================================================
# AI EXPLAINABILITY
# ============================================================

st.subheader("🤖 AI Explainability")

feature_importance = get_feature_importance(
    st.session_state.ai_model
)

feature_contribution = calculate_feature_contribution(
    rainfall=rainfall,
    soil_moisture=soil_moisture,
    river_level=river_level,
    temperature=temperature,
    humidity=humidity,
)

explain_col1, explain_col2 = st.columns(2)

with explain_col1:
    st.write("### Model Feature Importance")

    importance_df = pd.DataFrame(feature_importance)

    if not importance_df.empty and {
        "Feature", "Importance"
    }.issubset(importance_df.columns):
        st.bar_chart(
            importance_df.set_index("Feature")["Importance"]
        )
    else:
        st.info("Feature-importance data is unavailable.")

with explain_col2:
    st.write("### Current Event Contribution")

    contribution_df = pd.DataFrame(feature_contribution)

    st.dataframe(
        contribution_df,
        width="stretch",
        hide_index=True,
    )

if feature_contribution:
    dominant_factor = feature_contribution[0]

    st.info(
        f"**Dominant current factor:** "
        f"{dominant_factor['Feature']} "
        f"({dominant_factor['Contribution']:.1f}% "
        f"of the prototype contribution estimate)."
    )

with st.expander("AI vs Rule-Based Prediction"):
    comparison_df = pd.DataFrame([
        {
            "Model": "AI Random Forest",
            "Risk Score": ai_risk_score,
            "Risk State": ai_risk_state,
        },
        {
            "Model": "Rule-Based Fallback",
            "Risk Score": fallback_risk_score,
            "Risk State": fallback_risk_state,
        },
        {
            "Model": "Integrated Pipeline",
            "Risk Score": pipeline_result["risk_score"],
            "Risk State": pipeline_result["risk_state"],
        },
    ])

    st.dataframe(
        comparison_df,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# RISK EVOLUTION
# ============================================================

st.subheader("📈 Risk Evolution")

if len(history) >= 2:
    history_df = pd.DataFrame(history)
    st.line_chart(history_df["risk_score"])
else:
    st.info("Generate additional readings to show risk evolution.")

st.divider()


# ============================================================
# 3. UNCERTAINTY AND BLIND-ZONE DETECTION
# ============================================================

st.header("3️⃣ Uncertainty & Blind-Zone Detection")

confidence = calculate_uncertainty(
    total_sensors,
    missing_sensors,
    data_age,
    coverage,
    risk_trend=risk_trend,
)

confidence_status = get_confidence_status(confidence)

blind_zone = detect_blind_zone(
    total_sensors,
    missing_sensors,
    coverage,
)

u1, u2, u3, u4 = st.columns(4)

with u1:
    st.metric("Sensor Confidence", f"{confidence:.1f}%")

with u2:
    st.metric("Missing Sensors", missing_sensors)

with u3:
    st.metric("Coverage", f"{coverage * 100:.1f}%")

with u4:
    st.metric("Data Age", f"{data_age:.1f} min")

st.write(f"**Confidence Status:** {confidence_status}")

if blind_zone:
    st.error("🔴 BLIND ZONE DETECTED: Sensor visibility is degraded.")
else:
    st.success("🟢 No major sensor blind zone detected.")

st.caption(
    "Confidence is a heuristic data-quality indicator, not a "
    "calibrated probability that a forecast is correct."
)

st.divider()


# ============================================================
# INTEGRATED PRAVAAH ASSESSMENT
# ============================================================

st.header("🔗 Integrated PRAVAAH Assessment")

p1, p2, p3, p4 = st.columns(4)

with p1:
    st.metric(
        "Pipeline Rule-Based Risk",
        f"{pipeline_result['risk_score']:.1f}/100",
    )

with p2:
    st.metric(
        "Pipeline Confidence",
        f"{pipeline_result['confidence']:.1f}%",
    )

with p3:
    st.metric(
        "Pipeline Signal Coverage",
        f"{pipeline_result['coverage_percent']:.0f}%",
    )

with p4:
    st.metric(
        "Pipeline Cascade Events",
        len(pipeline_result["cascade_events"]),
    )

st.write(f"**Pipeline Risk State:** {pipeline_result['risk_state']}")
st.write(
    f"**Pipeline Confidence Status:** "
    f"{pipeline_result['confidence_status']}"
)
st.write(
    f"**Pipeline Cascade Status:** "
    f"{pipeline_result['cascade_status']}"
)

st.info(pipeline_result["uncertainty_message"])

if pipeline_result["blind_zone"]:
    st.warning("The integrated pipeline identifies a sensor blind zone.")

missing_signals = pipeline_result["risk_details"].get(
    "missing_signals", []
)

if missing_signals:
    st.warning("Missing signals: " + ", ".join(missing_signals))

if pipeline_result["cascade_events"]:
    pipeline_cascade_df = pd.DataFrame([
        {
            "Event": event["event"],
            "Estimated Probability": (
                f"{event['probability'] * 100:.1f}%"
            ),
            "Estimated Delay": f"{event['delay']} steps",
        }
        for event in pipeline_result["cascade_events"]
    ])

    st.dataframe(
        pipeline_cascade_df,
        width="stretch",
        hide_index=True,
    )

st.caption(
    "Pipeline results use rule-based risk. The dashboard cascade "
    "below uses the primary AI risk score. Both are prototype estimates."
)

st.divider()


# ============================================================
# 4. FAILURE-FIRST ARCHITECTURE
# ============================================================

st.header("4️⃣ Failure-First Architecture")

system_mode = determine_system_mode(
    sensor_health=confidence,
    communication_available=communication_available,
    cloud_available=cloud_available,
    gps_available=gps_available,
)

retained_capability = calculate_retained_capability(system_mode)

failure_col1, failure_col2, failure_col3, failure_col4 = (
    st.columns(4)
)

with failure_col1:
    st.metric("System Mode", system_mode)

with failure_col2:
    st.metric("Retained Capability", f"{retained_capability}%")

with failure_col3:
    st.metric(
        "Communication",
        "ONLINE" if communication_available else "OFFLINE",
    )

with failure_col4:
    dependencies_available = cloud_available and gps_available
    st.metric(
        "Cloud / GPS",
        "AVAILABLE" if dependencies_available else "DEGRADED",
    )

if system_mode == "Normal":
    st.success("🟢 NORMAL MODE: Major dependencies are available.")
elif system_mode == "Degraded":
    st.warning(
        "🟡 DEGRADED MODE: Some services are unavailable."
    )
elif system_mode == "Emergency":
    st.error(
        "🔴 EMERGENCY MODE: Critical dependencies have failed."
    )
else:
    st.error(
        "⚫ ISOLATED MODE: Network, cloud and GPS are unavailable."
    )

fallback_action = emergency_fallback(risk_score)
st.info(f"**Fallback Action:** {fallback_action}")

st.divider()


# ============================================================
# COMMAND CENTER
# ============================================================

st.header("🚨 PRAVAAH Command Center")

summary_points = [
    f"AI environmental risk is **{risk_score:.1f}/100**, "
    f"with state **{risk_state}**."
]

if risk_trend > 0:
    summary_points.append(
        f"Risk is increasing by approximately "
        f"**{risk_trend:.1f} points per simulation step**."
    )
elif risk_trend < 0:
    summary_points.append(
        f"Risk is decreasing by approximately "
        f"**{abs(risk_trend):.1f} points per simulation step**."
    )
else:
    summary_points.append("Risk is currently stable.")

if blind_zone:
    summary_points.append(
        "A **sensor blind zone** is active. Interpret predictions "
        "with caution."
    )

if system_mode != "Normal":
    summary_points.append(
        f"The system is operating in **{system_mode} mode**, "
        f"with **{retained_capability}% retained capability**."
    )

for point in summary_points:
    st.write(f"• {point}")

st.divider()


# ============================================================
# 5. CASCADING DISASTER ENGINE
# ============================================================

st.header("5️⃣ Cascading Disaster Engine")

cascade_graph = create_cascade_graph()

predicted_events = predict_cascade(
    cascade_graph,
    risk_score,
    rainfall,
    river_level,
    confidence=confidence,
)

cascade_severity = calculate_cascade_severity(
    cascade_graph,
    predicted_events,
)

cascade_col1, cascade_col2 = st.columns(2)

with cascade_col1:
    st.metric("Cascade Severity Index", f"{cascade_severity:.2f}")

with cascade_col2:
    st.metric("Predicted Cascade Events", len(predicted_events))

if predicted_events:
    cascade_df = pd.DataFrame([
        {
            "Predicted Event": event["event"],
            "Estimated Probability": (
                f"{event['probability'] * 100:.1f}%"
            ),
            "Estimated Delay": f"{event['delay']} steps",
        }
        for event in predicted_events
    ])

    st.dataframe(
        cascade_df,
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No major cascade chain is currently activated.")

st.caption(
    "Cascade probabilities are heuristic estimates, not "
    "calibrated forecasts from observed disasters."
)

st.divider()


# ============================================================
# 6. LOCALIZED RISK INTELLIGENCE
# ============================================================

st.header("6️⃣ Localized Risk Intelligence")

localized_villages = assign_cascade_to_locations(
    locations,
    risk_score,
)

accessibility_graph = create_road_network(locations)

village_table = []

for village in localized_villages:
    accessibility = calculate_accessibility(
        accessibility_graph,
        village["name"],
    )

    demand = calculate_rescue_demand(
        village["population"],
        village["exposure"],
        village["vulnerability"],
    )

    priority = calculate_priority(
        exposure=village["exposure"],
        vulnerability=village["vulnerability"],
        accessibility=accessibility,
        time_to_critical=time_to_critical,
        cascade_severity=cascade_severity,
    )

    village["accessibility"] = accessibility
    village["rescue_demand"] = demand
    village["priority"] = priority
    village["priority_level"] = get_priority_level(priority)

    village_table.append({
        "Village": village["name"],
        "Population": village["population"],
        "Vulnerability": f"{village['vulnerability'] * 100:.0f}%",
        "Exposure": f"{village['exposure'] * 100:.1f}%",
        "Accessibility": f"{accessibility * 100:.0f}%",
        "Rescue Demand": demand,
        "Priority": priority,
        "Priority Level": village["priority_level"],
    })

st.dataframe(
    pd.DataFrame(village_table),
    width="stretch",
    hide_index=True,
)

st.subheader("🗺️ Environmental Risk Map")

disaster_map = create_map(locations, localized_villages)

st_folium(
    disaster_map,
    width=1200,
    height=550,
)

st.caption(
    "Map locations are synthetic and do not represent verified "
    "government infrastructure."
)

st.divider()


# ============================================================
# 7. RESOURCE-AWARE RESCUE
# ============================================================

st.header("7️⃣ Resource-Aware Rescue")

resource_allocations = allocate_resources(
    villages=localized_villages,
    resources=locations.get("resources", []),
    graph=accessibility_graph,
    risk_score=risk_score,
)

allocation_rows = []

for allocation in resource_allocations:
    travel_time = allocation["travel_time"]

    allocation_rows.append({
        "Village": allocation["village"],
        "Resource": allocation["resource"],
        "Resource Type": allocation["resource_type"],
        "Capacity": allocation["capacity"],
        "Travel Time": (
            f"{travel_time:.1f} min"
            if travel_time is not None
            else "N/A"
        ),
        "Covered People": allocation["covered_people"],
        "Remaining Demand": allocation["remaining_demand"],
        "Allocation Score": allocation["allocation_score"],
        "Status": allocation["status"],
    })

if allocation_rows:
    st.dataframe(
        pd.DataFrame(allocation_rows),
        width="stretch",
        hide_index=True,
    )

    # Summarize the final demand snapshot for each village.
    village_demand = {}

    for allocation in resource_allocations:
        village_demand[allocation["village"]] = (
            allocation["remaining_demand"]
        )

    demand_df = pd.DataFrame([
        {
            "Village": village,
            "Final Remaining Demand": demand,
            "Status": "Unmet Demand" if demand > 0 else "Covered",
        }
        for village, demand in village_demand.items()
    ])

    st.subheader("Village-Level Demand Summary")
    st.dataframe(
        demand_df,
        width="stretch",
        hide_index=True,
    )

else:
    st.info("No resource allocation records were generated.")

# Use the summary helper so dashboard totals match allocation records.
allocation_summary = summarize_allocation(resource_allocations)

resource_col1, resource_col2, resource_col3, resource_col4 = (
    st.columns(4)
)

with resource_col1:
    st.metric(
        "Resources Allocated",
        allocation_summary["allocated_count"],
    )

with resource_col2:
    st.metric(
        "Villages with Unmet Demand",
        allocation_summary["unmet_count"],
    )

with resource_col3:
    st.metric(
        "People Covered",
        allocation_summary["covered_people"],
    )

with resource_col4:
    st.metric(
        "Remaining Demand",
        allocation_summary["remaining_demand"],
    )

if allocation_summary["unmet_count"] > 0:
    st.warning(
        "⚠️ Available resources cannot cover all estimated demand."
    )
else:
    st.success(
        "🟢 All estimated demand is covered by the current simulation."
    )

st.caption(
    "Allocation is a prototype heuristic. It does not account for "
    "live dispatch conditions or replace emergency-service decisions."
)

st.divider()


# ============================================================
# 8. DISASTER DIGITAL TWIN
# ============================================================

st.header("8️⃣ Disaster Digital Twin")

st.write(
    "Test hypothetical disaster conditions using the simulation."
)

dt1, dt2, dt3, dt4 = st.columns(4)

with dt1:
    twin_rainfall = st.slider(
        "Scenario Rainfall",
        min_value=0,
        max_value=120,
        value=int(min(max(rainfall, 0), 120)),
    )

with dt2:
    twin_river = st.slider(
        "Scenario River Level",
        min_value=0.0,
        max_value=10.0,
        value=float(min(max(river_level, 0), 10)),
        step=0.1,
    )

with dt3:
    twin_road_failures = st.slider(
        "Road Failures",
        min_value=0,
        max_value=4,
        value=0,
    )

with dt4:
    twin_communication_failures = st.slider(
        "Communication Failures",
        min_value=0,
        max_value=4,
        value=0,
    )

if st.button("🧪 Run Digital Twin Scenario", type="primary"):
    st.session_state.twin_result = simulate_flood(
        rainfall=twin_rainfall,
        river_level=twin_river,
        steps=4,
        road_failures=twin_road_failures,
        communication_failures=twin_communication_failures,
    )

if st.session_state.twin_result is not None:
    twin_result = st.session_state.twin_result

    twin1, twin2, twin3, twin4 = st.columns(4)

    with twin1:
        st.metric("Flooded Cells", twin_result["flooded_cells"])

    with twin2:
        st.metric(
            "Flood Ratio",
            f"{twin_result['flood_ratio'] * 100:.1f}%",
        )

    with twin3:
        st.metric("Blocked Roads", twin_result["blocked_roads"])

    with twin4:
        st.metric(
            "Communication Coverage",
            f"{twin_result['communication_coverage']}%",
        )

    st.subheader("Simulated Flood Grid")

    st.dataframe(
        pd.DataFrame(twin_result["grid"]),
        width="stretch",
        hide_index=True,
    )

    village_impacts = get_village_impacts(
        locations,
        twin_result,
    )

    impact_rows = [
        {
            "Village": village["name"],
            "Population": village["population"],
            "Vulnerability": (
                f"{village['vulnerability'] * 100:.0f}%"
            ),
            "Flooded": "YES" if village["flooded"] else "NO",
        }
        for village in village_impacts
    ]

    st.subheader("Village Impacts")

    st.dataframe(
        pd.DataFrame(impact_rows),
        width="stretch",
        hide_index=True,
    )
else:
    st.info("Run a Digital Twin scenario to simulate flood propagation.")

st.divider()


# ============================================================
# 9. COUNTERFACTUAL RESCUE
# ============================================================

st.header("9️⃣ Counterfactual Rescue")

st.write(
    "Compare alternative response strategies under the same "
    "simulated environmental conditions."
)

available_boats = sum(
    1
    for resource in locations.get("resources", [])
    if resource.get("type") == "Boat"
    and resource.get("available", False)
)

counterfactual_scenarios = compare_scenarios(
    locations=locations,
    rainfall=twin_rainfall,
    river_level=twin_river,
    road_failures=twin_road_failures,
    communication_failures=twin_communication_failures,
    available_boats=available_boats,
)

best_strategy = None

if counterfactual_scenarios:
    counterfactual_df = pd.DataFrame(counterfactual_scenarios)

    expected_columns = [
        "strategy",
        "exposed_population",
        "people_protected",
        "protection_rate",
        "evacuation_time",
        "isolation_duration",
        "flooded_cells",
        "communication_coverage",
    ]

    available_columns = [
        column
        for column in expected_columns
        if column in counterfactual_df.columns
    ]

    counterfactual_df = counterfactual_df[available_columns]

    rename_map = {
        "strategy": "Strategy",
        "exposed_population": "Estimated Exposed Population",
        "people_protected": "People Protected",
        "protection_rate": "Protection Rate",
        "evacuation_time": "Evacuation Time",
        "isolation_duration": "Isolation Duration",
        "flooded_cells": "Flooded Cells",
        "communication_coverage": "Communication Coverage",
    }

    st.dataframe(
        counterfactual_df.rename(columns=rename_map),
        width="stretch",
        hide_index=True,
    )

    best_strategy = min(
        counterfactual_scenarios,
        key=lambda item: (
            item.get("exposed_population", float("inf")),
            item.get("evacuation_time", float("inf")),
            item.get("isolation_duration", float("inf")),
        ),
    )

    st.success(
        f"**Recommended simulated strategy:** "
        f"{best_strategy['strategy']}"
    )

    st.caption(
        "Results are simulated planning estimates, not claims "
        "about actual lives saved."
    )
else:
    st.info("No counterfactual scenarios were generated.")

st.divider()


# ============================================================
# 10. DISASTER MEMORY
# ============================================================

st.header("🔟 Disaster Memory")

st.write(
    "Store simulated events and retrieve similar historical cases."
)

memory_col1, memory_col2 = st.columns(2)

with memory_col1:
    if st.button("💾 Store Current Event"):
        event = {
            "rainfall": rainfall,
            "river_level": river_level,
            "soil_moisture": soil_moisture,
            "temperature": temperature,
            "humidity": humidity,
            "risk_score": risk_score,
            "risk_state": risk_state,
            "cascade_severity": cascade_severity,
            "system_mode": system_mode,
            "confidence": confidence,
            "blind_zone": blind_zone,
            "best_strategy": (
                best_strategy["strategy"]
                if best_strategy is not None
                else "No strategy available"
            ),
            "data_source": "simulated",
        }

        save_event(event)
        st.session_state.event_saved = True

with memory_col2:
    stored_events = load_events()
    st.metric("Stored Disaster Events", len(stored_events))

if st.session_state.event_saved:
    st.success("Current event stored in Disaster Memory.")

similar_events = find_similar_events(
    rainfall=rainfall,
    river_level=river_level,
    risk_score=risk_score,
    limit=5,
)

if similar_events:
    memory_rows = []

    for item in similar_events:
        event = item["event"]

        memory_rows.append({
            "Similarity": f"{item['similarity']:.1f}%",
            "Rainfall": f"{event.get('rainfall', 0):.1f}",
            "River Level": f"{event.get('river_level', 0):.2f}",
            "Risk Score": f"{event.get('risk_score', 0):.1f}",
            "Risk State": event.get("risk_state", "Unknown"),
            "System Mode": event.get("system_mode", "Unknown"),
            "Strategy": event.get("best_strategy", "Unknown"),
        })

    st.subheader("Similar Previous Events")

    st.dataframe(
        pd.DataFrame(memory_rows),
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No similar previous events were found.")

st.divider()


# ============================================================
# 11. DECISION SUPPORT
# ============================================================

st.header("1️⃣1️⃣ PRAVAAH Decision Support")

decision_messages = []

if risk_score >= 75:
    decision_messages.append("🚨 High environmental hazard indicated.")
elif risk_score >= 50:
    decision_messages.append("⚠️ Critical environmental conditions indicated.")
elif risk_score >= 25:
    decision_messages.append("🟡 Vulnerable environmental conditions indicated.")
else:
    decision_messages.append("🟢 Current simulated conditions are stable.")

if risk_trend >= 5:
    decision_messages.append("📈 Risk is increasing rapidly.")
elif risk_trend > 0:
    decision_messages.append("📈 Risk is gradually increasing.")
elif risk_trend < 0:
    decision_messages.append("📉 Risk is decreasing.")

if blind_zone:
    decision_messages.append(
        "📡 Sensor blind zone detected. Interpret predictions cautiously."
    )

if cascade_severity > 10:
    decision_messages.append(
        "💥 Significant cascading consequences are predicted."
    )

unmet_count = 0

if unmet_count > 0:
    decision_messages.append(
        "🚑 Available resources may be insufficient for estimated demand."
    )

if system_mode in ["Emergency", "Isolated"]:
    decision_messages.append(
        "⚠️ Critical dependency failure detected. Use local fallback procedures."
    )

if best_strategy is not None:
    decision_messages.append(
        f"🧭 Simulated response recommendation: "
        f"{best_strategy['strategy']}."
    )

for message in decision_messages:
    st.write(f"• {message}")


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.subheader("📋 Executive Situation Summary")

summary_df = pd.DataFrame([
    {
        "Indicator": "AI Environmental Risk",
        "Value": f"{risk_score:.1f}/100",
        "Status": risk_state,
    },
    {
        "Indicator": "Rule-Based Pipeline Risk",
        "Value": f"{pipeline_result['risk_score']:.1f}/100",
        "Status": pipeline_result["risk_state"],
    },
    {
        "Indicator": "Risk Trend",
        "Value": f"{risk_trend:+.1f}/step",
        "Status": precursor_status,
    },
    {
        "Indicator": "Dashboard Sensor Confidence",
        "Value": f"{confidence:.1f}%",
        "Status": confidence_status,
    },
    {
        "Indicator": "Pipeline Confidence",
        "Value": f"{pipeline_result['confidence']:.1f}%",
        "Status": pipeline_result["confidence_status"],
    },
    {
        "Indicator": "Dashboard Blind Zone",
        "Value": "YES" if blind_zone else "NO",
        "Status": "Attention Required" if blind_zone else "Normal",
    },
    {
        "Indicator": "Cascade Severity",
        "Value": f"{cascade_severity:.2f}",
        "Status": "High" if cascade_severity > 10 else "Moderate",
    },
    {
        "Indicator": "System Mode",
        "Value": system_mode,
        "Status": f"{retained_capability}% capability",
    },
    {
        "Indicator": "Resources Allocated",
        "Value": str(allocation_summary["allocated_count"]),
        "Status": "Assigned",
    },
    {
        "Indicator": "People Covered",
        "Value": str(allocation_summary["covered_people"]),
        "Status": "Simulated coverage",
    },
    {
        "Indicator": "Remaining Demand",
        "Value": str(allocation_summary["remaining_demand"]),
        "Status": (
            "Shortage"
            if allocation_summary["remaining_demand"] > 0
            else "Covered"
        ),
    },
    {
        "Indicator": "Villages with Unmet Demand",
        "Value": str(allocation_summary["unmet_count"]),
        "Status": (
            "Shortage" if allocation_summary["unmet_count"] > 0
            else "Covered"
        ),
    },
])

st.dataframe(
    summary_df,
    width="stretch",
    hide_index=True,
)


# ============================================================
# INTELLIGENCE PIPELINE
# ============================================================

st.subheader("🔄 PRAVAAH Intelligence Pipeline")

st.info(
    "Environmental Change → Risk Precursor → Uncertainty Assessment → "
    "Cascade Prediction → Localized Impact → Rescue Demand → "
    "Resource Allocation → Digital Twin → Counterfactual Comparison → "
    "Disaster Memory"
)


# ============================================================
# DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "PRAVAAH is a hackathon prototype. Sensor data, locations, risk "
    "scores, cascade estimates, simulations and resource decisions "
    "are illustrative. The models have not been validated for "
    "real-world emergency response. Do not use prototype outputs "
    "as the sole basis for emergency decisions."
)
