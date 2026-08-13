import os
import re
import sys
import json
import numpy as np
import soundfile as sf
import sounddevice as sd
import torch
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

# Override torch.load to bypass weights security block
original_load = torch.load
def custom_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = custom_load

from kittentts import KittenTTS

print("🔊 Loading KittenTTS model into persistent memory...")
try:
    model = KittenTTS("KittenML/kitten-tts-mini-0.8")
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# Global playback state
playback_active = False
active_playback_proc = None
playback_lock = threading.Lock()

def lower_pitch(audio, factor=0.93):
    xp = np.arange(len(audio))
    x = np.arange(0, len(audio), factor)
    return np.interp(x, xp, audio)

class TTSRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress request logging

    def do_GET(self):
        global playback_active
        if self.path == "/status":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status_json = json.dumps({"status": "playing" if playback_active else "idle"})
            self.wfile.write(status_json.encode('utf-8'))

    def do_POST(self):
        global playback_active, active_playback_proc
        
        if self.path == "/interrupt":
            try:
                if active_playback_proc and active_playback_proc.poll() is None:
                    active_playback_proc.terminate()
            except Exception as ie:
                print(f"Interrupt failed: {ie}")
            with playback_lock:
                playback_active = False
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"interrupted"}')
            return

        if self.path == "/speak":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            text = payload.get("text", "")
            
            if text:
                clean = re.sub(r'#+\s*', '', text)
                clean = re.sub(r'[*_`~]', '', clean)
                clean = re.sub(r'[-•+]\s*', '', clean)
                clean = re.sub(r'\[.*?\]', '', clean)
                clean = re.sub(r'\*.*?\*', '', clean)
                clean = re.sub(r'[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDC00-\uDFFF]', '', clean)
                clean_text = clean.strip()
                
                if clean_text:
                    try:
                        # Use Luna voice with speed=1.35 and pitch lowered by 7% to sound more mature
                        audio = model.generate(clean_text, voice="Luna", speed=1.35)
                        audio = lower_pitch(audio, 0.93)
                        max_val = np.max(np.abs(audio))
                        if max_val > 0:
                            audio = audio / max_val
                        
                        reply_wav = os.path.expanduser("~/.jarvis/voice_reply.wav")
                        sf.write(reply_wav, audio, 24000, subtype='PCM_16')
                        
                        # Set active playback flag
                        with playback_lock:
                            playback_active = True
                        
                        # Play to speaker using robust pw-play command
                        def play_and_reset():
                            global playback_active, active_playback_proc
                            try:
                                active_playback_proc = subprocess.Popen(["pw-play", reply_wav])
                                active_playback_proc.wait()
                            except Exception as pe:
                                print(f"Playback failed: {pe}")
                            with playback_lock:
                                playback_active = False
                        
                        threading.Thread(target=play_and_reset).start()
                    except Exception as e:
                        print(f"Synthesis failed: {e}")
                        with playback_lock:
                            playback_active = False
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"success"}')

def run_server():
    server = HTTPServer(('localhost', 20129), TTSRequestHandler)
    print("🚀 TTS Server listening on http://localhost:20129/speak")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
