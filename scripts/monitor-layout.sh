#!/bin/bash
# Universal shell launcher for Monitor Layout Manager
# Works with bash, zsh, fish, and other shells

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ lives one level under the repo root
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Bootstrap the venv on a clean clone (missing venv, or click not installed)
if [ ! -f "$PROJECT_DIR/.venv/bin/python" ] || ! "$PROJECT_DIR/.venv/bin/python" -c "import click" >/dev/null 2>&1; then
    echo "⚙️  First run: setting up Python environment (.venv)..."
    python3 -m venv "$PROJECT_DIR/.venv" && \
        "$PROJECT_DIR/.venv/bin/pip" install -q -r "$PROJECT_DIR/requirements.txt"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to set up .venv — check that python3 is installed." >&2
        exit 1
    fi
    echo "✅ Environment ready."
fi

# Function to run CLI
run_cli() {
    if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
        "$PROJECT_DIR/.venv/bin/python" -m cli "$@"
    else
        python3 -m cli "$@"
    fi
}

# Function to run GUI
run_gui() {
    if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
        "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/main.py"
    else
        python3 "$PROJECT_DIR/main.py"
    fi
}

# Parse command
case "${1:-gui}" in
    "gui"|"")
        echo "🚀 Launching GUI..."
        cd "$PROJECT_DIR"
        run_gui
        ;;
    "cli")
        shift
        cd "$PROJECT_DIR"
        run_cli "$@"
        ;;
    *)
        # Default to CLI for any other command
        cd "$PROJECT_DIR"
        run_cli "$@"
        ;;
esac
