#!/usr/bin/env python3
import subprocess
import time
import socket
import os

VENV_PYTHON = "/home/dhanush/Projects/Experiments/.venv_kittentts/bin/python"
SYS_PYTHON = "python"
TTS_SCRIPT = "/home/dhanush/Projects/Experiments/tts_server.py"
DICTATE_SCRIPT = "/home/dhanush/Projects/Experiments/dictate_continuous.py"
SIH_SCRIPT = "/home/dhanush/Projects/Experiments/sih_server.py"
OMNIROUTE_CMD = ["node", "/home/dhanush/.npm-global/lib/node_modules/omniroute/bin/omniroute.mjs", "serve"]

LOG_DIR = "/home/dhanush/Projects/Experiments/logs"
os.makedirs(LOG_DIR, exist_ok=True)

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def check_process_running(script_name):
    try:
        output = subprocess.check_output(["pgrep", "-f", script_name])
        return len(output.strip()) > 0
    except subprocess.CalledProcessError:
        return False

def start_daemon(command, log_name):
    log_file = open(os.path.join(LOG_DIR, log_name), "a")
    proc = subprocess.Popen(command, stdout=log_file, stderr=log_file, start_new_session=True)
    return proc

def main():
    print("--- Starting Jarvis Services ---")

    # 1. Start OmniRoute on Port 20128 (Must be online first for Whisper STT)
    if is_port_open(20128):
        print("[✓] OmniRoute is already running on port 20128")
    else:
        print("[ ] Starting OmniRoute...")
        start_daemon(OMNIROUTE_CMD, "omniroute.log")
        # Wait up to 10 seconds for OmniRoute to start up
        for _ in range(20):
            if is_port_open(20128):
                print("[✓] OmniRoute initialized successfully on port 20128")
                break
            time.sleep(0.5)
        else:
            print("[!] Warning: OmniRoute is taking a long time to bind. Continuing...")

    # 2. Start TTS Server on Port 20129
    if is_port_open(20129):
        print("[✓] TTS Server is already running on port 20129")
    else:
        print("[ ] Starting TTS Server...")
        start_daemon([VENV_PYTHON, TTS_SCRIPT], "tts_server.log")
        for _ in range(20):
            if is_port_open(20129):
                print("[✓] TTS Server initialized successfully on port 20129")
                break
            time.sleep(0.5)
        else:
            print("[!] Warning: TTS Server is taking a long time to bind. Continuing...")

    # 3. Start Wake-Word Detector Daemon
    WAKEWORD_SCRIPT = "/home/dhanush/Projects/Experiments/wakeword_detector.py"
    if check_process_running(WAKEWORD_SCRIPT):
        print("[✓] Wake-Word Detector Daemon is already running")
    else:
        print("[ ] Starting Wake-Word Detector Daemon...")
        start_daemon([VENV_PYTHON, WAKEWORD_SCRIPT], "wakeword_detector.log")
        time.sleep(1)
        if check_process_running(WAKEWORD_SCRIPT):
            print("[✓] Wake-Word Detector started successfully")
        else:
            print("[!] Error: Wake-Word Detector failed to start. Check logs/wakeword_detector.log")

    # 4. Start SIH Diagnostics Server on Port 20130
    if is_port_open(20130):
        print("[✓] SIH Server is already running on port 20130")
    else:
        print("[ ] Starting SIH Diagnostics Server...")
        start_daemon([SYS_PYTHON, SIH_SCRIPT], "sih_server.log")
        time.sleep(1.5)
        if is_port_open(20130):
            print("[✓] SIH Diagnostics Server initialized on port 20130")
        else:
            print("[!] Error: SIH Server failed to bind. Check logs/sih_server.log")

    # 5. Start Jarvis HUD Overlay
    HUD_SCRIPT = "/home/dhanush/Projects/Experiments/jarvis_hud.py"
    if check_process_running(HUD_SCRIPT):
        print("[✓] Jarvis HUD is already running")
    else:
        print("[ ] Starting Jarvis HUD Overlay...")
        start_daemon([SYS_PYTHON, HUD_SCRIPT], "jarvis_hud.log")
        time.sleep(1)
        if check_process_running(HUD_SCRIPT):
            print("[✓] Jarvis HUD started successfully")
        else:
            print("[!] Error: Jarvis HUD failed to start. Check logs/jarvis_hud.log")

    print("\nAll Jarvis background daemons are synced and running.")

if __name__ == "__main__":
    main()
