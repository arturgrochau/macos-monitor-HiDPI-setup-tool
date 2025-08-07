#!/usr/bin/env fish
# Optional Fish Completion Setup
# Creates symlink for automatic completion pickup

set -l fish_config_dir ~/.config/fish
set -l functions_file "$fish_config_dir/functions/monitor-layout.fish"
set -l completions_file "$fish_config_dir/completions/monitor-layout.fish"

echo "🐟 Setting up Fish Shell Completion Symlink..."

# Check if function file exists
if not test -f $functions_file
    echo "⚠️  Function file not found: $functions_file"
    echo "💡 Run ./install-fish.fish first to set up the function"
    exit 1
end

# Create completions directory if it doesn't exist
mkdir -p (dirname $completions_file)

# Create symlink
if test -L $completions_file
    echo "✅ Completion symlink already exists"
else if test -f $completions_file
    echo "⚠️  Regular completion file exists, backing up..."
    mv $completions_file "$completions_file.backup"
    ln -s $functions_file $completions_file
    echo "✅ Completion symlink created (original backed up)"
else
    ln -s $functions_file $completions_file
    echo "✅ Completion symlink created"
end

echo "🎯 Fish shell will now auto-complete monitor-layout commands"
echo "💡 Restart fish or run: source $functions_file"
