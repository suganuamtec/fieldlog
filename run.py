#!/usr/bin/env python3
"""
Universal launcher — Windows / Mac / Linux
Usage:  python run.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def main():
    print("Installing dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(HERE / "requirements.txt")]
    )
    print("Starting UAM Deployment Entry...")
    subprocess.call(
        [sys.executable, "-m", "streamlit", "run", str(HERE / "app.py")]
    )


if __name__ == "__main__":
    main()
