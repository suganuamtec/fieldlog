#!/usr/bin/env python3
"""
FieldLog — Maintenance & Servicing
ROGER ROV maintenance checklists and servicing log.
Content sourced from Section 6 of ROGER_Deployment_Checklist.docx.
"""

import sys
from pathlib import Path
from datetime import date

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import _fieldlog_common as _common

st.set_page_config(page_title="Maintenance & Servicing — FieldLog", page_icon="🔧", layout="wide")
_common.apply_theme()
_common.login_gate()
_common.sidebar_nav()

# ── Session state helpers ──────────────────────────────────────────────────────

def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


# ── Checklist item definitions ─────────────────────────────────────────────────

_DAILY = [
    ("mt_day_1", "Confirm all connectors and caps are tight and fully seated"),
    ("mt_day_2", "Inspect all cables for cuts or signs of damage"),
    ("mt_day_3", "Check for any degradation to lifting points and hardware"),
    ("mt_day_4", "Check for water ingress inside sensor housings and light lenses"),
    ("mt_day_5", "Inspect camera domes for scuff marks or scratches"),
    ("mt_day_6", "Confirm all seals are intact and screws are tight"),
]

_WEEKLY = [
    ("mt_wk_1", "Check hub motors for any signs of leaks"),
    ("mt_wk_2", "Replace O-rings if worn or damaged and apply sealant as required"),
]

_AS_REQUIRED = [
    ("mt_ar_1", "Calibrate hub motors and check for leaks"),
    ("mt_ar_2", "Clean encoder PCB with contact cleaner"),
    ("mt_ar_3", "Seal and replace O-rings as required"),
    ("mt_ar_4", "Check tyre pressure on wheels"),
    ("mt_ar_5", "Patch tether using potting compound as required"),
]

# Initialise all checkbox keys
for _key, _ in _DAILY + _WEEKLY + _AS_REQUIRED:
    _ss(_key, False)

# Maintenance log entries stored in session
_ss("mt_log_entries", [])
_ss("mt_log_date",       str(date.today()))
_ss("mt_log_tech",       "")
_ss("mt_log_type",       "Daily")
_ss("mt_log_notes",      "")


# ── Render helpers ─────────────────────────────────────────────────────────────

def checklist_section(title, items, reset_key):
    checked = sum(1 for k, _ in items if st.session_state.get(k, False))
    total   = len(items)
    pct     = checked / total if total else 0
    st.progress(pct, text=f"{checked}/{total} completed")

    for key, label in items:
        st.checkbox(label, key=key)

    st.write("")
    if st.button(f"🔄 Reset {title}", key=f"rst_{reset_key}", use_container_width=False):
        for k, _ in items:
            st.session_state[k] = False
        st.rerun()


# ── Page header ────────────────────────────────────────────────────────────────

st.title("🔧 ROGER ROV — Maintenance & Servicing")
st.caption("Section 6 of the ROGER Deployment Checklist. Track routine maintenance and log servicing work.")

st.divider()


# ── Maintenance checklists ─────────────────────────────────────────────────────

tab_daily, tab_weekly, tab_ar = st.tabs(["📅 Daily Maintenance", "🗓 Weekly Maintenance", "🔩 As Required"])

with tab_daily:
    st.subheader("Daily Maintenance")
    st.caption("Complete at the start or end of each deployment day.")
    checklist_section("Daily Maintenance", _DAILY, "daily")

with tab_weekly:
    st.subheader("Weekly Maintenance")
    st.caption("Complete at least once per week during active deployment periods.")
    checklist_section("Weekly Maintenance", _WEEKLY, "weekly")

with tab_ar:
    st.subheader("As Required")
    st.caption("Complete when conditions warrant or issues are identified.")
    checklist_section("As Required", _AS_REQUIRED, "ar")


# ── Maintenance log ────────────────────────────────────────────────────────────

st.divider()
st.subheader("Maintenance Log")
st.caption("Record servicing activities and notes for this session.")

log_col1, log_col2, log_col3 = st.columns([1, 1, 1])
with log_col1:
    st.text_input("Date", key="mt_log_date", placeholder="YYYY-MM-DD")
with log_col2:
    st.text_input("Technician", key="mt_log_tech", placeholder="Name")
with log_col3:
    st.selectbox(
        "Maintenance Type",
        ["Daily", "Weekly", "As Required", "Repair", "Inspection", "Other"],
        key="mt_log_type",
    )

st.text_area(
    "Work Performed / Notes",
    key="mt_log_notes",
    placeholder="Describe the maintenance or repairs performed, parts replaced, observations, etc.",
    height=120,
)

_add_col, _ = st.columns([1, 4])
with _add_col:
    if st.button("➕ Add Log Entry", type="primary", use_container_width=True):
        entry = {
            "Date":       st.session_state.mt_log_date,
            "Technician": st.session_state.mt_log_tech,
            "Type":       st.session_state.mt_log_type,
            "Notes":      st.session_state.mt_log_notes,
        }
        if entry["Notes"].strip():
            st.session_state.mt_log_entries.append(entry)
            st.session_state.mt_log_notes = ""
            st.success("Log entry added.")
            st.rerun()
        else:
            st.warning("Add notes before logging the entry.")

# Display log entries
if st.session_state.mt_log_entries:
    st.markdown("**Log entries this session:**")
    st.dataframe(
        st.session_state.mt_log_entries,
        use_container_width=True,
    )

    # Download as CSV
    import io, csv as _csv
    _buf = io.StringIO()
    _writer = _csv.DictWriter(_buf, fieldnames=["Date", "Technician", "Type", "Notes"])
    _writer.writeheader()
    _writer.writerows(st.session_state.mt_log_entries)
    _csv_bytes = _buf.getvalue().encode()

    _dl_col, _clr_col, _ = st.columns([1, 1, 3])
    with _dl_col:
        st.download_button(
            label="⬇ Download Log CSV",
            data=_csv_bytes,
            file_name=f"maintenance_log_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with _clr_col:
        if st.button("🗑 Clear Log", use_container_width=True):
            st.session_state.mt_log_entries = []
            st.rerun()
else:
    st.info("No log entries yet. Add an entry above.")
