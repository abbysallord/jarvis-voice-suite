import os
import sys
import time
import requests
import subprocess
import signal
import numpy as np
import soundfile as sf
import sounddevice as sd

API_URL = os.environ.get("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
API_KEY = os.environ.get("OMNIROUTE_API_KEY", "anonymous")
STT_MODEL = os.environ.get("OMNIROUTE_STT_MODEL", "groq/whisper-large-v3-turbo")
PID_FILE = "/tmp/dictate_continuous.pid"

def play_beep(freq=880, duration=0.08, count=1):
    try:
        sample_rate = 16000
        for i in range(count):
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            tone = np.sin(2 * np.pi * freq * t)
            fade = int(sample_rate * 0.01)
            tone[-fade:] *= np.linspace(1, 0, fade)
            audio = (tone * 14000).astype(np.int16)
            temp_wav = f"/tmp/dictate_beep_{i}.wav"
            sf.write(temp_wav, audio, sample_rate, subtype='PCM_16')
            subprocess.run(["aplay", "-q", temp_wav])
            try:
                os.unlink(temp_wav)
            except OSError:
                pass
            if count > 1:
                time.sleep(0.05)
    except Exception:
        pass

def is_tts_playing() -> bool:
    try:
        r = requests.get("http://localhost:20129/status", timeout=1)
        if r.status_code == 200:
            return r.json().get("status") == "playing"
    except Exception:
        pass
    return False

def signal_handler(signum, frame):
    if os.path.exists(PID_FILE):
        try:
            os.unlink(PID_FILE)
        except OSError:
            pass
    play_beep(440, 0.12, count=2)  # Low double-beep for Toggle-OFF
    sys.exit(0)

def main():
    oneshot = "--oneshot" in sys.argv
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if not oneshot:
        # Toggle Check: If already running, kill it
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, signal.SIGTERM)
                print(f"Terminated existing dictation daemon with PID {old_pid}")
                sys.exit(0)
            except ProcessLookupError:
                pass
            except ValueError:
                pass

        # Save active PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

    # Start audio beeps
    if oneshot:
        # Single high beep for oneshot recording start
        play_beep(1000, 0.08, count=1)
    else:
        # High double-beep for Toggle-ON
        play_beep(1000, 0.08, count=2)

    try:
        requests.post("http://localhost:20129/interrupt", timeout=0.5)
    except Exception:
        pass

    if oneshot:
        print(f"One-shot dictation started with PID {os.getpid()}")
    else:
        print(f"Continuous dictation daemon started with PID {os.getpid()}")

    sample_rate = 16000
    chunk_size = 1024
    was_playing = False

    while True:
        if not oneshot:
            if is_tts_playing():
                was_playing = True
                time.sleep(0.3)
                continue
                
            if was_playing:
                time.sleep(1.2)
                was_playing = False

        # 1. Calibrate noise floor
        ambient_frames = []
        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, blocksize=chunk_size, dtype='float32') as stream:
                for _ in range(4):
                    data, _ = stream.read(chunk_size)
                    ambient_frames.append(np.sqrt(np.mean(data**2)))
        except Exception:
            if oneshot:
                play_beep(400, 0.15, count=1)
                sys.exit(1)
            time.sleep(1)
            continue

        ambient_noise = np.mean(ambient_frames)
        threshold = max(ambient_noise * 1.5, 0.003)

        # 2. Record audio
        frames = []
        speech_detected = False
        silent_chunks = 0
        active_chunks_count = 0
        
        max_silence_chunks = int(1.2 * sample_rate / chunk_size)    # 1.2s silence
        max_initial_silence = int(3.0 * sample_rate / chunk_size)  # 3s timeout for oneshot
        if not oneshot:
            max_initial_silence = int(4.0 * sample_rate / chunk_size)
        max_total_chunks = int(120.0 * sample_rate / chunk_size)

        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, blocksize=chunk_size, dtype='float32') as stream:
                for chunk_idx in range(max_total_chunks):
                    if not oneshot and is_tts_playing():
                        break
                            
                    data, _ = stream.read(chunk_size)
                    frames.append(data.copy())
                    
                    rms = np.sqrt(np.mean(data**2))
                    
                    if rms > threshold:
                        speech_detected = True
                        active_chunks_count += 1
                        silent_chunks = 0
                    else:
                        if speech_detected:
                            silent_chunks += 1
                    
                    if speech_detected and silent_chunks > max_silence_chunks:
                        break
                    
                    if not speech_detected and chunk_idx > max_initial_silence:
                        break
        except Exception:
            if oneshot:
                play_beep(400, 0.15, count=1)
                sys.exit(1)
            time.sleep(1)
            continue

        # Enforce minimum active chunks
        if not speech_detected or len(frames) < 12 or active_chunks_count < 3:
            if oneshot:
                play_beep(400, 0.15, count=1)
                sys.exit(0)
            continue

        # Process captured speech
        audio_data = np.concatenate(frames)
        temp_record_path = "/tmp/dictate_continuous_input.wav"
        sf.write(temp_record_path, audio_data, sample_rate, subtype='PCM_16')

        # Transcribe
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }
        data = {
            "model": STT_MODEL
        }
        
        text = ""
        try:
            with open(temp_record_path, "rb") as f:
                files = {
                    "file": ("user_voice.wav", f, "audio/wav")
                }
                response = requests.post(f"{API_URL}/audio/transcriptions", headers=headers, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                text = result.get("text", "").strip()
        except Exception:
            if oneshot:
                play_beep(400, 0.15, count=1)
                sys.exit(1)
            continue

        if not text:
            if oneshot:
                play_beep(400, 0.15, count=1)
                sys.exit(0)
            continue

        # Whisper hallucinations filter
        cleaned_text = text.lower().strip(" .!?")
        hallucinations = {
            "the", "the.", "you", "you.", "thank you", "thank you.", 
            "subtitles by", "subtitles by...", "bye", "bye.", "yes", "yes.", 
            "i'm going to go to the next one", "i'm going to go to the next one.",
            "thank you for watching", "thank you for watching.",
            "i'm sorry", "i'm sorry.", "sorry", "sorry.",
            "i'm going to go", "i'm going to go."
        }
        
        if len(text) < 4 or cleaned_text in hallucinations:
            print(f"Discarded noise/hallucination: '{text}'")
            if oneshot:
                play_beep(400, 0.15, count=1)
                sys.exit(0)
            continue

        # Play short acknowledgement beep
        play_beep(1200, 0.05, count=1)
        
        # Type text and press Return
        try:
            subprocess.run(["xdotool", "type", "--delay", "5", text])
            subprocess.run(["xdotool", "key", "Return"])
        except Exception:
            pass

        if oneshot:
            sys.exit(0)

        # Cool-down to prevent self-triggering
        time.sleep(2.5)

if __name__ == "__main__":
    main()
