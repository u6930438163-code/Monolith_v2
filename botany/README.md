# Botanika Kosmiczna i Biotechnologia

Prototype of the persistent crop and research registry for Monolith_v2.

- Vessel/station habitat records and species tracking.
- Crop lifecycle from seed to harvest, with manual/simulated/sensor-verified provenance.
- Environmental observations: temperature, humidity, light, pH.
- Research batch catalog for plant-derived compounds. **Research-only**: no clinical claims, dosage recommendations, or automated medicine production.
- SQLite backend; no connected physical sensors, actuators, or LibreChat UI yet.

Usage:
```bash
python3 -m botany.garden --db garden.sqlite3 plant "Ship Aurora" "Hydroponics A" "Ocimum basilicum"
python3 -m botany.garden --db garden.sqlite3 list
python3 -m unittest tests.test_botany -v
```

Future modules: growth timelines and safe alerts; sensor adapters with verifiable data provenance; nutrient/irrigation controllers with independent safety interlocks; image diagnosis with Ollama Vision; batch traceability and laboratory results; fleet habitat dashboard; role-based access through the Monolith permissions engine.

Do not treat simulated observations as physical measurements. Accelerated growth must be validated experimentally for each plant species.
