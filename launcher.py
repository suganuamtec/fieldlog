#!/usr/bin/env python3
"""
FieldLog — Desktop Launcher  (Qt edition)
Cross-platform: Windows / Mac / Linux
Requires PySide6  or  PyQt5  (fallback).
"""
import atexit
import os
import signal
import subprocess
import sys
import webbrowser
from pathlib import Path

PORT   = 8501
URL    = f"http://localhost:{PORT}"
HERE   = Path(__file__).parent
APP_PY = HERE / "app.py"


def _resolve_python() -> str:
    for candidate in [
        HERE / ".venv" / "bin" / "python",
        HERE / ".venv" / "Scripts" / "python.exe",
    ]:
        if candidate.exists():
            return str(candidate)
    return sys.executable


PYTHON = _resolve_python()

# ── Qt import (PySide6 preferred, PyQt5 fallback) ─────────────────────────────
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFrame, QSizePolicy, QDialog, QProgressDialog,
    )
    from PySide6.QtCore import Qt, QThread, Signal, QTimer
    from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QBrush
    _SIGNAL = Signal
except ImportError:
    try:
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QPushButton, QLabel, QFrame, QSizePolicy, QDialog, QProgressDialog,
        )
        from PyQt5.QtCore import Qt, QThread, QTimer
        from PyQt5.QtCore import pyqtSignal as _SIGNAL
        from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QBrush
        Signal = _SIGNAL
    except ImportError:
        # Neither Qt binding found — show a tkinter error (always available)
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            _r = _tk.Tk(); _r.withdraw()
            _mb.showerror(
                "FieldLog — Missing dependency",
                "PySide6 (or PyQt5) is required to run the launcher.\n\n"
                "Run in a terminal:\n"
                f"  {sys.executable} -m pip install PySide6",
            )
            _r.destroy()
        except Exception:
            pass
        sys.exit(1)

# ── Process-tree killer ────────────────────────────────────────────────────────

def _kill_proc(proc):
    if proc is None or proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
            )
        else:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


_atexit_proc: list = []


def _atexit_cleanup():
    if _atexit_proc:
        _kill_proc(_atexit_proc[0])


atexit.register(_atexit_cleanup)


def _kill_port():
    """Kill whatever is already bound to PORT."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if f":{PORT}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(
                        ["taskkill", "/F", "/PID", pid], capture_output=True
                    )
        else:
            subprocess.run(["fuser", "-k", f"{PORT}/tcp"], capture_output=True)
    except Exception:
        pass


# ── QSS themes ────────────────────────────────────────────────────────────────

_COMMON_QSS = """
* { font-size: 12pt; }
QPushButton { border-radius: 8px; font-weight: bold; padding: 13px 26px; font-size: 12pt; }
QPushButton#install_btn { padding: 11px 26px; font-size: 11pt; }
QPushButton#theme_btn   { border-radius: 6px; font-size: 17pt; padding: 4px 12px;
                           font-weight: normal; border: none; min-width: 44px; }
