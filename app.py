#!/usr/bin/env python3
"""
FieldLog — UAM Deployment Entry (Streamlit app)
Cross-platform (Windows / Mac / Linux).

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import re
import subprocess
import sys
import urllib.parse
from datetime import datetime, date, time as dtime
from pathlib import Path

import streamlit as st
import csv_manager


# ── Folder picker (Qt) ─────────────────────────────────────────────────────────

def _pick_folder(initialdir: str = None) -> str | None:
    """
    Open a native Qt folder dialog in a subprocess.
    Streamlit's script runs in a worker thread — Qt must run in a main thread,
    so we spawn a fresh process that uses QFileDialog and prints the result.
    Returns the selected path string, or None if cancelled.
    """
    _helper = Path(__file__).parent / "_folder_picker.py"
    _start  = str(initialdir) if initialdir else str(Path.home())
    result = subprocess.run(
        [sys.executable, str(_helper), _start],
        capture_output=True, text=True, timeout=300,
    )
    return result.stdout.strip() or None

# ── Constants ──────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_ARCGIS_EXPERIENCE_URL = (
    "https://experience.arcgis.com/experience/f703e7a448e44768b11f7ca209b61edd"
)

# Optional: requests for ArcGIS geocoding
try:
    import requests as _req
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# Optional: folium map
try:
    import folium
    from streamlit_folium import st_folium
    _HAS_FOLIUM = True
except ImportError:
    _HAS_FOLIUM = False

_MAP_DEFAULT = [43.6532, -79.3832]  # Toronto

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="FieldLog", page_icon="📋", layout="wide")

_BASE_CSS = """
<style>
/* ── Hide Streamlit chrome ── */
#MainMenu { display: none !important; }
footer { display: none !important; }
/* Make the top header bar invisible but keep it in the layout so the
   sidebar collapse/expand button (which lives inside it) still works. */
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { visibility: hidden; }
/* Sidebar open/close buttons must always be visible and clickable.
   In Streamlit 1.41+ the expand button (shown when sidebar is collapsed)
   has data-testid="stExpandSidebarButton"; the collapse button (inside the
   sidebar) has data-testid="stSidebarCollapseButton". */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapseButton"] * {
    visibility: visible !important;
    pointer-events: auto !important;
}

/* ── Title accent bar ── */
.main h1 {
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #2563eb;
    margin-bottom: 1rem;
}

/* ── Form border ── */
[data-testid="stForm"] {
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 12px;
    padding: 1.25rem 1.5rem !important;
}

/* ── Rounded buttons ── */
button[kind="primary"],
button[kind="primaryFormSubmit"],
button[kind="secondary"],
button[kind="tertiary"] {
    border-radius: 8px !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; }
