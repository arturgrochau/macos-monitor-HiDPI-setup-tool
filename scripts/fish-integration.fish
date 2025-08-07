#!/usr/bin/env fish
# Fish Shell Integration for Monitor Layout Manager
# Place this in ~/.config/fish/functions/monitor-layout.fish

function monitor-layout --description 'Monitor Layout Manager with fish shell integration'
    set -l script_dir (dirname (status --current-filename))
    set -l project_dir (realpath "$script_dir/..")
    set -l python_script "$project_dir/cli/advanced_cli.py"
    
    # Check if we're in the correct directory or if the script exists
    if not test -f "$python_script"
        # Try to find the script relative to current directory
        if test -f "./cli/advanced_cli.py"
            set python_script "./cli/advanced_cli.py"
            set project_dir "."
        else
            echo "❌ Error: Monitor Layout Manager not found"
            echo "Make sure you're in the project directory or install it properly"
            return 1
        end
    end
    
    # Configure Python environment if available
    if test -d "$project_dir/.venv"
        # Use virtual environment if available - set environment variables
        set -lx VIRTUAL_ENV "$project_dir/.venv"
        set -lx PATH "$project_dir/.venv/bin" $PATH
        "$project_dir/.venv/bin/python" "$python_script" $argv
    else if command -q conda
        # Use conda if available
        python "$python_script" $argv
    else
        # Fall back to system python
        python3 "$python_script" $argv
    end
end

# Completions for fish shell
complete -c monitor-layout -f

# Subcommands
complete -c monitor-layout -n '__fish_use_subcommand' -a 'detect' -d 'Detect connected displays'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'save' -d 'Save current layout'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'load' -d 'Load saved layout'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'list-layouts' -d 'List all layouts'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'delete' -d 'Delete a layout'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'export' -d 'Export layouts'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'import-layouts' -d 'Import layouts'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'backup' -d 'Create backup'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'gui' -d 'Launch GUI'
complete -c monitor-layout -n '__fish_use_subcommand' -a 'doctor' -d 'Run diagnostics'

# Options for detect command
complete -c monitor-layout -n '__fish_seen_subcommand_from detect' -l detailed -s d -d 'Show detailed information'
complete -c monitor-layout -n '__fish_seen_subcommand_from detect' -l json-output -s j -d 'JSON output format'

# Options for save command
complete -c monitor-layout -n '__fish_seen_subcommand_from save' -l name -s n -d 'Layout name' -r
complete -c monitor-layout -n '__fish_seen_subcommand_from save' -l description -s d -d 'Layout description' -r

# Options for load command
complete -c monitor-layout -n '__fish_seen_subcommand_from load' -l interactive -s i -d 'Interactive selection'
# Dynamic completion for layout names - will be populated by available layouts
complete -c monitor-layout -n '__fish_seen_subcommand_from load' -a '(monitor-layout list-layouts 2>/dev/null | grep "^•" | cut -d" " -f2 | tr -d "[:cntrl:]")'

# Options for delete command - also use dynamic layout names
complete -c monitor-layout -n '__fish_seen_subcommand_from delete' -a '(monitor-layout list-layouts 2>/dev/null | grep "^•" | cut -d" " -f2 | tr -d "[:cntrl:]")'

# Options for export command
complete -c monitor-layout -n '__fish_seen_subcommand_from export' -l output -s o -d 'Output file' -r

# Options for import-layouts command
complete -c monitor-layout -n '__fish_seen_subcommand_from import-layouts' -l merge -s m -d 'Merge with existing'

# Fish shell aliases for common operations
alias mlt='monitor-layout'
alias mldetect='monitor-layout detect'
alias mlgui='monitor-layout gui'
alias mlsave='monitor-layout save'
alias mlload='monitor-layout load'
alias mllist='monitor-layout list-layouts'
alias mldoctor='monitor-layout doctor'
