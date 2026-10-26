# PRAVAAH

**An AI-Powered Environmental Monitoring and Disaster Risk Prevention Network**

PRAVAAH is a prototype concept for environmental-risk monitoring and disaster decision support. The presentation describes a workflow that analyzes environmental signals, detects risk precursors and monitoring blind zones, explores cascading impacts, simulates flood spread, compares response strategies, and stores disaster memory.

## Current prototype status

The project presentation states that the current prototype uses **simulated readings** because controlled hazard testing and suitable real-world data were difficult to obtain. It should not be described as a deployed live-sensor system or as a validated real-world forecasting service.

## Technology stack

The presentation lists:
- Python
- Streamlit
- Pandas and NumPy
- Scikit-learn
- NetworkX
- Folium
- Plotly
- JSON / SQLite-ready architecture for disaster memory

## Repository structure

The repository currently shows these existing items:
- `app.py`
- `data/`
- `models/`
- `simulation/`
- `utils/`

Additional submission-support files in this package:
- `TECHNICAL_DESIGN.md` — high-level design based on the project presentation
- `requirements.txt` — package list inferred from the presentation; verify against imports in `app.py`
- `data/sample_environmental_readings.csv` — illustrative synthetic data, not measured field data
- `tests/test_sample_data.py` — basic checks for the included sample CSV
- `LICENSE` — MIT License; keep this only if the team chooses to release its code under MIT

## Setup

Use Python 3.10 or later if compatible with the code in this repository.

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application from the repository root:

   ```bash
   streamlit run app.py
   ```

If the app fails because a package is missing or a version is incompatible, compare `requirements.txt` with the actual imports and runtime needs in `app.py` and the project folders.

## Sample data

The CSV in `data/` contains **synthetic example readings only**. It is included to document the expected general shape of environmental input data. Confirm that column names and units match the actual app before using it in the prototype.

## Limitations and responsible use

- Sample values are synthetic and are not a source of real-time warnings.
- Outputs require testing and validation before any operational use.
- Human authorities must verify alerts and make emergency decisions.
- Sensor failure, incomplete coverage, communication outages, changing road access, false alarms, and limited historical data are known risks described in the project presentation.

## References

- National Disaster Management Authority: https://ndma.gov.in/
- India Meteorological Department: https://mausam.imd.gov.in/
- Central Pollution Control Board: https://cpcb.nic.in/
- ISRO Bhuvan: https://bhuvan.nrsc.gov.in/
- Scikit-learn: https://scikit-learn.org/
- NetworkX: https://networkx.org/
