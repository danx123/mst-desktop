# 🛰️ MST Desktop — Macan Satellite Tracker

Desktop edition of MST, written in **Python + PySide6**. Real-time satellite tracking with full **SGP4/SDP4** propagation, an offline-first TLE catalog, 48-hour pass prediction and a 2D sky radar.
---

<img width="1024" height="1536" alt="MST_ Jelajahi Langit Bersama Macan Angkasa" src="https://github.com/user-attachments/assets/bc7abfc8-5414-42ff-b4c9-7597da1dc6cf" />

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

Requires Python 3.10+, PySide6 6.6+ and sgp4 2.22+.

## Features

- **Orbit Map** — live position (1 s refresh), 90-minute ground track, coverage footprint, observer pin, wheel-zoom / drag-pan (double-click resets), telemetry window
- **Full SGP4/SDP4 propagation** — near-Earth (SGP4) and deep-space (SDP4: lunar-solar perturbations, 12 h / 24 h resonances for GPS, Molniya and geostationary satellites) are selected automatically from the orbital period
- **Catalog** — 15 bundled satellites (SATRIA-1, Telkom, BRISAT, Nusantara Satu, LAPAN, ISS, Tiangong, NOAA, Meteor, Starlink, Hubble), search, category filters, favorites; handles thousands of rows after a Starlink sync
- **CelesTrak sync** — Stations, Weather, Starlink, Geostationary; favorites are preserved
- **Pass prediction** — next 48 h, AOS / peak / LOS with azimuths, quality rating; AOS/LOS and peak are refined to about a second
- **Sky Radar** — polar az/el plot, steering hints and target lock, plus the predicted pass path ("Buka Radar" on a pass card)
- **Observer location** — Indonesian presets or manual coordinates (saved between runs)

Desktops have no compass sensor, so the radar uses a **heading slider** instead of the phone's rotation sensor.

### Keyboard shortcuts

| Key | Action |
|---|---|
| `F11` | Enter / toggle fullscreen |
| `Esc` | Leave fullscreen |
| `Ctrl+1` … `Ctrl+4` | Orbit Map / Catalog / Passes / Sky Radar |

The sidebar also has a fullscreen button.

### Languages

The UI is available in **English** and **Bahasa Indonesia**. Pick one in the sidebar (bottom-left); it switches instantly, keeps your current page and window state, and is remembered between runs. On first launch the language follows your system locale (Indonesian locale → Indonesian, anything else → English).

To add a language, add a column to every entry in `mst/i18n.py`; `tests/test_i18n.py` verifies that no key is missing and that placeholders match.

## Project layout

```
main.py                     entry point
satellite.ico               application icon (next to main.py)
tools/make_icon.py          regenerates satellite.ico (multi-size)
mst/
  app.py                    bootstrap (DB, language, icon, controller, window)
  i18n.py                   all UI strings (Indonesian + English)
  resources.py              finds bundled files such as satellite.ico
  core/                     pure Python, no Qt — easy to test
    constants.py  models.py  tle.py  geo.py  propagator.py  passes.py
  data/                     persistence and network
    database.py  default_satellites.py  celestrak.py  repository.py
  ui/
    theme.py  formatting.py  controller.py  main_window.py  window_host.py
    pages/      map_page  catalog_page  passes_page  radar_page
    widgets/    world_map  radar  telemetry  common  mapdata
    dialogs/    location_dialog  detail_dialog
tests/test_core.py  tests/test_sgp4.py  tests/test_i18n.py
```

Layers only depend downward: `ui → data → core`. `AppController` owns all state and exposes Qt signals; pages never talk to each other directly, they just observe the controller. Pass prediction and CelesTrak sync run on a thread pool, so the UI never blocks.

## Tests

```bash
python -m unittest discover -s tests -v
```

`tests/test_sgp4.py` checks the propagator against the Vallado/SGP4 verification vectors (satellite 00005) and the near-Earth/deep-space model selection.

## Accuracy notes

- Propagation uses the **`sgp4` package** (full SGP4 + SDP4, WGS-72 constants as TLEs are fitted with). Output is in the TEME frame and is rotated to ECEF with GMST; polar motion and nutation are ignored (far below TLE accuracy).
- A fresh TLE is typically good to about 1 km at epoch, and the error grows by roughly 1–3 km per day for low orbits. Keep the catalog synced.
- If SGP4 cannot propagate a TLE (for example a decayed object or a very old element set), the map shows no position instead of a wrong one.
- The **bundled TLEs are a static snapshot from early 2024**. Sync with CelesTrak before relying on positions; the map shows a warning when a TLE is older than 7 days.
- The world map is a simplified outline for orientation only.

## Build a standalone executable (Nuitka)

```bash
python -m nuitka --standalone --enable-plugin=pyside6 --include-package=sgp4 --windows-console-mode=disable ^
  --windows-icon-from-ico=satellite.ico --include-data-files=satellite.ico=satellite.ico main.py
```

`--include-package=sgp4` makes sure the SGP4 package (including its compiled C++ extension, when installed) is bundled. `--windows-icon-from-ico` sets the `.exe` icon; `--include-data-files` ships `satellite.ico` so the window and taskbar icon also work at runtime. (Use `\` instead of `^` for line continuation on Linux/macOS.)

Data lives in the per-user app-data folder (`MacanAngkasa/MST`), and settings in `QSettings`.
