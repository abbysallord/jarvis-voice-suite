import os
import sys
import json
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
        self.root.attributes("-alpha", 0.0)  # Starts invisible
        self.root.configure(bg="#050a18")
        
        # Sleek horizontal mini-bar dimensions: 320x52
        self.width = 320
        self.height = 52
        
        # Initial position: bottom right corner, slightly offset
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.width - 24
        y = screen_height - self.height - 80
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Dragging variables
        self.drag_x = 0
        self.drag_y = 0
        
        # Canvas for HUD graphics
        self.canvas = tk.Canvas(
            self.root, 
            width=self.width, 
            height=self.height, 
            bg="#050a18", 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Drag bindings to let user move the HUD anywhere on screen
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        
        # State variables
        self.state = "idle"
        self.display_text = ""
        self.angle = 0
        self.pulse = 0.0
        self.pulse_dir = 1
        
        # Start loops
        self.update_state()
        self.draw_loop()
        
    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
        
    def drag(self, event):
        deltax = event.x - self.drag_x
        deltay = event.y - self.drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
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
            
        # Hide when idle, show when active
        if self.state == "idle":
            self.root.attributes("-alpha", 0.0)
        else:
            self.root.attributes("-alpha", 0.85) # High visibility overlay
            
        self.root.after(100, self.update_state)
        
    def draw_loop(self):
        self.canvas.delete("all")
        
        if self.state != "idle":
            # 1. Outer holographic pill border
            self.draw_hud_frame()
            
            # 2. Main visual indicator (Left side)
            cx, cy = 30, self.height // 2
            if self.state == "listening":
                self.draw_listening_waves(cx, cy)
            elif self.state == "thinking":
                self.draw_thinking_loader(cx, cy)
            elif self.state == "speaking":
                self.draw_speaking_waves(cx, cy)
                
            # 3. Horizontal layout text / subtitle (Right side)
            self.draw_hud_text()
            
        # Animate angles & pulses
        self.angle = (self.angle + 4) % 360
        self.pulse += 0.08 * self.pulse_dir
        if self.pulse > 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse < 0.2:
            self.pulse = 0.2
            self.pulse_dir = 1
            
        self.root.after(30, self.draw_loop)
        
    def draw_hud_frame(self):
        # Semi-transparent capsule border
        self.canvas.create_rectangle(
            2, 2, self.width-2, self.height-2, 
            outline="#00f0ff", width=1, dash=(3, 6)
        )
        # Tech highlights at left and right edges
        self.canvas.create_line(2, 2, 10, 2, fill="#00f0ff", width=2)
        self.canvas.create_line(2, 2, 2, 10, fill="#00f0ff", width=2)
        self.canvas.create_line(self.width-2, 2, self.width-10, 2, fill="#00f0ff", width=2)
        self.canvas.create_line(self.width-2, 2, self.width-2, 10, fill="#00f0ff", width=2)
        
        self.canvas.create_line(2, self.height-2, 10, self.height-2, fill="#00f0ff", width=2)
        self.canvas.create_line(2, self.height-2, 2, self.height-10, fill="#00f0ff", width=2)
        self.canvas.create_line(self.width-2, self.height-2, self.width-10, self.height-2, fill="#00f0ff", width=2)
        self.canvas.create_line(self.width-2, self.height-2, self.width-2, self.height-10, fill="#00f0ff", width=2)

    def draw_listening_waves(self, cx, cy):
        r1 = 12 + self.pulse * 6
        r2 = 6 + self.pulse * 3
        self.canvas.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, outline="#00a8ff", width=1)
        self.canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, outline="#00f0ff", width=2)
        self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="#00f0ff")
        
        # Tiny expanding waveform lines
        for i in range(8):
            angle = i * (360 / 8) + (self.angle / 2)
            rad = math.radians(angle)
            h = 13 + (5 * math.sin(rad * 2 + self.pulse * 8))
            x1 = cx + 8 * math.cos(rad)
            y1 = cy + 8 * math.sin(rad)
            x2 = cx + h * math.cos(rad)
            y2 = cy + h * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill="#00f0ff", width=1.5)

    def draw_thinking_loader(self, cx, cy):
        self.canvas.create_oval(cx-14, cy-14, cx+14, cy+14, outline="#0066aa", width=1)
        
        # Rotating outer arc segment
        self.canvas.create_arc(
            cx-15, cy-15, cx+15, cy+15, 
            start=self.angle, extent=90, 
            outline="#00f0ff", width=2, style=tk.ARC
        )
        self.canvas.create_arc(
            cx-15, cy-15, cx+15, cy+15, 
            start=self.angle + 180, extent=90, 
            outline="#00f0ff", width=2, style=tk.ARC
        )
        
        # Inner reverse arc
        self.canvas.create_arc(
            cx-10, cy-10, cx+10, cy+10, 
            start=-self.angle * 1.5, extent=120, 
            outline="#00a8ff", width=1.5, style=tk.ARC
        )
        
        # Blinking core
        flash_color = "#00f0ff" if self.angle % 20 < 10 else "#0066aa"
        self.canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill=flash_color)

    def draw_speaking_waves(self, cx, cy):
        # Draw dynamic horizontal waveforms around center
        points = []
        for x in range(cx - 18, cx + 18, 2):
            dx = x - cx
            amp = 12 * math.exp(- (dx / 10) ** 2)
            y = cy + amp * math.sin(dx * 0.4 - self.angle * 0.15)
            points.append((x, y))
            
        for i in range(len(points) - 1):
            self.canvas.create_line(
                points[i][0], points[i][1], 
                points[i+1][0], points[i+1][1], 
                fill="#00f0ff", width=2
            )
            
    def draw_hud_text(self):
        # Clean, modern single-line status & subtitle text display
        state_labels = {
            "listening": "🎙️ LISTENING...",
            "thinking": "⚙️ PROCESSING...",
            "speaking": "🔊 JARVIS:"
        }
        label = state_labels.get(self.state, "JARVIS")
        color = "#00f0ff" if self.state == "listening" else ("#00ff66" if self.state == "speaking" else "#ffb300")
        
        # 1. State badge (small capsule)
        self.canvas.create_text(
            58, 16, text=label, fill=color, 
            anchor="w", font=("Sans", 8, "bold")
        )
        
        # 2. Main content/subtitle text
        text_content = self.display_text if self.state == "speaking" else "Awaiting speech..."
        if self.state == "listening":
            text_content = "Speak now... press Enter to submit"
            
        # Truncate text if it exceeds single line width
        max_chars = 34
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars-3] + "..."
            
        self.canvas.create_text(
            58, 34, text=text_content, fill="#e2f5ff", 
            anchor="w", font=("Sans", 9, "italic")
        )

def main():
    with open(STATE_FILE, "w") as f:
        json.dump({"state": "idle", "text": ""}, f)
        
    root = tk.Tk()
    app = JarvisHUD(root)
    root.mainloop()

if __name__ == "__main__":
    main()
