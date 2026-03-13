#!/usr/bin/env python3
"""
FieldLog — ROGER ROV Deployment Checklist
Interactive checklist based on ROGER_Deployment_Checklist.docx
"""

import sys
from pathlib import Path
from datetime import date

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import _fieldlog_common as _common

st.set_page_config(page_title="Deployment Checklist — FieldLog", page_icon="✅", layout="wide")
_common.apply_theme()
_common.login_gate()
_common.sidebar_nav()

# ── Session state helpers ──────────────────────────────────────────────────────

def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


# Deployment header info
_ss("dc_date",      str(date.today()))
_ss("dc_site",      "")
_ss("dc_operators", [""])   # list of operator name strings

# ── Checklist item definitions ─────────────────────────────────────────────────
# Format: (key_suffix, label, is_warning)

_S1_SHARED = [
    ("s1_sh_1", "Lift manhole lid", False),
    ("s1_sh_2", "Start generator", False),
    ("s1_sh_3", "Unload equipment from the truck", False),
    ("s1_sh_4", "Confined Space Entry (CSE) — complete entry permits and lower ROGER into manhole", False),
    ("s1_sh_5", "Co-ordinate with CSE to drop and lift equipment for ROGER setup inside the manhole", False),
]

_S1_P1_CASE = [
    ("s1_p1c_1", "Set up 2 laptops and connect to HDMI screens", False),
    ("s1_p1c_2", "Connect chargers to both laptops", False),
    ("s1_p1c_3", "Connect Ethernet cables", False),
    ("s1_p1c_4", "Connect deployment case kettle cord (mains power)", False),
    ("s1_p1c_5", "Connect controller to Surface PC", False),
    ("s1_p1c_6", "Connect wireless mouse (if required)", False),
    ("s1_p1c_7", "Connect encoder USB cable", False),
]

_S1_P1_SPOOL = [
    ("s1_p1s_1", "Connect Ethernet cable from deployment case to spool Ethernet port", False),
    ("s1_p1s_2", "Connect spool power cable", False),
    ("s1_p1s_3", "Connect spool USB cable for Icron Extender", False),
]

_S1_P1_ENCODER = [
    ("s1_p1e_1", "Connect encoder power adapter", False),
    ("s1_p1e_2", "Connect encoder USB interface cable", False),
]

_S1_P2 = [
    ("s1_p2_1", "Set up tripod and winch", False),
]

_S1_P3 = [
    ("s1_p3_1", "Unload toolboxes", False),
    ("s1_p3_2", "Set up encoder", False),
    ("s1_p3_3", "Set up power boards", False),
    ("s1_p3_4", "Safely manage and secure equipment around the site", False),
]

_S2_NETWORK = [
    ("s2_net_1", "Open ROGER UI on both surface laptops", False),
    ("s2_net_2", "Verify ROGER network link is at 1 Gbps — if showing 100 Mbps: clean connectors with contact cleaner, then restart ROGER + spool Ethernet controller power", False),
    ("s2_net_3", "Run connectivity speed test — must exceed 800 Mbps", False),
    ("s2_net_4", "Sync ROGER clock to surface", False),
]

_S2_SENSORS = [
    ("s2_sen_1", "Turn on WBIB", False),
    ("s2_sen_2", "Turn on Livox LiDAR — enable USB Direct (Livox scanner) or LiDAR USB (BLK scanner) as appropriate", False),
    ("s2_sen_3", "Turn on Sonar", False),
    ("s2_sen_4", "Confirm 360° camera is on", False),
]

_S2_SOFTWARE = [
    ("s2_sw_1", "Start Robot Agent — confirm button turns red and status mirrors on second PC", False),
    ("s2_sw_2", "Start ROGER Stack on ROGER", False),
    ("s2_sw_3", "Start Camera Stack on ROGER", False),
    ("s2_sw_4", "Once ROGER stacks are running: start Surface Stack, then UAM Studio", False),
    ("s2_sw_5", "On streaming laptop: start Surface Video Stack", False),
    ("s2_sw_6", "On Windows laptop: open Sonar Surface software and confirm sonar connection", False),
    ("s2_sw_7", "Open UAM Studio → Tools → confirm Foxglove webpage loads correctly", False),
]

_S3_PRERUN = [
    ("s3_pre_1", 'Confirm WBIB status shows "Device is Running" with all messages including BMS', False),
    ("s3_pre_2", "If WBIB is idle, use the single-service command to restart it", False),
    ("s3_pre_3", "In Job Control panel: enter project name and fill in all required parameters", False),
    ("s3_pre_4", "Position ROGER in the manhole and set encoder to zero (0)", False),
    ("s3_pre_5", "Wipe camera domes with Rain-X and confirm imagery is clear before starting the run", False),
]

