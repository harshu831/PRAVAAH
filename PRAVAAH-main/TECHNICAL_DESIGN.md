# PRAVAAH — Technical Design

## 1. Purpose

PRAVAAH is a prototype environmental monitoring and disaster decision-support concept. Its goal is to turn environmental signals into risk-aware recommendations rather than presenting isolated readings alone.

## 2. Inputs

The presentation identifies these environmental signals:
- Rainfall
- Soil moisture
- River level
- Temperature
- Humidity

The current prototype presentation states that it uses simulated readings. The sample CSV included with this package is synthetic and illustrative.

## 3. High-level processing flow

1. Data collection
2. Risk calculation
3. Risk-trend and precursor detection
4. Uncertainty and blind-zone analysis
5. Cascading-impact prediction
6. Digital Twin simulation
7. Resource allocation
8. Counterfactual comparison
9. Failure-aware recommendation
10. Disaster memory

This is the workflow described in the project presentation. Exact algorithms and implementation details should be documented from the source code before claiming that every stage is fully implemented.

## 4. Main capabilities described in the presentation

- Monitor rainfall, soil moisture, river level, temperature and humidity.
- Detect possible environmental risk before a hazard reaches a severe stage.
- Estimate data confidence and flag sensor blind zones.
- Explore cascading consequences such as flooding, road blockage, village isolation and rescue delay.
- Simulate flood propagation through a Digital Twin.
- Prioritize locations using exposure, vulnerability, accessibility and rescue demand.
- Compare possible response strategies, including earlier evacuation and additional boat deployment.
- Store disaster memory for future learning.

## 5. Technology stack

The presentation lists Python, Streamlit, Pandas, NumPy, Scikit-learn, NetworkX, Folium, Plotly, and JSON with a SQLite-ready architecture.

`requirements.txt` is a starting dependency list inferred from that presentation. It must be checked against the actual imports and code.

## 6. Failure handling and limitations

The presentation identifies these risks:
- Sensor failure and communication outages
- Uneven sensor coverage
- False alarms and limited rescue resources
- Changing road conditions
- Lack of historical data

Mitigations described in the presentation include sensor-health monitoring, confidence scoring, degraded or isolated operating modes, coverage and uncertainty warnings, human verification, multi-signal confirmation, priority scoring, scenario comparison, and dynamic accessibility updates.

The current prototype should not be presented as operationally validated. The presentation proposes future work including historical-dataset testing, pilot sensor deployment, district-level decision support and multi-hazard expansion.

## 7. Validation plan

Before real-world use:
- Validate input formats and missing-value handling.
- Test risk outputs against documented scenarios and historical data.
- Test behavior when sensors or communication are unavailable.
- Review false positives and false negatives with qualified disaster-management stakeholders.
- Verify map, accessibility, and resource-allocation assumptions.
- Keep human review in the decision loop.

## 8. Intended beneficiaries

- Disaster authorities
- Environmental agencies
- District administrations
- Vulnerable rural communities
- Emergency and rescue teams

## 9. Source references

- NDMA: https://ndma.gov.in/
- IMD: https://mausam.imd.gov.in/
- CPCB: https://cpcb.nic.in/
- ISRO Bhuvan: https://bhuvan.nrsc.gov.in/
- Scikit-learn documentation: https://scikit-learn.org/
- NetworkX documentation: https://networkx.org/
