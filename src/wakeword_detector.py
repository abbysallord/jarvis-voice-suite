import os
import sys
import time
import json
import requests
import subprocess
import numpy as np
import soundfile as sf
import sounddevice as sd

API_URL = os.environ.get("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
API_KEY = os.environ.get("OMNIROUTE_API_KEY", "anonymous")
STT_MODEL = os.environ.get("OMNIROUTE_STT_MODEL", "groq/whisper-large-v3-turbo")

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

def is_tts_playing() -> bool:
    try:
        r = requests.get("http://localhost:20129/status", timeout=0.5)
        if r.status_code == 200:
            return r.json().get("status") == "playing"
    except Exception:
        pass
    return False

def check_wakeword(audio_data) -> bool:
    temp_path = "/tmp/jarvis_wakeword_check.wav"
    sf.write(temp_path, audio_data, SAMPLE_RATE, subtype='PCM_16')
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        with open(temp_path, "rb") as f:
            files = {"file": ("wakeword.wav", f, "audio/wav")}
            data = {"model": STT_MODEL, "language": "en"}
            r = requests.post(f"{API_URL}/audio/transcriptions", headers=headers, files=files, data=data, timeout=3)
            if r.status_code == 200:
                text = r.json().get("text", "").lower().strip(" .!?")
                print(f"[WakeWord] Transcribed segment: '{text}'")
                
                # Check for phonetic variations of "Jarvis"
                keywords = ["jarvis", "jarves", "hey jarvis", "hi jarvis", "charles", "charlie", "travis", "service", "hirs", "hrvs", "harvest", "harvis", "artist", "office", "habas", "hobby", "harness"]
                for kw in keywords:
                    if kw in text:
                        return True
    except Exception as e:
        print(f"[WakeWord] Verification request failed: {e}")
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    return False

def main():
    print("🎙️ Starting Jarvis Wake-Word Listener...")
    
    # Calculate noise floor for calibration
    ambient_frames = []
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=CHUNK_SIZE, dtype='float32') as stream:
            for _ in range(10):
                data, _ = stream.read(CHUNK_SIZE)
                ambient_frames.append(np.sqrt(np.mean(data**2)))
    except Exception as se:
        print(f"Failed to open audio input: {se}")
        sys.exit(1)
        
    ambient_noise = np.mean(ambient_frames)
    threshold = max(ambient_noise * 1.5, 0.002) # More sensitive threshold to trigger easily on speech
    print(f"⚙️ Calibrated Wake-Word threshold: {threshold:.5f} (Ambient: {ambient_noise:.5f})")
    
    triggered = False
    
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=CHUNK_SIZE, dtype='float32') as stream:
            while True:
                # If TTS is speaking or dictation is already running, sleep and skip
                if is_tts_playing():
                    time.sleep(0.5)
                    continue
                
                data, _ = stream.read(CHUNK_SIZE)
                rms = np.sqrt(np.mean(data**2))
                
                # Trigger transcription verification if sound exceeds threshold
                if rms > threshold and not triggered:
                    triggered = True
                    print("[WakeWord] Sound event detected. Capturing wake phrase...")
                    
                    # Record 1.6s of future audio containing the wake phrase
                    wake_frames = []
                    for _ in range(int(1.6 * SAMPLE_RATE / CHUNK_SIZE)):
                        d, _ = stream.read(CHUNK_SIZE)
                        wake_frames.append(d.copy())
                        
                    full_segment = np.concatenate(wake_frames)
                    
                    # Verify wake word via fast STT
                    if check_wakeword(full_segment):
                        print("[WakeWord] WAKE WORD SUCCESS: 'Jarvis' matches. Activating mic!")
                        
                        # Trigger dictate_continuous.py in oneshot mode
                        dictate_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dictate_continuous.py")
                        subprocess.Popen([sys.executable, dictate_script, "--oneshot"])
                        
                        # Sleep to allow dictation loop to start and finish before resuming wake detection
                        time.sleep(8)
                    else:
                        # Cool-down to prevent rapid double-checks on ambient noise spikes
                        time.sleep(1.5)
                        
                    triggered = False
                    
    except KeyboardInterrupt:
        print("\nWake-Word Listener terminated.")
    except Exception as e:
        print(f"Error in Wake-Word loop: {e}")

if __name__ == "__main__":
    main()