_S3_START = [
    ("s3_sta_1", "START Sonar recording", False),
    ("s3_sta_2", "Start and confirm the project in Job Control — status must progress from STARTING → RUNNING", False),
]

_S3_DURING = [
    ("s3_dur_1", "Co-ordinate with team to drive ROGER and capture high-quality data", False),
    ("s3_dur_2", "Monitor image quality continuously (lens cleanliness, lighting, ROV angle)", False),
    ("s3_dur_3", "⚠ If data quality is in doubt or any risk arises — stop and consult Craig. Craig has final authority to proceed or abort.", True),
]

_S3_END = [
    ("s3_end_1", "STOP and confirm in Job Control — status must progress from STOPPING → STOPPED", False),
    ("s3_end_2", "Stop Sonar recording", False),
    ("s3_end_3", "⚠ Drive back in coordination with manhole personnel and spool operator — keep tether taut at all times to avoid driving over it. Use reverse camera to verify tether tension.", True),
]

_S4_TRANSFER = [
    ("s4_dtr_1", "Once ROGER is stationary and on the winch: open Download Panel and start data transfer", False),
]

_S4_RETRIEVAL = [
    ("s4_ret_1", "Co-ordinate team to safely move ROGER out of the manhole", False),
    ("s4_ret_2", "Wash and clean ROGER", False),
    ("s4_ret_3", "Turn off ROGER", False),
]

_S4_PACKDOWN = [
    ("s4_pck_1", "Pack down all equipment and confirm everything is secured", False),
    ("s4_pck_2", "Check site — no tools, cables, or hardware left behind", False),
    ("s4_pck_3", "Close and replace manhole lid", False),
]

_S5_TETHER = [
    ("s5_tth_1", "While spooling in and out, inspect tether for cuts or abrasions — note the chainage or mark the section for future repair if damage is found", False),
    ("s5_tth_2", "Calibrate hub motors if required", False),
]

# All checklist keys for total progress
_ALL_ITEMS = (
    _S1_SHARED + _S1_P1_CASE + _S1_P1_SPOOL + _S1_P1_ENCODER
    + _S1_P2 + _S1_P3
    + _S2_NETWORK + _S2_SENSORS + _S2_SOFTWARE
    + _S3_PRERUN + _S3_START + _S3_DURING + _S3_END
    + _S4_TRANSFER + _S4_RETRIEVAL + _S4_PACKDOWN
    + _S5_TETHER
)

# Initialise all checkbox keys
for _key, _label, _warn in _ALL_ITEMS:
    _ss(f"dc_{_key}", False)


# ── Render helpers ─────────────────────────────────────────────────────────────

def checklist_item(key, label, is_warning=False):
    """Render a single checklist row: checkbox + optional warning styling."""
    full_key = f"dc_{key}"
    if is_warning:
        st.warning(label)
        st.checkbox("Acknowledged", key=full_key)
    else:
        st.checkbox(label, key=full_key)


def subsection(title, items):
    """Render a subsection header and its checklist items."""
    st.markdown(f"**{title}**")
    for key, label, warn in items:
        checklist_item(key, label, warn)
    st.write("")


def progress_bar(items, label="Section progress"):
    checked = sum(1 for k, _, _ in items if st.session_state.get(f"dc_{k}", False))
    total   = len(items)
    pct     = checked / total if total else 0
    st.progress(pct, text=f"{label}: {checked}/{total}")


# ── Page header ────────────────────────────────────────────────────────────────

st.title("✅ ROGER ROV — Deployment Checklist")
st.caption("Complete each section in order. Items persist for this session. Use Reset to start fresh.")

col_date, col_site = st.columns(2)
with col_date:
    st.text_input("Date", key="dc_date", placeholder="YYYY-MM-DD")
with col_site:
    st.text_input("Site Location", key="dc_site", placeholder="e.g. 123 Main St, MH-042")

# ── Operators ──────────────────────────────────────────────────────────────────
st.markdown("**Operators**")
ops = st.session_state.dc_operators

for i, op in enumerate(ops):
    op_col, del_col = st.columns([6, 1])
    with op_col:
        new_val = st.text_input(
            f"Operator {i + 1}",
            value=op,
            key=f"dc_op_input_{i}",
            placeholder="Name",
            label_visibility="collapsed" if i > 0 else "visible",
        )
        ops[i] = new_val
    with del_col:
        if len(ops) > 1:
            st.write("")
            if i > 0:  # keep vertical alignment consistent
                st.write("")
            if st.button("✕", key=f"dc_op_del_{i}", help="Remove operator"):
                ops.pop(i)
                st.session_state.dc_operators = ops
                st.rerun()

