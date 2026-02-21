#!/usr/bin/env bash
# FieldLog Installer — macOS
# Double-click this file in Finder to run.
# (The .command extension tells macOS to open it in Terminal.)

DIR="$(cd "$(dirname "$0")" && pwd)"

# Colours
BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
GRAY="\033[0;90m"
RESET="\033[0m"

header() {
    clear
    echo ""
    echo -e "${BOLD} ========================================"
    echo -e "   FieldLog  |  UAM Deployment Entry"
    echo -e "   Installer for macOS${RESET}"
    echo -e "${BOLD} ========================================${RESET}"
    echo ""
}

ok()   { echo -e "  ${GREEN}✓${RESET}  $1"; }
err()  { echo -e "  ${RED}✗${RESET}  $1"; }
info() { echo -e "  ${GRAY}·${RESET}  $1"; }

header

# ── Locate Python ──────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    err "Python 3 not found."
    echo ""
    echo "  Install options:"
    echo "    • https://www.python.org/downloads/macos/"
    echo "    • brew install python3"
    echo ""
    read -rp "  Press Enter to close..."
    exit 1
fi

PY_VER=$("$PYTHON" --version 2>&1)
ok "Found $PY_VER"


# ── Create / reuse virtualenv ──────────────────────────────────────────────────
VENV="$DIR/.venv"
echo ""
if [ -d "$VENV" ]; then
    info "Reusing existing virtualenv at .venv"
else
    info "Creating virtualenv at .venv ..."
    "$PYTHON" -m venv "$VENV"
    ok "Virtualenv created"
fi
VENV_PY="$VENV/bin/python"

# ── Install Python dependencies into venv ─────────────────────────────────────
echo ""
info "Installing Python dependencies (streamlit, folium, requests)..."
"$VENV_PY" -m pip install --quiet \
    "streamlit>=1.35.0" \
    "requests>=2.31.0" \
    "folium>=0.17.0" \
    "streamlit-folium>=0.22.0"

# ── Install Qt binding — PySide6 preferred, PyQt5 fallback ────────────────────
echo ""
info "Installing Qt binding..."
if "$VENV_PY" -m pip install --quiet "PySide6>=6.5.0,<6.9" 2>/dev/null; then
    ok "PySide6 installed"
else
    info "PySide6 not compatible with this macOS version — trying PyQt5..."
    if "$VENV_PY" -m pip install --quiet "PyQt5>=5.15" 2>/dev/null; then
        ok "PyQt5 installed (fallback)"
    else
        err "Could not install a Qt binding (PySide6 or PyQt5)."
        echo ""
        echo "  Try updating macOS to 10.15.7 or later, then re-run this installer."
        echo ""
        read -rp "  Press Enter to close..."
        exit 1
    fi
fi

# ── Create .app bundle + DMG on Desktop ───────────────────────────────────────
echo ""
info "Creating FieldLog.app and FieldLog.dmg on Desktop..."
"$VENV_PY" "$DIR/install.py" --dmg --skip-qt

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD} ========================================"
echo -e "   Installation complete!"
echo -e ""
echo -e "   FieldLog.app  →  drag to /Applications to install"
echo -e "   FieldLog.dmg  →  share this file to distribute FieldLog${RESET}"
echo -e "${BOLD} ========================================${RESET}"
echo ""
read -rp "  Press Enter to close..."
