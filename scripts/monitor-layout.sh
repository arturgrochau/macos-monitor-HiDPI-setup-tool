#!/bin/bash
# Universal shell launcher for Monitor Layout Manager
# Works with bash, zsh, fish, and other shells

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ lives one level under the repo root
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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