_add_op_col, _ = st.columns([1, 5])
with _add_op_col:
    if st.button("➕ Add Operator", use_container_width=True):
        ops.append("")
        st.session_state.dc_operators = ops
        st.rerun()

st.divider()

# Overall progress
all_checked = sum(1 for k, _, _ in _ALL_ITEMS if st.session_state.get(f"dc_{k}", False))
all_total   = len(_ALL_ITEMS)
overall_pct = all_checked / all_total if all_total else 0
st.progress(overall_pct, text=f"Overall: {all_checked}/{all_total} items completed")

# Reset button (top)
_rst_col, _ = st.columns([1, 4])
with _rst_col:
    if st.button("🔄 Reset Entire Checklist", use_container_width=True):
        for k, _, _ in _ALL_ITEMS:
            st.session_state[f"dc_{k}"] = False
        st.session_state.dc_date      = str(date.today())
        st.session_state.dc_site      = ""
        st.session_state.dc_operators = [""]
        st.rerun()

st.divider()


# ── Section 1 ─────────────────────────────────────────────────────────────────

with st.expander("### Section 1 · Site Setup", expanded=True):
    s1_items = _S1_SHARED + _S1_P1_CASE + _S1_P1_SPOOL + _S1_P1_ENCODER + _S1_P2 + _S1_P3
    progress_bar(s1_items, "Section 1")
    st.markdown("---")

    subsection("Shared — All Personnel", _S1_SHARED)

    st.markdown("**Personnel 1 — Deployment Case**")
    st.markdown("*Deployment Case*")
    for key, label, warn in _S1_P1_CASE:
        checklist_item(key, label, warn)
    st.write("")
    st.markdown("*Spool*")
    for key, label, warn in _S1_P1_SPOOL:
        checklist_item(key, label, warn)
    st.write("")
    st.markdown("*Encoder*")
    for key, label, warn in _S1_P1_ENCODER:
        checklist_item(key, label, warn)
    st.write("")

    subsection("Personnel 2", _S1_P2)
    subsection("Personnel 3", _S1_P3)


# ── Section 2 ─────────────────────────────────────────────────────────────────

with st.expander("### Section 2 · System Startup", expanded=True):
    s2_items = _S2_NETWORK + _S2_SENSORS + _S2_SOFTWARE
    progress_bar(s2_items, "Section 2")
    st.markdown("---")

    subsection("Network & Connectivity", _S2_NETWORK)
    subsection("Sensor Power-On", _S2_SENSORS)
    subsection("Software Stack Startup", _S2_SOFTWARE)


# ── Section 3 ─────────────────────────────────────────────────────────────────

with st.expander("### Section 3 · Project Setup & Inspection Run", expanded=True):
    s3_items = _S3_PRERUN + _S3_START + _S3_DURING + _S3_END
    progress_bar(s3_items, "Section 3")
    st.markdown("---")

    subsection("Pre-Run Checks", _S3_PRERUN)
    subsection("Starting the Run", _S3_START)
    subsection("During the Run", _S3_DURING)
    subsection("Ending the Run", _S3_END)


# ── Section 4 ─────────────────────────────────────────────────────────────────

with st.expander("### Section 4 · Retrieval & Pack Down", expanded=True):
    s4_items = _S4_TRANSFER + _S4_RETRIEVAL + _S4_PACKDOWN
    progress_bar(s4_items, "Section 4")
    st.markdown("---")

    subsection("Data Transfer", _S4_TRANSFER)
    subsection("Retrieval", _S4_RETRIEVAL)
    subsection("Pack Down", _S4_PACKDOWN)


# ── Section 5 ─────────────────────────────────────────────────────────────────

with st.expander("### Section 5 · Things to Look Out For", expanded=True):
    progress_bar(_S5_TETHER, "Section 5")
    st.markdown("---")

    subsection("Tether & Mechanical", _S5_TETHER)


# ── Maintenance notice ─────────────────────────────────────────────────────────

st.divider()
st.info(
    "**Section 6 · Maintenance Schedule** has been moved to the "
    "**Maintenance & Servicing** page. Use the sidebar navigation to access it."
)

# ── Completion summary ─────────────────────────────────────────────────────────

st.divider()
if all_checked == all_total:
    st.success(f"All {all_total} items completed. Deployment checklist is done.")
else:
    remaining = all_total - all_checked
    st.info(f"{remaining} item(s) remaining.")

# Reset button (bottom)
_rst_col2, _ = st.columns([1, 4])
with _rst_col2:
    if st.button("🔄 Reset Entire Checklist", use_container_width=True, key="reset_bottom"):
        for k, _, _ in _ALL_ITEMS:
            st.session_state[f"dc_{k}"] = False
        st.session_state.dc_date      = str(date.today())
        st.session_state.dc_site      = ""
        st.session_state.dc_operators = [""]
        st.rerun()
