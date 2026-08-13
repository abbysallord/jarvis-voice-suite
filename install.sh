#!/usr/bin/env bash
# ==============================================================================
# Jarvis Voice Suite - Automated Setup Installer for Antigravity (AGY)
# ==============================================================================

set -euo pipefail

JARVIS_DIR="$HOME/.jarvis"
CONFIG_DIR="$HOME/.gemini/config"
SYSTEMD_DIR="$HOME/.config/systemd/user"

echo "🎙️ Starting Jarvis Voice Suite Setup..."

# 1. Create target directories
mkdir -p "$JARVIS_DIR" "$JARVIS_DIR/logs" "$CONFIG_DIR" "$CONFIG_DIR/rules" "$SYSTEMD_DIR"

# 2. Check for system dependencies
echo "📦 Verifying system audio dependencies..."
for cmd in pw-play xdotool python3 pip; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌ Error: '$cmd' is not installed. Please install it first (e.g. sudo dnf install pipewire-utils xdotool python3)."
        exit 1
    fi
done
echo "✓ System dependencies verified."

# 3. Setting up Python Virtual Environment
echo "🐍 Creating Python virtual environment in $JARVIS_DIR/.venv..."
python3 -m venv "$JARVIS_DIR/.venv"
source "$JARVIS_DIR/.venv/bin/activate"

echo "📥 Installing required python packages..."
pip install --upgrade pip
pip install requests numpy soundfile sounddevice torch --extra-index-url https://download.pytorch.org/whl/cpu
pip install kittentts
deactivate
echo "✓ Python environment initialized."

# 4. Copying Scripts
echo "✍️ Copying Jarvis daemons and handlers..."
cp src/tts_server.py "$JARVIS_DIR/tts_server.py"
cp src/dictate_continuous.py "$JARVIS_DIR/dictate_continuous.py"
cp src/start_jarvis.py "$JARVIS_DIR/start_jarvis.py"
cp src/speak_completion.py "$JARVIS_DIR/speak_completion.py"
chmod +x "$JARVIS_DIR/speak_completion.py"

# 5. Configure Global Antigravity Lifecycle Hook
echo "⚙️ Registering global hooks in $CONFIG_DIR/hooks.json..."
cat <<EOF > "$CONFIG_DIR/hooks.json"
{
  "jarvis-voice": {
    "Stop": [
      {
        "type": "command",
        "command": "$JARVIS_DIR/speak_completion.py"
      }
    ]
  }
}
EOF

# 6. Configure Systemd User Service
echo "☁️ Creating Systemd User service..."
cat <<EOF > "$SYSTEMD_DIR/jarvis.service"
[Unit]
Description=Jarvis Voice & Hackathon Services Orchestrator
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python $JARVIS_DIR/start_jarvis.py
RemainAfterExit=yes

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable jarvis.service
systemctl --user restart jarvis.service

echo "=============================================================================="
echo "🎉 Setup Complete! Jarvis Voice Suite is running in the background."
echo "💡 To bind the toggle shortcut on GNOME:"
echo "   Go to Settings -> Keyboard -> Keyboard Shortcuts -> Custom Shortcuts"
echo "   Add a shortcut:"
echo "     Name: Toggle Jarvis Dictation"
echo "     Command: $JARVIS_DIR/.venv/bin/python $JARVIS_DIR/dictate_continuous.py"
echo "     Shortcut: Super + Shift + D"
echo "=============================================================================="
