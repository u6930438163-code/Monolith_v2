# Solar System Fleet Map

Interactive orbital overview is currently prototyped in ChatGPT. This module will be integrated into the Monolith_v2 fleet dashboard.

## Data contract

A ship position report should include:
- ship_id, display_name
- coordinate_frame (e.g. heliocentric_ecliptic_J2000)
- x_au, y_au, z_au
- observed_at (UTC)
- source (telemetry, imported, simulation)
- mission, operational_status
- optional velocity vector and uncertainty

Never present illustrative positions as real-time telemetry. A live deployment requires an authenticated position feed and a clearly displayed age of last update.

## Planned functions

- Zoom and pan, orbit layers, ship selection, filters
- Switch between simulated data and verified telemetry
- Show ship details, mission ETA only when trajectories and time data exist
- Historical timeline and position playback
- Permissions and access logs for fleet telemetry
