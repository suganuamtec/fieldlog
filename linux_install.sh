#!/usr/bin/env bash
# FieldLog Installer — Linux
# Run:  bash linux_install.sh
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colours
BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
GRAY="\033[0;90m"
RESET="\033[0m"

header() {
    echo ""
    echo -e "${BOLD} ========================================"
    echo -e "   FieldLog  |  UAM Deployment Entry"
    echo -e "   Installer${RESET}"
    echo -e "${BOLD} ========================================${RESET}"
    echo ""
}

ok()   { echo -e "  ${GREEN}[OK]${RESET}  $1"; }
err()  { echo -e "  ${RED}[ERROR]${RESET} $1"; }
info() { echo -e "  ${GRAY}···${RESET}  $1"; }

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
    echo "  Install it with:"
    echo "    sudo apt install python3 python3-pip python3-tk   # Debian/Ubuntu"
    echo "    sudo dnf install python3 python3-pip python3-tkinter  # Fedora"
    echo ""
    exit 1
fi

PY_VER=$("$PYTHON" --version 2>&1)
ok "Found $PY_VER"

# ── Check tkinter ──────────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import tkinter" &>/dev/null; then
    err "tkinter not found (required for the launcher GUI)."
    echo ""
    echo "  Install it with:"
    echo "    sudo apt install python3-tk    # Debian/Ubuntu"
    echo "    sudo dnf install python3-tkinter  # Fedora"
    echo ""
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

# ── Create desktop shortcut ────────────────────────────────────────────────────
echo ""
info "Creating desktop shortcut..."
"$VENV_PY" "$DIR/install.py"

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD} ========================================"
echo -e "   Installation complete!"
echo -e "   Launch FieldLog from your Desktop"
echo -e "   or app menu.${RESET}"
echo -e "${BOLD} ========================================${RESET}"
echo ""
