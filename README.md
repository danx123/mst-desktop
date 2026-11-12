# 🛰️ MST Desktop — Macan Satellite Tracker

Desktop edition of MST, written in **Python + PySide6**. Real-time satellite tracking, an offline-first TLE catalog, 48-hour pass prediction and a 2D sky radar.

---

## Screenshot

<img width="1365" height="732" alt="Screenshot 2026-11-12 151137" src="https://github.com/user-attachments/assets/1c0dffcb-fa7a-456a-bcb0-f8f9e86e8a7b" />

<img width="1365" height="734" alt="Screenshot 2026-11-12 151150" src="https://github.com/user-attachments/assets/48be276e-1c08-4205-87fc-ceb1d2e308ad" />

<img width="1365" height="734" alt="Screenshot 2026-11-12 151157" src="https://github.com/user-attachments/assets/dcc390da-4651-4f83-8107-d6eff67d4362" />

<img width="1365" height="733" alt="Screenshot 2026-11-12 151205" src="https://github.com/user-attachments/assets/784ed237-66a3-4a12-8170-89df106ad3fb" />

## Run

```bash
pip install -r requirements.txt
python main.py          # or: python -m mst
```

Requires Python 3.10+ and PySide6 6.6+.

## Features

- **Orbit Map** — live position (1 s refresh), 90-minute ground track, coverage footprint, observer pin, wheel-zoom / drag-pan (double-click resets), telemetry window
- **Catalog** — 15 bundled satellites (SATRIA-1, Telkom, BRISAT, Nusantara Satu, LAPAN, ISS, Tiangong, NOAA, Meteor, Starlink, Hubble), search, category filters, favorites; handles thousands of rows after a Starlink sync
- **CelesTrak sync** — Stations, Weather, Starlink, Geostationary; favorites are preserved
- **Pass prediction** — next 48 h, AOS / peak / LOS with azimuths, quality rating; AOS/LOS and peak are refined to about a second
- **Sky Radar** — polar az/el plot, steering hints and target lock, plus the predicted pass path ("Buka Radar" on a pass card)
- **Observer location** — Indonesian presets or manual coordinates (saved between runs)

Desktops have no compass sensor, so the radar uses a **heading slider** instead of the phone's rotation sensor. Keyboard: `Ctrl+1..4` switches pages.

## Project layout

```
main.py                     entry point
mst/
  app.py                    bootstrap (DB + controller + window)
  core/                     pure Python, no Qt — easy to test
    constants.py  models.py  tle.py  geo.py  propagator.py  passes.py
  data/                     persistence and network
    database.py  default_satellites.py  celestrak.py  repository.py
  ui/
    theme.py  formatting.py  controller.py  main_window.py
    pages/      map_page  catalog_page  passes_page  radar_page
    widgets/    world_map  radar  telemetry  common  mapdata
    dialogs/    location_dialog  detail_dialog
tests/test_core.py
```

Layers only depend downward: `ui → data → core`. `AppController` owns all state and exposes Qt signals; pages never talk to each other directly, they just observe the controller. Pass prediction and CelesTrak sync run on a thread pool, so the UI never blocks.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Accuracy notes

- The propagator is Keplerian motion with J2 secular perturbations — **not full SGP4**. There is no drag or deep-space modelling, so error grows as a TLE ages.
- The **bundled TLEs are a static snapshot from early 2024**. Sync with CelesTrak before relying on positions; the map shows a warning when a TLE is older than 7 days.
- The world map is a simplified outline for orientation only.

## Build a standalone executable (Nuitka)

```bash
python -m nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable main.py
```

Data lives in the per-user app-data folder (`MacanAngkasa/MST`), and settings in `QSettings`.
