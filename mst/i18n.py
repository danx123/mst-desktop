"""Tiny dependency-free i18n layer (Indonesian + English).

Every UI string lives here as ``key: (indonesian, english)``. Use ``tr(key)``
or ``tr(key, name=value)`` for ``str.format`` placeholders. Keeping both
languages side by side makes a missing translation impossible to overlook
(see tests/test_i18n.py).
"""
from __future__ import annotations

LANGUAGES: dict[str, str] = {"id": "Bahasa Indonesia", "en": "English"}
_INDEX = {"id": 0, "en": 1}
_current = "id"


def set_language(code: str) -> None:
    global _current
    if code in LANGUAGES:
        _current = code


def current_language() -> str:
    return _current


def detect_language(locale_name: str) -> str:
    """Pick a default from a system locale such as ``id_ID`` or ``en_US``."""
    return "id" if locale_name.lower().startswith(("id", "in_")) else "en"


def tr(key: str, **params: object) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry[_INDEX[_current]]
    return text.format(**params) if params else text


STRINGS: dict[str, tuple[str, str]] = {
    # ---- navigation / shell -------------------------------------------------
    "nav.map": ("◍  Peta Orbit", "◍  Orbit Map"),
    "nav.catalog": ("☰  Katalog", "☰  Catalog"),
    "nav.passes": ("◷  Prediksi", "◷  Passes"),
    "nav.radar": ("◎  Sky Radar", "◎  Sky Radar"),
    "side.observer": ("PENGAMAT", "OBSERVER"),
    "side.utc": ("WAKTU UTC", "UTC TIME"),
    "side.language": ("BAHASA", "LANGUAGE"),
    "side.fullscreen": ("⛶  Layar Penuh (F11)", "⛶  Fullscreen (F11)"),
    "side.exit_fullscreen": ("⛶  Keluar Layar Penuh (Esc)", "⛶  Exit Fullscreen (Esc)"),
    # ---- map page -----------------------------------------------------------
    "map.pick": ("PILIH SATELIT", "SELECT A SATELLITE"),
    "map.detail": ("ⓘ  Detail", "ⓘ  Details"),
    "map.visible": ("TERLIHAT", "VISIBLE"),
    "map.hidden": ("OCCULT", "HIDDEN"),
    "map.tle_warn": (
        "⚠ TLE berusia {days:.0f} hari — sinkronkan CelesTrak (menu Katalog) untuk posisi akurat",
        "⚠ TLE is {days:.0f} days old — sync CelesTrak (Catalog menu) for accurate positions",
    ),
    "map.subsat": ("POSISI SUBSATELIT", "SUB-SATELLITE POINT"),
    "map.loading": ("Memuat koordinat real-time...", "Loading real-time coordinates..."),
    "map.elaz": ("ELEVASI / AZIMUTH", "ELEVATION / AZIMUTH"),
    # ---- detail dialog ------------------------------------------------------
    "detail.title": ("Detail Telemetri", "Telemetry Details"),
    "detail.vis_yes": ("SEDANG MELINTAS (TERLIHAT DI LANGIT)", "PASSING OVERHEAD (VISIBLE IN THE SKY)"),
    "detail.vis_no": ("DI BAWAH CAKRAWALA (TIDAK TERLIHAT)", "BELOW THE HORIZON (NOT VISIBLE)"),
    "detail.latlon": ("LINTANG / BUJUR", "LATITUDE / LONGITUDE"),
    "detail.alt": ("KETINGGIAN ORBIT", "ORBIT ALTITUDE"),
    "detail.speed": ("KECEPATAN", "VELOCITY"),
    "detail.period": ("PERIODE ORBIT", "ORBITAL PERIOD"),
    "detail.azel": ("AZIMUTH / ELEVASI", "AZIMUTH / ELEVATION"),
    "detail.range": ("JARAK KE PENGAMAT", "RANGE TO OBSERVER"),
    "detail.epoch": ("EPOCH TLE", "TLE EPOCH"),
    "detail.age": ("USIA TLE", "TLE AGE"),
    "detail.minutes": ("{v:.1f} menit", "{v:.1f} min"),
    "detail.days": ("{v:.1f} hari", "{v:.1f} days"),
    "detail.radar": ("Sky Radar", "Sky Radar"),
    "detail.passes": ("Jadwal Lintasan", "Pass Schedule"),
    # ---- catalog page -------------------------------------------------------
    "catalog.title": ("Katalog Satelit", "Satellite Catalog"),
    "catalog.count": ("{n} Satelit Tersedia (Offline Ready)", "{n} Satellites Available (Offline Ready)"),
    "catalog.search": ("Cari nama satelit atau NORAD ID...", "Search satellite name or NORAD ID..."),
    "catalog.col_fav": ("★", "★"),
    "catalog.col_name": ("Nama Satelit", "Satellite Name"),
    "catalog.col_norad": ("NORAD ID", "NORAD ID"),
    "catalog.col_category": ("Kategori", "Category"),
    "catalog.fav_tip": ("Klik untuk tandai / hapus favorit", "Click to add / remove favorite"),
    "catalog.hint": (
        "Klik ★ untuk favorit • klik dua kali untuk melacak",
        "Click ★ to favorite • double-click to track",
    ),
    "catalog.track": ("Lacak Satelit Terpilih", "Track Selected Satellite"),
    "cat.all": ("Semua", "All"),
    "cat.favorites": ("Favorit", "Favorites"),
    "cat.indonesia": ("Indonesia", "Indonesia"),
    "cat.stations": ("Stasiun", "Stations"),
    "cat.weather": ("Cuaca", "Weather"),
    "cat.starlink": ("Starlink", "Starlink"),
    "cat.geo": ("Geostasioner", "Geostationary"),
    # ---- CelesTrak sync -----------------------------------------------------
    "sync.stations": ("Sinkronkan Stasiun Luar Angkasa (ISS)", "Sync Space Stations (ISS)"),
    "sync.weather": ("Sinkronkan Satelit Cuaca (Weather)", "Sync Weather Satellites"),
    "sync.starlink": ("Sinkronkan Starlink", "Sync Starlink"),
    "sync.geo": ("Sinkronkan Geostasioner (GEO)", "Sync Geostationary (GEO)"),
    "sync.downloading": (
        "Mengunduh data TLE {category} dari CelesTrak...",
        "Downloading {category} TLE data from CelesTrak...",
    ),
    "sync.success": ("Berhasil memperbarui {count} satelit {category}", "Updated {count} {category} satellites"),
    "sync.failed": ("Gagal: {message}", "Failed: {message}"),
    "err.connection": ("Koneksi terputus", "Connection lost"),
    "err.http": ("HTTP error {code}: {reason}", "HTTP error {code}: {reason}"),
    "err.empty": ("Respons kosong", "Empty response"),
    "err.no_tle": ("Tidak ada data TLE valid ({snippet})", "No valid TLE data ({snippet})"),
    # ---- passes page --------------------------------------------------------
    "passes.title": ("Prediksi Lintasan", "Pass Prediction"),
    "passes.subtitle": (
        "Jadwal Satelit Melintas (48 Jam Ke Depan)",
        "Satellite Flyover Schedule (Next 48 Hours)",
    ),
    "passes.recalc": ("⟳  Hitung Ulang", "⟳  Recalculate"),
    "passes.observer": ("LOKASI PENGAMAT", "OBSERVER LOCATION"),
    "passes.change": ("📍  Ubah Lokasi", "📍  Change Location"),
    "passes.pick": ("Pilih Satelit", "Select a Satellite"),
    "passes.count": ("{n} Lintasan Terprediksi", "{n} Passes Predicted"),
    "passes.calculating": ("Menghitung propagasi orbit...", "Calculating orbit propagation..."),
    "passes.need_sat": (
        "Pilih satelit dari Katalog terlebih dahulu.",
        "Select a satellite from the Catalog first.",
    ),
    "passes.none": (
        "Tidak Ada Lintasan Terdeteksi\n"
        "Tidak ada lintasan dengan elevasi puncak ≥ 10° dalam 48 jam ke depan "
        "(satelit geostasioner yang selalu terlihat atau selalu di bawah cakrawala tidak punya lintasan).",
        "No Passes Detected\n"
        "No pass with a peak elevation of at least 10° in the next 48 hours "
        "(geostationary satellites that are always above or always below the horizon have no passes).",
    ),
    "pass.excellent": ("SANGAT BAGUS", "EXCELLENT"),
    "pass.fair": ("CUKUP TINGGI", "FAIRLY HIGH"),
    "pass.low": ("RENDAH", "LOW"),
    "pass.aos": ("MUNCUL (AOS)", "RISES (AOS)"),
    "pass.peak": ("PUNCAK ELEVASI", "PEAK ELEVATION"),
    "pass.los": ("HILANG (LOS)", "SETS (LOS)"),
    "pass.duration": ("⏱  Durasi: {d}", "⏱  Duration: {d}"),
    "pass.open_radar": ("◎  Buka Radar", "◎  Open Radar"),
    "fmt.duration": ("{m}m {s}d", "{m}m {s}s"),
    # ---- radar page ---------------------------------------------------------
    "radar.title": ("Sky Radar 2D", "2D Sky Radar"),
    "radar.mode_north": ("Mode North-Up (Utara Tetap)", "North-Up Mode (Fixed North)"),
    "radar.mode_heading": ("Mode Arah Hadap: {deg}°", "Heading Mode: {deg}°"),
    "radar.clear_path": ("✕  Hapus Jalur Lintasan", "✕  Clear Pass Path"),
    "radar.loading": ("Memuat...", "Loading..."),
    "radar.heading": ("ARAH HADAP", "HEADING"),
    "radar.reset": ("Reset ke Utara", "Reset to North"),
    "radar.t_az": ("AZIMUTH TARGET", "TARGET AZIMUTH"),
    "radar.t_el": ("ELEVASI TARGET", "TARGET ELEVATION"),
    "radar.t_range": ("JARAK", "RANGE"),
    "radar.pick": ("Pilih satelit dari Katalog", "Select a satellite from the Catalog"),
    "radar.locked": ("🎯 TARGET ACQUIRED! TEPAT DI DEPAN", "🎯 TARGET ACQUIRED! RIGHT AHEAD"),
    "radar.turn_right": ("PUTAR KE KANAN {deg}°", "TURN RIGHT {deg}°"),
    "radar.turn_left": ("PUTAR KE KIRI {deg}°", "TURN LEFT {deg}°"),
    "radar.below": ("SATELIT BERADA DI BAWAH CAKRAWALA", "SATELLITE IS BELOW THE HORIZON"),
    "radar.heading_value": ("{deg}° ({name})", "{deg}° ({name})"),
    "radar.card_n": ("U", "N"),
    "radar.card_e": ("T", "E"),
    "radar.card_s": ("S", "S"),
    "radar.card_w": ("B", "W"),
    "compass.0": ("Utara", "North"),
    "compass.1": ("Timur Laut", "Northeast"),
    "compass.2": ("Timur", "East"),
    "compass.3": ("Tenggara", "Southeast"),
    "compass.4": ("Selatan", "South"),
    "compass.5": ("Barat Daya", "Southwest"),
    "compass.6": ("Barat", "West"),
    "compass.7": ("Barat Laut", "Northwest"),
    # ---- location dialog ----------------------------------------------------
    "loc.title": ("Pilih Lokasi Pengamat", "Choose Observer Location"),
    "loc.presets": ("Kota Preset Indonesia:", "Indonesian City Presets:"),
    "loc.manual": ("Atau Masukkan Koordinat Manual:", "Or Enter Coordinates Manually:"),
    "loc.name": ("Nama", "Name"),
    "loc.lat": ("Lintang (Lat)", "Latitude"),
    "loc.lon": ("Bujur (Lon)", "Longitude"),
    "loc.alt": ("Ketinggian (m)", "Altitude (m)"),
    "loc.cancel": ("Batal", "Cancel"),
    "loc.apply": ("Terapkan", "Apply"),
    "loc.manual_name": ("Koordinat Manual", "Manual Coordinates"),
    "loc.custom": ("Kustom", "Custom"),
    "loc.jakarta": ("Jakarta (Monas)", "Jakarta (Monas)"),
    "loc.surabaya": ("Surabaya (Jawa Timur)", "Surabaya (East Java)"),
    "loc.bandung": ("Bandung (Observatorium Bosscha)", "Bandung (Bosscha Observatory)"),
    "loc.medan": ("Medan (Sumatera Utara)", "Medan (North Sumatra)"),
    "loc.makassar": ("Makassar (Sulawesi Selatan)", "Makassar (South Sulawesi)"),
    "loc.denpasar": ("Denpasar (Bali)", "Denpasar (Bali)"),
    "loc.ikn": ("IKN Nusantara (Kalimantan)", "Nusantara Capital (Kalimantan)"),
}
