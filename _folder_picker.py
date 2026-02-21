#!/usr/bin/env python3
"""
Qt file/folder picker helper — run as a subprocess from app.py.
Prints the chosen path to stdout (nothing on cancel).

Modes:
  python _folder_picker.py [initial_dir]
      → open folder picker, print chosen directory

  python _folder_picker.py --save [initial_dir] [default_filename]
      → open save-file dialog, print chosen file path
"""
import sys
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QFileDialog
except ImportError:
    from PyQt5.QtWidgets import QApplication, QFileDialog

app = QApplication(sys.argv)

if "--save" in sys.argv:
    idx     = sys.argv.index("--save")
    start   = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else str(Path.home())
    default = sys.argv[idx + 2] if idx + 2 < len(sys.argv) else "export.csv"
    path, _ = QFileDialog.getSaveFileName(
        None, "Save CSV", str(Path(start) / default),
        "CSV files (*.csv);;All files (*.*)",
    )
    if path:
        print(path, end="")
else:
    start  = sys.argv[1] if len(sys.argv) > 1 else str(Path.home())
    folder = QFileDialog.getExistingDirectory(
        None, "Select Folder", start,
        QFileDialog.Option.ShowDirsOnly,
    )
    if folder:
        print(folder, end="")
