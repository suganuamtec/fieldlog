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

# ── Check tkinter (may need python-tk from brew) ───────────────────────────────
if ! "$PYTHON" -c "import tkinter" &>/dev/null; then
    err "tkinter not found."
    echo ""
    echo "  If you installed Python via Homebrew, run:"
    echo "    brew install python-tk"
    echo ""
    read -rp "  Press Enter to close..."
    exit 1
fi
ok "tkinter available"

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
info "Installing Python dependencies..."
"$VENV_PY" -m pip install --quiet -r "$DIR/requirements.txt"
ok "Dependencies installed (streamlit)"

# ── Create .app bundle on Desktop ─────────────────────────────────────────────
echo ""
info "Creating FieldLog.app on Desktop..."
"$VENV_PY" "$DIR/install.py"

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD} ========================================"
echo -e "   Installation complete!"
echo -e "   FieldLog.app is on your Desktop."
echo -e "   Drag it to /Applications to keep it.${RESET}"
echo -e "${BOLD} ========================================${RESET}"
echo ""
read -rp "  Press Enter to close..."