QLabel#title_lbl  { font-size: 20pt; font-weight: bold; }
QLabel#sub_lbl    { font-size: 9pt; }
QLabel#status_lbl { font-size: 12pt; }
QLabel#url_lbl    { font-size: 10pt; font-family: monospace; }
QFrame#card       { border-radius: 10px; border: 1px solid; }
QFrame#divider    { border: none; max-height: 1px; min-height: 1px; }
"""

_LIGHT_QSS = _COMMON_QSS + """
QMainWindow, QWidget { background-color: #f0f2f5; color: #111827; }
QFrame#card           { background-color: #ffffff; border-color: #e5e7eb; }
QLabel#status_lbl     { color: #111827; }
QLabel#url_lbl        { color: #9ca3af; }
QLabel#sub_lbl        { color: #9ca3af; }
QPushButton#start_btn { background-color: #2563eb; color: white; }
QPushButton#start_btn:hover    { background-color: #1d4ed8; }
QPushButton#start_btn:disabled { background-color: #bfdbfe; color: #93c5fd; }
QPushButton#stop_btn  { background-color: #b91c1c; color: white; }
QPushButton#stop_btn:hover     { background-color: #991b1b; }
QPushButton#browser_btn { background-color: #16a34a; color: white; }
QPushButton#browser_btn:hover    { background-color: #15803d; }
QPushButton#browser_btn:disabled { background-color: #bbf7d0; color: #6ee7b7; }
QPushButton#install_btn { background-color: #7c3aed; color: white; }
QPushButton#install_btn:hover { background-color: #6d28d9; }
QPushButton#theme_btn { color: #111827; }
QPushButton#theme_btn:hover { background-color: #e5e7eb; }
QFrame#divider        { background-color: #e5e7eb; }
"""

_DARK_QSS = _COMMON_QSS + """
QMainWindow, QWidget { background-color: #18181b; color: #f4f4f5; }
QFrame#card           { background-color: #27272a; border-color: #3f3f46; }
QLabel#status_lbl     { color: #f4f4f5; }
QLabel#url_lbl        { color: #71717a; }
QLabel#sub_lbl        { color: #71717a; }
QPushButton#start_btn { background-color: #2563eb; color: white; }
QPushButton#start_btn:hover    { background-color: #3b82f6; }
QPushButton#start_btn:disabled { background-color: #1e3a5f; color: #93c5fd; }
QPushButton#stop_btn  { background-color: #b91c1c; color: white; }
QPushButton#stop_btn:hover     { background-color: #dc2626; }
QPushButton#browser_btn { background-color: #16a34a; color: white; }
QPushButton#browser_btn:hover    { background-color: #22c55e; }
QPushButton#browser_btn:disabled { background-color: #14532d; color: #86efac; }
QPushButton#install_btn { background-color: #7c3aed; color: white; }
QPushButton#install_btn:hover { background-color: #8b5cf6; }
QPushButton#theme_btn { color: #f4f4f5; }
QPushButton#theme_btn:hover { background-color: #3f3f46; }
QFrame#divider        { background-color: #3f3f46; }
"""


def _write_streamlit_theme(dark: bool):
    """Write .streamlit/config.toml so the webapp uses the chosen theme."""
    cfg = HERE / ".streamlit" / "config.toml"
    cfg.parent.mkdir(exist_ok=True)
    base = "dark" if dark else "light"
    cfg.write_text(f'[theme]\nbase = "{base}"\n', encoding="utf-8")


# ── Server background thread ───────────────────────────────────────────────────

class _ServerThread(QThread):
    started_ok  = Signal()
    start_fail  = Signal(str)

    def __init__(self, proc_box: list):
        super().__init__()
        self._box = proc_box   # mutable [proc] shared with main window

    def run(self):
        import time
        _kill_port()
        time.sleep(0.5)
        try:
            extra = {}
            if sys.platform == "win32":
                extra["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                extra["preexec_fn"] = os.setsid

            proc = subprocess.Popen(
                [PYTHON, "-m", "streamlit", "run", str(APP_PY),
                 "--server.port", str(PORT),
                 "--server.headless", "true",
                 "--server.fileWatcherType", "none",
                 "--browser.gatherUsageStats", "false"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(HERE),
                **extra,
            )
            self._box.clear()
            self._box.append(proc)
            _atexit_proc.clear()
            _atexit_proc.append(proc)
            time.sleep(3)
            if proc.poll() is None:
                self.started_ok.emit()
            else:
                self.start_fail.emit("Process exited early")
        except Exception as exc:
            self.start_fail.emit(str(exc))


# ── Icon helper ───────────────────────────────────────────────────────────────

def _make_icon() -> QIcon:
    icon_png = HERE / "assets" / "icon.png"
    if icon_png.exists():
        return QIcon(str(icon_png))
    # Fallback: draw a blue rounded square in a QPixmap
    px = QPixmap(64, 64)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor("#2563eb")))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(2, 2, 60, 60, 12, 12)
    p.setBrush(QBrush(QColor("white")))
    for y in [18, 26, 34, 42]:
        w = 18 if y == 42 else 26
        p.drawRoundedRect(16, y, w, 4, 2, 2)
    p.end()
    return QIcon(px)


# ── Status dot ────────────────────────────────────────────────────────────────

class _Dot(QWidget):
    """16×16 colored circle."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self._color = QColor("#dc2626")

    def set_color(self, hex_color: str):
        self._color = QColor(hex_color)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(1, 1, 16, 16)


# ── Main window ───────────────────────────────────────────────────────────────

class FieldLogWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FieldLog")
        self.setFixedWidth(520)
        self.setWindowIcon(_make_icon())
        self._dark = False
        self._proc_box: list = []   # mutable [proc]
        self._server_thread = None
        self._build_ui()
        self._apply_theme()
        # Write a light base theme once so Streamlit has a clean starting point.
        # The webapp's own dark/light toggle (CSS-based) handles runtime switching.
        _write_streamlit_theme(False)
        QTimer.singleShot(200, self._start_server)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Blue accent bar
        bar = QFrame()
        bar.setFixedHeight(5)
        bar.setStyleSheet("background-color: #2563eb;")
        layout.addWidget(bar)

        inner = QWidget()
        vbox  = QVBoxLayout(inner)
        vbox.setContentsMargins(30, 22, 30, 28)
        vbox.setSpacing(18)
        layout.addWidget(inner)

        # ── Header: icon + title + theme toggle ──────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(16)

        icon_lbl = QLabel()
        px = _make_icon().pixmap(56, 56)
        icon_lbl.setPixmap(px)
        icon_lbl.setFixedSize(56, 56)
        header.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        t1 = QLabel("FieldLog")
        t1.setObjectName("title_lbl")
        t2 = QLabel("UAM Deployment Entry")
        t2.setObjectName("sub_lbl")
        title_col.addWidget(t1)
        title_col.addWidget(t2)
        header.addLayout(title_col)
        header.addStretch()

        self._theme_btn = QPushButton("🌙")
        self._theme_btn.setObjectName("theme_btn")
        self._theme_btn.setToolTip("Toggle dark / light mode")
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._theme_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self._theme_btn)

        vbox.addLayout(header)

        # ── Status card ───────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 14, 20, 14)
        card_layout.setSpacing(6)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self._dot = _Dot()
        status_row.addWidget(self._dot)
        self._status_lbl = QLabel("Server stopped")
        self._status_lbl.setObjectName("status_lbl")
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()
        card_layout.addLayout(status_row)

        self._url_lbl = QLabel(URL)
        self._url_lbl.setObjectName("url_lbl")
        card_layout.addWidget(self._url_lbl)
        vbox.addWidget(card)

        # ── Buttons ───────────────────────────────────────────────────────────
        self._start_btn = QPushButton("▶   Start Server")
        self._start_btn.setObjectName("start_btn")
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(self._toggle_server)
        vbox.addWidget(self._start_btn)

        self._browser_btn = QPushButton("⬡   Open in Browser")
        self._browser_btn.setObjectName("browser_btn")
        self._browser_btn.setCursor(Qt.PointingHandCursor)
        self._browser_btn.setEnabled(False)
        self._browser_btn.clicked.connect(lambda: webbrowser.open(URL))
        vbox.addWidget(self._browser_btn)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        vbox.addWidget(div)

        self._install_btn = QPushButton("⬇   Install Desktop Shortcut")
        self._install_btn.setObjectName("install_btn")
        self._install_btn.setCursor(Qt.PointingHandCursor)
        self._install_btn.clicked.connect(self._run_installer)
        vbox.addWidget(self._install_btn)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        QApplication.instance().setStyleSheet(
            _DARK_QSS if self._dark else _LIGHT_QSS
        )

    def _toggle_theme(self):
        self._dark = not self._dark
        self._theme_btn.setText("☀" if self._dark else "🌙")
        self._apply_theme()
        # Webapp theme is toggled from within the browser — no restart needed.

    # ── Server control ────────────────────────────────────────────────────────

    def _toggle_server(self):
        proc = self._proc_box[0] if self._proc_box else None
        if proc and proc.poll() is None:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        self._set_status("Starting…", "#6b7280")
        self._start_btn.setEnabled(False)
        self._start_btn.setText("  Starting…")

        self._server_thread = _ServerThread(self._proc_box)
        self._server_thread.started_ok.connect(self._on_started)
        self._server_thread.start_fail.connect(self._on_start_fail)
        self._server_thread.start()

    def _on_started(self):
        self._set_status("Server running", "#16a34a")
        self._start_btn.setObjectName("stop_btn")
        self._start_btn.setEnabled(True)
        self._start_btn.setText("■   Stop Server")
        self._apply_theme()   # refresh QSS so stop_btn colour picks up
        self._browser_btn.setEnabled(True)
        webbrowser.open(URL)

    def _on_start_fail(self, msg: str):
        self._set_status(f"Failed: {msg}", "#dc2626")
        self._start_btn.setObjectName("start_btn")
        self._start_btn.setEnabled(True)
        self._start_btn.setText("▶   Start Server")
        self._apply_theme()

    def _stop_server(self):
        proc = self._proc_box[0] if self._proc_box else None
        _kill_proc(proc)
        self._proc_box.clear()
        _atexit_proc.clear()
        self._set_status("Server stopped", "#dc2626")
        self._start_btn.setObjectName("start_btn")
        self._start_btn.setEnabled(True)
        self._start_btn.setText("▶   Start Server")
        self._apply_theme()
        self._browser_btn.setEnabled(False)

    def _set_status(self, text: str, color: str):
        self._status_lbl.setText(text)
        self._dot.set_color(color)

    # ── Installer ─────────────────────────────────────────────────────────────

    def _run_installer(self):
        install_script = HERE / "install.py"
        if not install_script.exists():
            return

        self._install_btn.setEnabled(False)
        self._install_btn.setText("  Installing…")

        dlg = QDialog(self)
        dlg.setWindowTitle("Installing…")
        dlg.setFixedSize(320, 100)
        lay = QVBoxLayout(dlg)
        lbl = QLabel("Starting…")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        dlg.show()

        import threading
        def run():
            try:
                proc = subprocess.Popen(
                    [PYTHON, str(install_script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(HERE),
                )
                for line in proc.stdout:
                    line = line.strip()
                    if line:
                        QTimer.singleShot(0, lambda l=line: lbl.setText(l))
                proc.wait()
                if proc.returncode == 0:
                    QTimer.singleShot(0, lambda: lbl.setText("✓ Installation complete!"))
                    QTimer.singleShot(1500, dlg.accept)
                    QTimer.singleShot(1500, lambda: self._install_btn.setText("✓   Shortcut Installed"))
                else:
                    QTimer.singleShot(0, lambda: lbl.setText("✗ Installation failed."))
                    QTimer.singleShot(2000, dlg.accept)
                    QTimer.singleShot(2000, lambda: self._install_btn.setText("⬇   Install Desktop Shortcut"))
            except Exception as exc:
                QTimer.singleShot(0, lambda: lbl.setText(f"Error: {exc}"))
                QTimer.singleShot(2000, dlg.accept)
                QTimer.singleShot(2000, lambda: self._install_btn.setText("⬇   Install Desktop Shortcut"))
            QTimer.singleShot(0, lambda: self._install_btn.setEnabled(True))

        threading.Thread(target=run, daemon=True).start()

    # ── Close ─────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._stop_server()
        event.accept()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Enable HiDPI scaling (required for Qt5; Qt6 enables it automatically)
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass
    app = QApplication(sys.argv)
    app.setApplicationName("FieldLog")
    # Set a readable system font at 11 pt so the OS DPI is respected
    app.setFont(QFont("", 11))
    win = FieldLogWindow()
    win.show()
    sys.exit(app.exec())
