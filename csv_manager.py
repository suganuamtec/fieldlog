#!/usr/bin/env python3
"""
CSV Manager — standalone (no ROS/Docker dependencies)
Manages per-project inspection log CSVs stored under ./data/
"""

import csv
import os
from datetime import datetime
from typing import List

# Storage root — relative to this file so it works on Windows, Mac, Linux
BASE_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

PROJECT_HEADERS = [
    "project_code",
    "client",
    "address",
    "project_description",
    "location_lat",
    "location_lon",
    "arcgis_link",
    "task_number",
    "attempt_number",
    "directory_name",
    "data_type",
    "asset_id",
    "asset_designation",
    "asset_type",
    "deployment_platform",
    "entry_point",
    "exit_point",
    "pipe_length",
    "date_start",
    "date_stop",
    "run_quality",
    "observation_summary",
    "other_comments",
]


# ── Folder helpers ─────────────────────────────────────────────────────────────

def _project_folder(project_code: str) -> str:
    """
    Return the dated folder name for project_code.
    Format: <project_code>_YYYYMMDD

    If a folder with that prefix already exists in BASE_STORAGE, the most
    recent one (lexicographic sort on the date suffix) is reused so that
    reopening a project doesn't create a duplicate.
    """
    today = f"{project_code}_{datetime.now().strftime('%Y%m%d')}"
    prefix = project_code + "_"
    try:
        if os.path.isdir(BASE_STORAGE):
            candidates = [
                e for e in os.listdir(BASE_STORAGE)
                if e.startswith(prefix)
                and os.path.isdir(os.path.join(BASE_STORAGE, e))
            ]
            if candidates:
                candidates.sort()
                return candidates[-1]
    except OSError:
        pass
    return today


def set_storage_path(path: str) -> None:
    """Change the storage root directory at runtime (e.g. from the UI folder picker)."""
    global BASE_STORAGE
    BASE_STORAGE = path


def get_project_folder(project_code: str) -> str:
    return _project_folder(project_code)


def project_csv_path(project_code: str) -> str:
    return os.path.join(BASE_STORAGE, _project_folder(project_code), "jobs.csv")


def list_existing_projects() -> List[str]:
    """Return bare project codes (without date suffix) found in ./data/."""
    if not os.path.isdir(BASE_STORAGE):
        return []
    codes = set()
    try:
        for entry in os.listdir(BASE_STORAGE):
            path = os.path.join(BASE_STORAGE, entry)
            if not os.path.isdir(path):
                continue
            # Folder name is <code>_YYYYMMDD — strip the last _YYYYMMDD
            parts = entry.rsplit("_", 1)
            if len(parts) == 2 and len(parts[1]) == 8 and parts[1].isdigit():
                codes.add(parts[0])
    except OSError:
        pass
    return sorted(codes)


# ── Per-project CSV I/O ────────────────────────────────────────────────────────

def _load_project(project_code: str) -> List[dict]:
    path = project_csv_path(project_code)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return [{h: row.get(h, "") for h in PROJECT_HEADERS} for row in rows]


def _write_project(project_code: str, rows: List[dict]):
    path = project_csv_path(project_code)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PROJECT_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in PROJECT_HEADERS})


# ── Public API ─────────────────────────────────────────────────────────────────

def setup_project(project_code: str, meta: dict) -> str:
    """
    Create the project folder (<project_code>_YYYYMMDD) and initialise jobs.csv.
    If the folder already exists it is left untouched.
    meta keys: client, address, project_description, location_lat, location_lon,
               arcgis_link, asset_type, deployment_platform
    """
    folder_name = _project_folder(project_code)
    folder_path = os.path.join(BASE_STORAGE, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    path = project_csv_path(project_code)
    if os.path.exists(path):
        return f"Project '{project_code}' opened — {folder_name}"

    _write_project(project_code, [])
    return f"Project '{project_code}' created — {folder_name}"


def append_or_update_project_run(project_code: str,
                                  meta: dict, run_data: dict) -> str:
    """
    Add or update a run row in the per-project jobs.csv.
    Rows are matched by task_number + attempt_number.
      - Match found  → UPDATE all run_data fields; fill blanks from meta.
      - No match     → APPEND a new row using meta + run_data.
    Returns a human-readable status string.
    """
    rows     = _load_project(project_code)
    task_str = str(run_data.get("task_number", ""))
    run_str  = str(run_data.get("attempt_number", ""))

    for row in rows:
        if row["task_number"] == task_str and row["attempt_number"] == run_str:
            for h in PROJECT_HEADERS:
                if h in run_data:
                    row[h] = run_data[h]
                if h in meta and not run_data.get(h):
                    row[h] = meta[h]
            _write_project(project_code, rows)
            return f"Task {task_str} run {run_str}: updated."

    new_row = {h: "" for h in PROJECT_HEADERS}
    new_row["project_code"] = project_code
    new_row.update(meta)
    new_row.update(run_data)
    rows.append(new_row)
    _write_project(project_code, rows)
    return f"Task {task_str} run {run_str}: added."


def next_run_number(task: int, project_code: str = "") -> int:
    """
    Return the next attempt number for task by scanning the project CSV.
    Returns max(attempt_number) + 1, or 1 if no rows found.
    """
    task_str = str(task)
    max_run  = 0

    if project_code:
        for row in _load_project(project_code):
            if row["task_number"] == task_str:
                try:
                    n = int(row["attempt_number"])
                    if n > max_run:
                        max_run = n
                except (ValueError, TypeError):
                    pass

    return max_run + 1


def delete_last_entry(project_code: str) -> str:
    """Remove the last row from the project CSV. Returns a status string."""
    rows = _load_project(project_code)
    if not rows:
        return "No entries to delete."
    removed = rows.pop()
    _write_project(project_code, rows)
    return (
        f"Deleted: Task {removed.get('task_number','')} "
        f"Run {removed.get('attempt_number','')}."
    )


def clear_project_csv(project_code: str) -> str:
    """Wipe all rows from the project CSV (keeps headers). Returns a status string."""
    rows = _load_project(project_code)
    if not rows:
        return "CSV is already empty."
    _write_project(project_code, [])
    return f"Cleared {len(rows)} row(s) from {project_code}."


def clear_all_projects() -> str:
    """Delete every project folder under BASE_STORAGE. Returns a status string."""
    import shutil
    if not os.path.isdir(BASE_STORAGE):
        return "No data to clear."
    count = 0
    errors = []
    for entry in os.listdir(BASE_STORAGE):
        path = os.path.join(BASE_STORAGE, entry)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                count += 1
            except Exception as e:
                errors.append(str(e))
    if errors:
        return f"Cleared {count} folder(s) — errors: {'; '.join(errors)}"
    return f"All {count} project folder(s) deleted."


def get_project_csv_bytes(project_code: str) -> bytes:
    """Return the raw bytes of the project jobs.csv for download."""
    path = project_csv_path(project_code)
    if not os.path.exists(path):
        # Return headers-only CSV if nothing saved yet
        import io
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=PROJECT_HEADERS)
        writer.writeheader()
        return buf.getvalue().encode("utf-8")
    with open(path, "rb") as f:
        return f.read()
