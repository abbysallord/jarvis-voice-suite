# 🎙️ Jarvis Voice Suite for Antigravity (AGY)

An open-source, hands-free, sub-second latency voice-to-voice interaction suite for Google Antigravity (AGY).

```
 ┌────────────────────────────────────────────────────────┐
 │                      User Speaks                       │
 └──────────────────────────┬─────────────────────────────┘
                            │ (VAD / Earbuds Mic)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │   dictate_continuous.py (Continuous Listening Loop)    │
 └──────────────────────────┬─────────────────────────────┘
                            │ (Whisper Transcription / Port 20128)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │              Antigravity IDE/CLI Chat                  │
 └──────────────────────────┬─────────────────────────────┘
                            │ (Stop Event Lifecycle Hook)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │         speak_completion.py (Hook Intercept)           │
 └──────────────────────────┬─────────────────────────────┘
                            │ (POST /speak / Port 20129)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │      tts_server.py (Hot KittenTTS Memory / pw-play)    │
 └──────────────────────────┬─────────────────────────────┘
                            │ (Bluetooth Audio Output)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │                     User Hears AI                      │
 └────────────────────────────────────────────────────────┘
```

---

## ✨ Features

* **Continuous Hands-Free Input**: Voice activation loop (`Super + Shift + D`) that dynamically calibrates VAD to filter background noise (e.g., classroom ambient chatter).
* **Sub-Second Voice Output**: A persistent TTS server that keeps the `KittenTTS` model in memory for millisecond synthesis.
* **Adult Feminine Voice Profile (`Luna`)**: Tuned using native neural speed scaling (`1.35`) and pitch-lowering (`0.93`) for warm, natural speech.
* **Speech Barge-In (Interruption)**: Activating the dictation loop instantly terminates active playback processes, letting you speak over long answers.
* **PipeWire Routing Integration**: Uses native `pw-play` to output audio, seamlessly routing to Bluetooth earbuds when connected.
* **Global Agent Hook**: Integrated via a global `Stop` hook (`hooks.json`) so any new chat conversation automatically speaks responses.
* **Self-Healing Launch Orchestration**: A Systemd User Service (`jarvis.service`) that automatically starts the API Gateway (OmniRoute), TTS Server, VAD Daemon, and Hackathon Server on user login.

## 💻 Operating System Compatibility

| OS | Status | Notes |
| :--- | :--- | :--- |
| **Linux** | 🟢 Native (Supported) | Full features: uses PipeWire (`pw-play`), Systemd User units, and `xdotool` out-of-the-box. |
| **macOS** | 🟡 Adaptable (In Progress) | Needs changing `pw-play` to `afplay`, systemd to `launchd`, and `xdotool` to AppleScript (`osascript`) keystrokes. |
| **Windows** | 🟡 Adaptable (WSL / Native) | Runs inside WSL, or natively by swapping `pw-play` for `winsound` or `mpv.exe` and `xdotool` for Python's `pyautogui`/`pynput` key injection. |

---

## 📂 Repository Structure

```
jarvis-voice-suite/
├── LICENSE                 # MIT Open Source License
├── README.md               # Documentation
├── install.sh              # Automated Unix Setup Script
├── src/
│   ├── tts_server.py       # Text-to-Speech hot memory daemon (Port 20129)
│   ├── dictate_continuous.py # Speech-to-Text VAD dictation loop
│   ├── start_jarvis.py     # Background services orchestrator
│   └── speak_completion.py # Stop hook response audio synthesizer
└── config/
    ├── hooks.json          # Global Antigravity Hook config
    └── user_jarvis_preferences.mdc # Tuned voice rules
```

---

## 🚀 Quick Setup

Ensure your Linux system has `pipewire-utils`, `xdotool`, `python3`, and `pip` installed, then run the installer:

```bash
git clone https://github.com/YOUR_USERNAME/jarvis-voice-suite.git
cd jarvis-voice-suite
bash install.sh
```

### Keyboard Toggle Shortcut:
1. Open GNOME **Settings > Keyboard > Keyboard Shortcuts > Custom Shortcuts**.
2. Add a new shortcut:
   * **Name**: `Toggle Jarvis Dictation`
   * **Command**: `/home/YOUR_USERNAME/.jarvis/.venv/bin/python /home/YOUR_USERNAME/.jarvis/dictate_continuous.py`
   * **Shortcut**: **`Super + Shift + D`** (or your custom preference).

---

## 📝 License

Distributed under the **MIT License**. See `LICENSE` for details.