</style>
"""

_DARK_CSS = """
<style>
/* === FIELDLOG DARK THEME === */
html, body, .stApp { background-color: #18181b !important; color: #f4f4f5 !important; }
.main .block-container { background-color: #18181b !important; }
/* Sidebar — target the element itself and its content area only.
   Do NOT target > div:first-child: that is the collapse-button container
   and painting it dark makes the toggle icon invisible. */
section[data-testid="stSidebar"] { background-color: #111113 !important; }
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] { background-color: #111113 !important; }

/* Typography */
h1, h2, h3, h4, h5, h6 { color: #f4f4f5 !important; }
p, label, small { color: #f4f4f5; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color: #f4f4f5 !important; }
.stCaption, [data-testid="stCaptionContainer"] * { color: #a1a1aa !important; }

/* Inputs */
.stTextInput input, .stTextArea textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input {
    background-color: #27272a !important;
    color: #f4f4f5 !important;
    border-color: #3f3f46 !important;
}
/* Select / Dropdown */
[data-baseweb="select"] > div:first-child {
    background-color: #27272a !important;
    border-color: #3f3f46 !important;
    color: #f4f4f5 !important;
}
[data-baseweb="popover"] > div,
[data-baseweb="menu"] { background-color: #27272a !important; border-color: #3f3f46 !important; }
[role="option"] { background-color: #27272a !important; color: #f4f4f5 !important; }
[role="option"]:hover,
[aria-selected="true"][role="option"] { background-color: #3f3f46 !important; }

/* Form */
[data-testid="stForm"] { background-color: #1e1e22 !important; border-color: #3f3f46 !important; }

/* Divider */
hr, [data-testid="stDivider"] > div { background-color: #3f3f46 !important; }

/* Tabs */
[data-baseweb="tab-list"] { background-color: #27272a !important; }
[data-baseweb="tab"] { color: #a1a1aa !important; }
[aria-selected="true"][data-baseweb="tab"] { color: #f4f4f5 !important; }

/* Alert boxes */
[data-testid="stAlert"] { background-color: #1e1e22 !important; }

/* Dataframe */
[data-testid="stDataFrame"] *,
.stDataFrame { background-color: #27272a !important; color: #f4f4f5 !important; }
[data-testid="stDataFrame"] th { background-color: #3f3f46 !important; }

/* Secondary / download buttons */
button[kind="secondary"],
[data-testid="baseButton-secondary"],
[data-testid="stDownloadButton"] > button {
    background-color: #27272a !important;
    border-color: #3f3f46 !important;
    color: #f4f4f5 !important;
}
button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover,
[data-testid="stDownloadButton"] > button:hover {
    background-color: #3f3f46 !important;
}

/* Checkboxes / radio labels */
.stCheckbox label, .stRadio label,
[data-testid="stCheckbox"] span,
[data-testid="stRadio"] span { color: #f4f4f5 !important; }

/* Sidebar widget labels */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p { color: #f4f4f5 !important; }

/* Info widget */
[data-testid="stInfo"] { background-color: #1e3a5f !important; }
[data-testid="stSuccess"] { background-color: #14532d !important; }
[data-testid="stWarning"] { background-color: #451a03 !important; }
[data-testid="stError"] { background-color: #450a0a !important; }

/* Links */
a { color: #60a5fa !important; }

/* Scrollbar */
::-webkit-scrollbar-track { background: #18181b; }
::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }

/* ── Sidebar toggle — always visible even in dark mode ── */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapseButton"] * {
    visibility: visible !important;
    pointer-events: auto !important;
}
[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"] button {
    background-color: #3f3f46 !important;
    border: 1px solid #71717a !important;
    color: #f4f4f5 !important;
}
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stSidebarCollapseButton"] svg { fill: #f4f4f5 !important; }
</style>
"""

st.markdown(_BASE_CSS, unsafe_allow_html=True)
if st.session_state.get("webapp_theme", "light") == "dark":
    st.markdown(_DARK_CSS, unsafe_allow_html=True)

st.title("📋 FieldLog — UAM Deployment Entry")


# ── ArcGIS Geocoding helpers ───────────────────────────────────────────────────
_GC = "https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer"


def _gc_params(extra: dict) -> dict:
    p = {"f": "json", **extra}
    tok = st.session_state.get("arcgis_token", "").strip()
    if tok:
        p["token"] = tok
    return p


def geocode_address(query: str, max_results: int = 5) -> list:
    if not _HAS_REQUESTS:
        return []
    try:
        r = _req.get(
            f"{_GC}/findAddressCandidates",
            params=_gc_params({"SingleLine": query,
                               "maxLocations": max_results,
                               "outFields": "Place_addr"}),
            timeout=6,
        )
        r.raise_for_status()
        return r.json().get("candidates", [])
    except Exception:
        return []


def reverse_geocode(lat: float, lon: float) -> str:
    if not _HAS_REQUESTS:
        return ""
    try:
        r = _req.get(
            f"{_GC}/reverseGeocode",
            params=_gc_params({"location": f"{lon},{lat}"}),
            timeout=6,
        )
        r.raise_for_status()
        return r.json().get("address", {}).get("LongLabel", "")
    except Exception:
        return ""


def parse_arcgis_link(url: str):
    """Extract (lat, lon) from ArcGIS web-map URL patterns."""
    m = re.search(r"[?&]center=([-+]?\d+\.?\d*),([-+]?\d+\.?\d*)", url)
    if m:
        try:
            lon, lat = float(m.group(1)), float(m.group(2))
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                return lat, lon
        except ValueError:
            pass
    m = re.search(r"marker=([-+]?\d+\.?\d*);([-+]?\d+\.?\d*)", url)
    if m:
        try:
            lon, lat = float(m.group(1)), float(m.group(2))
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                return lat, lon
        except ValueError:
            pass
    return None, None


# ── Session state defaults ─────────────────────────────────────────────────────

def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


_ss("webapp_theme",       "light")
_ss("confirm_clear_all",  False)
_ss("attempt_num",        1)
_ss("last_project",       "")
_ss("gc_results",         [])
_ss("arcgis_token",       "")
# ── Form field state (pre-populated by Load Entry) ─────────────────────────────
_ss("form_project_code",  "")
_ss("form_task_number",   1)
_ss("form_client",        "")
_ss("form_address",       "")
_ss("form_description",   "")
_ss("form_lat",           "")
_ss("form_lon",           "")
_ss("form_arcgis_link",   "")
_ss("form_directory",     "")
_ss("form_asset_id",      "")
_ss("form_asset_desig",   "")
_ss("form_asset_type",        "Manhole")
_ss("form_asset_type_other",  "")
_ss("form_platform_other",    "")
_ss("form_quality_other",     "")
_ss("form_platform",      "ROGER")
_ss("form_entry_point",   "")
_ss("form_exit_point",    "")
_ss("form_pipe_length",   "")
_ss("form_quality",       "1 - Excellent")
_ss("form_observation",   "")
_ss("form_comments",      "")
_ss("form_lidar",         False)
_ss("form_csv_chk",       True)
_ss("form_cam",           True)
_ss("form_ptz",           False)


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    # ── Appearance toggle ─────────────────────────────────────────────────────
    _is_dark = st.session_state.get("webapp_theme", "light") == "dark"
    if st.button(
        "☀  Light Mode" if _is_dark else "🌙  Dark Mode",
        use_container_width=True,
    ):
        st.session_state.webapp_theme = "light" if _is_dark else "dark"
        st.rerun()

    st.markdown("---")
    st.header("Project")
    existing = csv_manager.list_existing_projects()

    if existing:
        options      = ["— new project —"] + existing
        choice       = st.selectbox("Existing projects", options)
        default_code = "" if choice == "— new project —" else choice
    else:
        default_code = ""

    st.markdown("---")
    st.subheader("Storage")
    st.caption(f"`{csv_manager.BASE_STORAGE}`")

    if st.button("📁 Change Folder", use_container_width=True):
        try:
            folder = _pick_folder(initialdir=csv_manager.BASE_STORAGE)
            if folder:
                csv_manager.set_storage_path(folder)
                st.success(f"Storage: `{folder}`")
                st.rerun()
        except Exception as ex:
            st.error(f"Folder picker error: {ex}")

    st.markdown("---")
    st.subheader("Danger Zone")
    if not st.session_state.confirm_clear_all:
        if st.button("🗑 Clear All Projects", use_container_width=True):
            st.session_state.confirm_clear_all = True
            st.rerun()
    else:
        st.warning("⚠ This will permanently delete **all** project data!")
        _ca_col1, _ca_col2 = st.columns(2)
        with _ca_col1:
            if st.button("✓ Yes, delete all", use_container_width=True, type="primary"):
                _msg = csv_manager.clear_all_projects()
                st.session_state.confirm_clear_all = False
                st.session_state.last_project      = ""
                st.session_state.form_project_code = ""
                st.error(_msg)
                st.rerun()
        with _ca_col2:
            if st.button("✕ Cancel", use_container_width=True):
                st.session_state.confirm_clear_all = False
                st.rerun()

    st.markdown("---")
    st.subheader("ArcGIS")
    st.session_state.arcgis_token = st.text_input(
        "API Token (optional)",
        value=st.session_state.arcgis_token,
        type="password",
        help=(
            "ArcGIS Developer API token — unlocks higher geocoding rate limits. "
            "Leave blank for free-tier use."
        ),
    )
    if not _HAS_REQUESTS:
        st.warning("`requests` not installed — geocoding disabled.")


# ── Project Code (top-level — drives auto-fill, form, and CSV view) ────────────

# Seed from sidebar selection if the field is currently empty
if default_code and not st.session_state.form_project_code:
    st.session_state.form_project_code = default_code

_pc_col, _ = st.columns([2, 3])
with _pc_col:
    _pc_val = st.text_input(
        "Project Code *",
        value=st.session_state.form_project_code,
        placeholder="e.g. PROJ-001",
        key="_top_project_code_input",
    )
st.session_state.form_project_code = _pc_val.strip()

st.divider()


# ── Auto-fill Attempt # ────────────────────────────────────────────────────────

st.subheader("Auto-fill Attempt #")
auto_col1, auto_col2 = st.columns([3, 1])
with auto_col1:
    auto_task = st.number_input(
        "Task Number", min_value=1, step=1, value=1, key="auto_task"
    )
with auto_col2:
    st.write("")
    st.write("")
    if st.button("Auto-fill", use_container_width=True):
        _pc = st.session_state.form_project_code
        if _pc:
            try:
                n = csv_manager.next_run_number(int(auto_task), _pc)
                st.session_state.attempt_num = n
                st.success(f"Attempt # → {n}")
            except Exception as e:
                st.error(f"Could not calculate: {e}")
        else:
            st.warning("Enter a Project Code at the top first.")

st.divider()


# ── Location Lookup ────────────────────────────────────────────────────────────

_gc_label = "Location Lookup" + (
    "" if _HAS_REQUESTS else "  *(install `requests` to enable)*"
)
st.subheader(_gc_label)

gc1, gc2, gc3 = st.columns([4, 1, 1])
with gc1:
    gc_query = st.text_input(
        "Search address  or  paste an ArcGIS link to extract coordinates",
        placeholder="123 Main St, Toronto  —or—  https://arcgis.com/…?center=-79.38,43.65",
        key="gc_query",
    )
with gc2:
    st.write("")
    st.write("")
    search_clicked = st.button(
        "🔍 Search", use_container_width=True, disabled=not _HAS_REQUESTS
    )
with gc3:
    st.write("")
    st.write("")
    if st.button("✕ Clear", use_container_width=True):
        st.session_state.gc_results = []
        st.rerun()

if search_clicked and gc_query.strip():
    q = gc_query.strip()
    if q.startswith("http"):
        lat_v, lon_v = parse_arcgis_link(q)
        if lat_v is not None:
            addr = reverse_geocode(lat_v, lon_v)
            st.session_state.form_lat = f"{lat_v:.6f}"
            st.session_state.form_lon = f"{lon_v:.6f}"
            if addr:
                st.session_state.form_address = addr
            st.success(
                f"Extracted — Lat: {lat_v:.6f}, Lon: {lon_v:.6f}"
                + (f"  |  {addr}" if addr else "")
            )
        else:
            st.warning("Could not extract coordinates from this link.")
    else:
        with st.spinner("Querying ArcGIS World Geocoder…"):
            results = geocode_address(q)
        if results:
            st.session_state.gc_results = results
        else:
            st.warning("No results found.  Try a more specific address.")

if st.session_state.gc_results:
    labels = [
        f"{r.get('address', '')}  (score {r.get('score', 0):.0f})"
        for r in st.session_state.gc_results
    ]
    chosen_label = st.selectbox("Select the correct address", labels, key="gc_sel")
    idx = labels.index(chosen_label)
    chosen = st.session_state.gc_results[idx]

    apply_col, _ = st.columns([1, 3])
    with apply_col:
        if st.button("✓ Apply to form", type="primary"):
            loc  = chosen.get("location", {})
            addr = chosen.get("address", "")
            st.session_state.form_address = addr
            st.session_state.form_lat = (
                f"{loc['y']:.6f}" if loc.get("y") is not None else ""
            )
            st.session_state.form_lon = (
                f"{loc['x']:.6f}" if loc.get("x") is not None else ""
            )
            st.session_state.gc_results = []
            st.rerun()

st.divider()


# ── Location Map ───────────────────────────────────────────────────────────────

_map_tab, = st.tabs(["📍 Location Map"])

with _map_tab:
    if _HAS_FOLIUM:
        try:
            _mlat = float(st.session_state.form_lat) if st.session_state.form_lat else None
            _mlon = float(st.session_state.form_lon) if st.session_state.form_lon else None
        except ValueError:
            _mlat = _mlon = None

        _center = [_mlat, _mlon] if (_mlat is not None and _mlon is not None) else _MAP_DEFAULT
        _zoom   = 15 if (_mlat is not None) else 5
        _m = folium.Map(location=_center, zoom_start=_zoom, control_scale=True)

        if _mlat is not None and _mlon is not None:
            folium.Marker(
                location=[_mlat, _mlon],
                tooltip=st.session_state.form_address or f"{_mlat:.6f}, {_mlon:.6f}",
                popup=folium.Popup(
                    st.session_state.form_address or "Current location", max_width=200
                ),
                icon=folium.Icon(color="blue", icon="map-marker", prefix="fa"),
            ).add_to(_m)

        _map_result = st_folium(
            _m,
            use_container_width=True,
            height=580,
            key="location_map",
            returned_objects=["last_clicked"],
        )

        _lc = (_map_result or {}).get("last_clicked")
        if _lc:
            _click_lat = round(_lc["lat"], 6)
            _click_lon = round(_lc["lng"], 6)
            _info_col, _btn_col = st.columns([3, 1])
            with _info_col:
                st.info(f"Clicked: {_click_lat}, {_click_lon}")
            with _btn_col:
                if st.button("✓ Use This Location", use_container_width=True, type="primary"):
                    with st.spinner("Looking up address…"):
                        _addr = reverse_geocode(_click_lat, _click_lon)
                    st.session_state.form_lat = str(_click_lat)
                    st.session_state.form_lon = str(_click_lon)
                    if _addr:
                        st.session_state.form_address = _addr
                    st.rerun()
        else:
            st.caption("Click anywhere on the map to set the location.")
    else:
        st.info(
            "Map not available. Install the missing packages and restart:\n\n"
            "    pip install folium streamlit-folium"
        )

st.divider()


# ── ArcGIS Structure Link ──────────────────────────────────────────────────────

st.subheader("ArcGIS Structure Link")

_arc_btn_col, _arc_input_col = st.columns([1, 3])

with _arc_btn_col:
    st.link_button(
        "🌐 Open ArcGIS",
        _ARCGIS_EXPERIENCE_URL,
        use_container_width=True,
        type="primary",
    )
    st.caption("Opens in your default browser. Navigate to a structure, then copy the URL from the address bar and paste it below.")

with _arc_input_col:
    def _on_url_paste():
        _u = st.session_state.get("arcgis_url_paste", "").strip()
        if _u and "arcgis.com" in _u:
            st.session_state.form_arcgis_link = _u

    st.text_input(
        "Paste structure URL here:",
        key="arcgis_url_paste",
        on_change=_on_url_paste,
        placeholder=_ARCGIS_EXPERIENCE_URL + "#data_s=…",
    )
    if st.session_state.form_arcgis_link:
        st.success(f"✓ Captured: `{st.session_state.form_arcgis_link}`")

st.divider()


# ── Load Entry for Editing ─────────────────────────────────────────────────────

_ASSET_TYPES = ["Manhole", "Tunnel", "Culvert", "Other"]
_PLATFORMS   = ["ROGER", "MANITOR", "Other"]
_QUALITIES   = ["1 - Excellent", "2 - Good", "3 - Fair", "4 - Poor", "5 - Failed", "Other"]

_lpc = st.session_state.form_project_code
if _lpc:
    _lrows = csv_manager._load_project(_lpc)
    if _lrows:
        st.subheader("Load Entry for Editing")
        _llabels = ["— select an entry —"] + [
            f"Task {r['task_number']}  ·  Attempt {r['attempt_number']}"
            + (f"  ·  {r['asset_id']}" if r.get("asset_id") else "")
            + (f"  ·  {r.get('date_start','')}" if r.get("date_start") else "")
            for r in _lrows
        ]
        _lsel_col, _lbtn_col = st.columns([4, 1])
        with _lsel_col:
            _lsel = st.selectbox("Select an existing entry to load into the form below:",
                                 _llabels, key="load_entry_sel")
        with _lbtn_col:
            st.write("")
            st.write("")
            if st.button("📥 Load", use_container_width=True) \
                    and _lsel != "— select an entry —":
                _lr = _lrows[_llabels.index(_lsel) - 1]
                _at = _lr.get("asset_type", "Manhole")
                _pl = _lr.get("deployment_platform", "ROGER")
                _ql = _lr.get("run_quality", "1")
                _dt = _lr.get("data_type", "")
                st.session_state.form_task_number  = int(_lr.get("task_number", 1))
                st.session_state.attempt_num       = int(_lr.get("attempt_number", 1))
                st.session_state.form_client       = _lr.get("client", "")
                st.session_state.form_address      = _lr.get("address", "")
                st.session_state.form_description  = _lr.get("project_description", "")
                st.session_state.form_lat          = _lr.get("location_lat", "")
                st.session_state.form_lon          = _lr.get("location_lon", "")
                st.session_state.form_arcgis_link  = _lr.get("arcgis_link", "")
                st.session_state.form_directory    = _lr.get("directory_name", "")
                st.session_state.form_asset_id     = _lr.get("asset_id", "")
                st.session_state.form_asset_desig  = _lr.get("asset_designation", "")
                if _at in _ASSET_TYPES:
                    st.session_state.form_asset_type       = _at
                    st.session_state.form_asset_type_other = ""
                else:
                    st.session_state.form_asset_type       = "Other"
                    st.session_state.form_asset_type_other = _at
                if _pl in _PLATFORMS:
                    st.session_state.form_platform       = _pl
                    st.session_state.form_platform_other = ""
                else:
                    st.session_state.form_platform       = "Other"
                    st.session_state.form_platform_other = _pl
                st.session_state.form_entry_point  = _lr.get("entry_point", "")
                st.session_state.form_exit_point   = _lr.get("exit_point", "")
                st.session_state.form_pipe_length  = _lr.get("pipe_length", "").replace(" ft", "").strip()
                _ql_match = next((q for q in _QUALITIES if q.startswith(_ql)), None)
                if _ql_match:
                    st.session_state.form_quality       = _ql_match
                    st.session_state.form_quality_other = ""
                else:
                    st.session_state.form_quality       = "Other"
                    st.session_state.form_quality_other = _ql
                st.session_state.form_observation  = _lr.get("observation_summary", "")
                st.session_state.form_comments     = _lr.get("other_comments", "")
                st.session_state.form_lidar        = "Lidar"      in _dt
                st.session_state.form_csv_chk      = "CSV"        in _dt
                st.session_state.form_cam          = "360_Camera" in _dt
                st.session_state.form_ptz          = "PTZ"        in _dt
                st.rerun()
        st.divider()
else:
    _ASSET_TYPES = ["Manhole", "Tunnel", "Culvert", "Other"]
    _PLATFORMS   = ["ROGER", "MANITOR", "Other"]
    _QUALITIES   = ["1 - Excellent", "2 - Good", "3 - Fair", "4 - Poor", "5 - Failed", "Other"]


# ── Entry Form ─────────────────────────────────────────────────────────────────

with st.container():

    # ── Project ───────────────────────────────────────────────────────────────
    st.subheader("Project")
    project_code = st.session_state.form_project_code
    st.info(f"Project Code: **{project_code}**" if project_code else "⚠ No project code entered above.")

    client = st.text_input("Client", key="form_client", placeholder="e.g. City Council")

    addr_col, desc_col = st.columns(2)
    with addr_col:
        address = st.text_input("Address", key="form_address", placeholder="e.g. 123 Main St")
    with desc_col:
        description = st.text_input("Description", key="form_description",
                                    placeholder="Brief project description")

    lat_col, lon_col, arc_col = st.columns(3)
    with lat_col:
        lat = st.text_input("Latitude", key="form_lat", placeholder="e.g. 43.6532")
    with lon_col:
        lon = st.text_input("Longitude", key="form_lon", placeholder="e.g. -79.3832")
    with arc_col:
        arcgis_link = st.text_input("ArcGIS Link", key="form_arcgis_link",
                                    placeholder="Paste from ArcGIS section above")

    # ── Run ───────────────────────────────────────────────────────────────────
    st.subheader("Run")
    task_col, attempt_col, dir_col = st.columns([1, 1, 2])
    with task_col:
        task_number = st.number_input("Task Number *", min_value=1, step=1,
                                      key="form_task_number")
    with attempt_col:
        attempt_number = st.number_input(
            "Attempt # *", min_value=1, step=1,
            value=st.session_state.attempt_num,
            help="Use Auto-fill above, or load an existing entry above to edit it.",
        )
    with dir_col:
        # Auto-fill from BASE_STORAGE when the field is blank and a project code is set
        if project_code and not st.session_state.form_directory:
            try:
                st.session_state.form_directory = str(
                    Path(csv_manager.project_csv_path(project_code)).parent
                )
            except Exception:
                pass
        directory = st.text_input(
            "Directory", key="form_directory",
            placeholder="/path/to/data/<project>_YYYYMMDD",
            help="Where the run data is stored on disk.",
        )

    # ── Sensors / Data Types ──────────────────────────────────────────────────
    st.write("**Sensors / Data Types**")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        lidar_cb = st.checkbox("Lidar",       key="form_lidar")
    with s2:
        csv_cb   = st.checkbox("CSV",         key="form_csv_chk")
    with s3:
        cam_cb   = st.checkbox("360 Camera",  key="form_cam")
    with s4:
        ptz_cb   = st.checkbox("PTZ",         key="form_ptz")

    # ── Asset ─────────────────────────────────────────────────────────────────
    st.subheader("Asset")
    aid_col, adesig_col, atype_col, plat_col = st.columns(4)
    with aid_col:
        asset_id = st.text_input("Asset ID", key="form_asset_id", placeholder="e.g. MH-042")
    with adesig_col:
        asset_desig = st.text_input("Asset Designation", key="form_asset_desig",
                                    placeholder="e.g. Section A North")
    with atype_col:
        st.selectbox("Asset Type", _ASSET_TYPES, key="form_asset_type")
        if st.session_state.form_asset_type == "Other":
            asset_type = st.text_input(
                "Specify asset type", key="form_asset_type_other",
                placeholder="e.g. Bridge, Vault, Chamber…",
                label_visibility="collapsed",
            ).strip() or "Other"
        else:
            asset_type = st.session_state.form_asset_type
    with plat_col:
        st.selectbox("Platform", _PLATFORMS, key="form_platform")
        if st.session_state.form_platform == "Other":
            platform = st.text_input(
                "Specify platform", key="form_platform_other",
                placeholder="e.g. Custom Robot…",
                label_visibility="collapsed",
            ).strip() or "Other"
        else:
            platform = st.session_state.form_platform

    # ── Inspection ────────────────────────────────────────────────────────────
    st.subheader("Inspection")
    entry_col, exit_col, pipe_col = st.columns(3)
    with entry_col:
        entry_point = st.text_input("Entry Point", key="form_entry_point",
                                    placeholder="e.g. MH-001")
    with exit_col:
        if platform == "MANITOR":
            st.text_input("Exit Point", value=entry_point, disabled=True,
                          help="Mirrors Entry Point for MANITOR.")
            exit_point = entry_point
        else:
            exit_point = st.text_input("Exit Point", key="form_exit_point",
                                       placeholder="e.g. MH-002")
    with pipe_col:
        pipe_length = st.text_input("Pipe Length (ft)", key="form_pipe_length",
                                    placeholder="e.g. 45.5")

    ds_col1, ds_col2, de_col1, de_col2 = st.columns(4)
    with ds_col1:
        date_start_d = st.date_input("Date Start",  value=date.today(), key="form_date_start_d")
    with ds_col2:
        date_start_t = st.time_input("Time Start",  value=dtime(0, 0, 0), step=60,
                                     key="form_date_start_t")
    with de_col1:
        date_stop_d  = st.date_input("Date Stop",   value=date.today(), key="form_date_stop_d")
    with de_col2:
        date_stop_t  = st.time_input("Time Stop",   value=dtime(0, 0, 0), step=60,
                                     key="form_date_stop_t")

    qual_col, _ = st.columns([1, 2])
    with qual_col:
        st.selectbox("Run Quality", _QUALITIES, key="form_quality")
        if st.session_state.form_quality == "Other":
            quality = st.text_input(
                "Specify quality", key="form_quality_other",
                placeholder="e.g. N/A, Partial…",
                label_visibility="collapsed",
            ).strip() or "Other"
        else:
            quality = st.session_state.form_quality

    obs_col, cmt_col = st.columns(2)
    with obs_col:
        observation = st.text_area(
            "Observation Summary", key="form_observation",
            placeholder="e.g. root intrusion at 12 m, sediment build-up near exit...",
            height=120,
        )
    with cmt_col:
        comments = st.text_area(
            "Other Comments", key="form_comments",
            placeholder="e.g. cable snagged, crew notes, weather conditions...",
            height=120,
        )

    _sbtn_col, _ubtn_col = st.columns(2)
    with _sbtn_col:
        submitted = st.button(
            "➕ Submit New Entry", use_container_width=True, type="primary"
        )
    with _ubtn_col:
        update_clicked = st.button(
            "✏ Update Entry", use_container_width=True
        )


# ── Handle submission ──────────────────────────────────────────────────────────

if submitted or update_clicked:
    if not project_code:
        st.error("Project Code is required — enter it at the top of the page.")
    else:
        _task_str = str(int(task_number))
        _run_str  = str(int(attempt_number))

        # For Update: verify the entry already exists — refuse to create new rows
        _proceed = True
        if update_clicked:
            _rows = csv_manager._load_project(project_code)
            _match = any(
                r["task_number"] == _task_str and r["attempt_number"] == _run_str
                for r in _rows
            )
            if not _match:
                st.error(
                    f"No entry found for Task {_task_str}, Attempt {_run_str}. "
                    f"Use **➕ Submit New Entry** to create it first."
                )
                _proceed = False

        if _proceed:
            sensors = []
            if lidar_cb: sensors.append("Lidar")
            if csv_cb:   sensors.append("CSV")
            if cam_cb:   sensors.append("360_Camera")
            if ptz_cb:   sensors.append("PTZ")
            data_type = "&".join(sensors)

            fmt = "%m-%d-%Y %H:%M:%S"
            date_start_str = datetime.combine(date_start_d, date_start_t).strftime(fmt)
            date_stop_str  = datetime.combine(date_stop_d,  date_stop_t).strftime(fmt)

            meta = {
                "client":              client.strip(),
                "address":             address.strip(),
                "project_description": description.strip(),
                "location_lat":        lat.strip(),
                "location_lon":        lon.strip(),
                "arcgis_link":         arcgis_link.strip(),
            }
            run_data = {
                "task_number":         _task_str,
                "attempt_number":      _run_str,
                "directory_name":      directory.strip(),
                "data_type":           data_type,
                "asset_id":            asset_id.strip(),
                "asset_designation":   asset_desig.strip(),
                "asset_type":          asset_type,
                "deployment_platform": platform,
                "entry_point":         entry_point.strip(),
                "exit_point":          exit_point.strip(),
                "pipe_length":         f"{pipe_length.strip()} ft" if pipe_length.strip() else "",
                "date_start":          date_start_str,
                "date_stop":           date_stop_str,
                "run_quality":         quality.split(" - ")[0],
                "observation_summary": observation.strip(),
                "other_comments":      comments.strip(),
            }

            try:
                csv_manager.setup_project(project_code, meta)
                msg = csv_manager.append_or_update_project_run(
                    project_code, meta, run_data
                )
                action = "Updated" if update_clicked else "Saved"
                st.success(f"{action} — {msg}")
                st.session_state.last_project = project_code
                if submitted:
                    st.session_state.attempt_num = int(attempt_number) + 1
                # Update: keep the form pointing at the same entry (no increment)
                elif update_clicked:
                    st.session_state.attempt_num = int(attempt_number)
            except Exception as e:
                st.error(f"Error: {e}")


# ── Current CSV table + download ───────────────────────────────────────────────

st.divider()
st.subheader("Current CSV Entries")

view_project = (
    st.session_state.last_project
    or st.session_state.form_project_code
    or (existing[0] if existing else "")
)

if view_project:
    rows = csv_manager._load_project(view_project)
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No entries yet for this project.")

    csv_bytes = csv_manager.get_project_csv_bytes(view_project)
    folder    = csv_manager.get_project_folder(view_project)

    dl_col, save_col, del_col, clr_col = st.columns(4)
    with dl_col:
        st.download_button(
            label=f"⬇ Download jobs.csv  ({view_project})",
            data=csv_bytes,
            file_name=f"{folder}_jobs.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with save_col:
        if st.button("💾 Save to Folder…", use_container_width=True):
            try:
                _helper = Path(__file__).parent / "_folder_picker.py"
                _res = subprocess.run(
                    [sys.executable, str(_helper), "--save",
                     str(csv_manager.BASE_STORAGE), f"{folder}_jobs.csv"],
                    capture_output=True, text=True, timeout=300,
                )
                save_path = _res.stdout.strip()
                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(csv_bytes)
                    st.success(f"Saved to `{save_path}`")
            except Exception as ex:
                st.error(f"Could not save: {ex}")
    with del_col:
        if st.button("🗑 Delete Last Entry", use_container_width=True):
            msg = csv_manager.delete_last_entry(view_project)
            st.warning(msg)
            st.rerun()
    with clr_col:
        if st.button("⚠ Clear All Entries", use_container_width=True):
            msg = csv_manager.clear_project_csv(view_project)
            st.error(msg)
            st.rerun()
else:
    st.info("Enter a Project Code and submit an entry to see the table here.")
