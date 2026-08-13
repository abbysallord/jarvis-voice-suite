import os
import sys
import json
import time
import math
import tkinter as tk

STATE_FILE = "/tmp/jarvis_hud_state.json"

class JarvisHUD:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis HUD")
        
        # Borderless, always on top, semi-transparent
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg="#050a18")
        
        # Position at bottom right corner
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.width = 320
        self.height = 360
        x = screen_width - self.width - 24
        y = screen_height - self.height - 80
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Canvas for premium holographic graphics
        self.canvas = tk.Canvas(
            self.root, 
            width=self.width, 
            height=self.height, 
            bg="#050a18", 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initial state
        self.state = "idle"
        self.display_text = ""
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        
        # State monitoring loop
        self.update_state()
        self.draw_loop()
        
    def update_state(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    self.state = data.get("state", "idle")
                    self.display_text = data.get("text", "")
            else:
                self.state = "idle"
        except Exception:
            pass
            
        # Hide/minimize when idle, show when active
        if self.state == "idle":
            self.root.attributes("-alpha", 0.0) # Fully transparent/invisible
        else:
            self.root.attributes("-alpha", 0.9) # Make it pop up
            
        self.root.after(100, self.update_state)
        
    def draw_loop(self):
        self.canvas.delete("all")
        
        if self.state != "idle":
            # 1. Background holographic grid lines (cyberpunk style)
            self.draw_hologram_grid()
            
            # 2. Main animated indicator
            cx, cy = self.width // 2, 140
            
            if self.state == "listening":
                self.draw_listening_waves(cx, cy)
            elif self.state == "thinking":
                self.draw_thinking_loader(cx, cy)
            elif self.state == "speaking":
                self.draw_speaking_telemetry(cx, cy)
                
            # 3. Subtitle / Status Text Display
            self.draw_status_text()
            
        # Spin and pulse variables
        self.angle = (self.angle + 4) % 360
        self.pulse += 0.08 * self.pulse_dir
        if self.pulse > 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse < 0.2:
            self.pulse = 0.2
            self.pulse_dir = 1
            
        self.root.after(30, self.draw_loop)
        
    def draw_hologram_grid(self):
        # Semi-transparent boundary box
        self.canvas.create_rectangle(
            5, 5, self.width-5, self.height-5, 
            outline="#00f0ff", width=1, dash=(4, 8)
        )
        # Tech corners
        size = 12
        for x, y in [(5, 5), (self.width-5, 5), (5, self.height-5), (self.width-5, self.height-5)]:
            dx = size if x == 5 else -size
            dy = size if y == 5 else -size
            self.canvas.create_line(x, y, x + dx, y, fill="#00f0ff", width=2)
            self.canvas.create_line(x, y, x, y + dy, fill="#00f0ff", width=2)
            
    def draw_listening_waves(self, cx, cy):
        # Pulse expanding cyan sonar rings
        r1 = 40 + self.pulse * 30
        r2 = 20 + self.pulse * 15
        self.canvas.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, outline="#00a8ff", width=1)
        self.canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, outline="#00f0ff", width=2)
        self.canvas.create_oval(cx-10, cy-10, cx+10, cy+10, fill="#00f0ff")
        
        # Audio wave indicators radiating from center
        for i in range(12):
            angle = i * (360 / 12) + (self.angle / 2)
            rad = math.radians(angle)
            h = 45 + (15 * math.sin(rad * 4 + self.pulse * 10))
            x1 = cx + 35 * math.cos(rad)
            y1 = cy + 35 * math.sin(rad)
            x2 = cx + h * math.cos(rad)
            y2 = cy + h * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill="#00f0ff", width=2)
            
    def draw_thinking_loader(self, cx, cy):
        # Concentric rotating dotted tech rings
        self.canvas.create_oval(cx-50, cy-50, cx+50, cy+50, outline="#0066aa", width=1)
        
        # Rotating outer arc
        self.canvas.create_arc(
            cx-55, cy-55, cx+55, cy+55, 
            start=self.angle, extent=60, 
            outline="#00f0ff", width=3, style=tk.ARC
        )
        self.canvas.create_arc(
            cx-55, cy-55, cx+55, cy+55, 
            start=self.angle + 180, extent=60, 
            outline="#00f0ff", width=3, style=tk.ARC
        )
        
        # Reverse rotating inner arc
        self.canvas.create_arc(
            cx-40, cy-40, cx+40, cy+40, 
            start=-self.angle * 1.5, extent=120, 
            outline="#00a8ff", width=2, style=tk.ARC
        )
        
        # Core flashing telemetry
        flash_color = "#00f0ff" if self.angle % 30 < 15 else "#0066aa"
        self.canvas.create_oval(cx-15, cy-15, cx+15, cy+15, fill=flash_color)
        
    def draw_speaking_telemetry(self, cx, cy):
        # Simulated digital wave rings
        r = 50
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#0066aa", width=1, dash=(2, 4))
        
        # Draw active sine waves mirroring speaking
        points = []
        for x in range(cx - 80, cx + 80, 2):
            dx = x - cx
            amp = 25 * math.exp(- (dx / 40) ** 2) # Gaussian envelope
            y = cy + amp * math.sin(dx * 0.15 - self.angle * 0.1)
            points.append((x, y))
            
        for i in range(len(points) - 1):
            self.canvas.create_line(
                points[i][0], points[i][1], 
                points[i+1][0], points[i+1][1], 
                fill="#00f0ff", width=2
            )
            
    def draw_status_text(self):
        # Display current Jarvis state badge
        state_labels = {
            "listening": "🎙️ JARVIS - LISTENING",
            "thinking": "⚙️ JARVIS - PROCESSING",
            "speaking": "🔊 JARVIS - SPEAKING"
        }
        label = state_labels.get(self.state, "JARVIS")
        color = "#00f0ff" if self.state == "listening" else ("#00ff66" if self.state == "speaking" else "#ffb300")
        
        # Header Status Badge
        self.canvas.create_rectangle(
            20, 240, self.width-20, 265, 
            fill="#0c1b3a", outline=color, width=1
        )
        self.canvas.create_text(
            self.width//2, 252, 
            text=label, fill=color, 
            font=("Sans", 10, "bold")
        )
        
        # Body text / subtitle
        text_content = self.display_text if self.state == "speaking" else "Awaiting input..."
        if self.state == "listening":
            text_content = "Speak now. The microphone is actively capturing voice input..."
            
        # Wrap long subtitle text
        words = text_content.split()
        lines = []
        current_line = []
        for word in words:
            if len(" ".join(current_line + [word])) > 32:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        if current_line:
            lines.append(" ".join(current_line))
            
        # Draw subtitles
        y_offset = 285
        for line in lines[:3]: # Limit to 3 lines
            self.canvas.create_text(
                self.width//2, y_offset, 
                text=line, fill="#e2f5ff", 
                font=("Sans", 9, "italic")
            )
            y_offset += 20

def main():
    # Write initial idle state
    with open(STATE_FILE, "w") as f:
        json.dump({"state": "idle", "text": ""}, f)
        
    root = tk.Tk()
    app = JarvisHUD(root)
    root.mainloop()

if __name__ == "__main__":
    main()
