#!/usr/bin/env python3
"""
AI-Aimbot v4 - Matrix Dark Green Edition
Clean, structured Triggerbot + Aim Assist for Linux (X11)
"""

import json
import os
import threading
import time
import subprocess

import cv2
import mss
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO
import customtkinter as ctk


# ====================== MATRIX THEME ======================
ctk.set_appearance_mode("dark")

MATRIX_BG = "#0a0f0a"
MATRIX_DARK = "#050805"
MATRIX_GREEN = "#00ff41"
MATRIX_GREEN_DARK = "#00cc33"
MATRIX_TEXT = "#e8ffe8"
MATRIX_TEXT_DIM = "#88aa88"
PANEL_BG = "#0f150f"


# ====================== SETTINGS ======================
SETTINGS_FILE = "aimbot_config.json"

DEFAULT_SETTINGS = {
    "triggerbot_enabled": True,
    "aim_assist_enabled": True,
    "headshot_mode": True,
    "confidence": 0.42,
    "screenshot_size": 320,
    "trigger_width": 45,
    "trigger_height": 75,
    "fire_delay": 15,
    "aim_strength": 0.28,
    "aa_movement_amp": 0.40,
    "show_boxes": True,
    "monitor_index": 1,
}


class Settings:
    def __init__(self):
        for key, value in DEFAULT_SETTINGS.items():
            setattr(self, key, value)


settings = Settings()


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        except Exception:
            pass


def save_settings():
    data = {k: getattr(settings, k) for k in DEFAULT_SETTINGS}
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


load_settings()


# ====================== AIMBOT ENGINE ======================
class AimbotEngine:
    def __init__(self):
        self.model = None
        self.sct = mss.MSS()
        self.last_shot = 0
        self.detections_count = 0

    def _get_safe_device(self):
        """Gibt das Device zurück. GTX 1050 Ti (sm_61) wird jetzt unterstützt."""
        if not torch.cuda.is_available():
            return "cpu"

        try:
            props = torch.cuda.get_device_properties(0)
            cc = props.major * 10 + props.minor

            # GTX 1050 Ti (sm_61) und neuere werden unterstützt
            # Wichtig: PyTorch muss mit passendem CUDA (cu118/cu121) kompiliert sein!
            if cc >= 61:
                print(f"[INFO] GPU Compute Capability {props.major}.{props.minor} → CUDA-Modus")
                return "cuda"
            else:
                print(f"[WARN] Sehr alte GPU (CC {props.major}.{props.minor}) → CPU-Modus")
                return "cpu"
        except Exception:
            return "cpu"

    def load_model(self):
        try:
            model_path = "yolov8n.pt"

            if not os.path.exists(model_path):
                print("[INFO] YOLOv8n Modell nicht gefunden.")
                print("[INFO] Starte automatischen Download... (kann 1-2 Minuten dauern)")

            print("[INFO] Lade YOLOv8n Modell...")

            self.model = YOLO(model_path)
            device = self._get_safe_device()
            self.model.to(device)

            if device == "cuda":
                print("[INFO] NVIDIA GPU aktiviert (CUDA)")
            else:
                print("[INFO] CPU-Modus")

            print("[INFO] Modell erfolgreich geladen!")
            return True

        except Exception as e:
            print(f"[ERROR] Modell konnte nicht geladen werden: {e}")
            return False

    def get_monitor(self):
        mon_index = getattr(settings, "monitor_index", 1)
        if mon_index >= len(self.sct.monitors):
            mon_index = 1
        return self.sct.monitors[mon_index]

    def capture_and_detect(self):
        monitor = self.get_monitor()
        cx, cy = monitor["width"] // 2, monitor["height"] // 2
        size = settings.screenshot_size

        box = {
            "left": cx - size // 2,
            "top": cy - size // 2,
            "width": size,
            "height": size,
        }

        screenshot = self.sct.grab(box)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        if self.model is None:
            return frame, []

        results = self.model(frame, verbose=False)
        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if cls == 0 and conf > settings.confidence:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        detections.append([x1, y1, x2, y2, conf, cls])

        self.detections_count = len(detections)
        return frame, detections

    def process_aim(self, frame, detections):
        if not detections:
            return frame

        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        for det in detections:
            x1, y1, x2, y2, conf, cls = det
            tx = int((x1 + x2) / 2)
            ty = int((y1 + y2) / 2)

            # Triggerbot
            if settings.triggerbot_enabled:
                if (abs(tx - cx) < settings.trigger_width and
                        abs(ty - cy) < settings.trigger_height):
                    now = time.time() * 1000
                    if now - self.last_shot > settings.fire_delay:
                        subprocess.run(["xdotool", "click", "1"],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self.last_shot = now

            # Aim Assist
            if settings.aim_assist_enabled:
                if abs(tx - cx) < 120:
                    move_x = int((tx - cx) * settings.aa_movement_amp * settings.aim_strength)
                    move_y = int((ty - cy) * settings.aa_movement_amp * settings.aim_strength * 0.9)
                    subprocess.run(["xdotool", "mousemove_relative", "--", str(move_x), str(move_y)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if settings.show_boxes:
                color = (0, 255, 65)
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

        return frame


# ====================== GUI ======================
class AimbotGUI:
    def __init__(self):
        self.engine = AimbotEngine()
        self.root = ctk.CTk()
        self.root.title("AI-Aimbot v4 - Matrix")
        self.root.geometry("980x720")
        self.root.configure(fg_color=MATRIX_BG)

        self.running = False
        self.preview_label = None
        self.status_label = None
        self.monitor_var = None
        self.available_monitors = []

        self._detect_monitors()
        self._build_ui()

    def _detect_monitors(self):
        try:
            sct = mss.MSS()
            self.available_monitors = []
            for i, mon in enumerate(sct.monitors[1:], start=1):
                self.available_monitors.append({
                    "index": i,
                    "width": mon["width"],
                    "height": mon["height"],
                })
        except Exception:
            self.available_monitors = [{"index": 1, "width": 1920, "height": 1080}]

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(
            self.root,
            text="▲ AI-AIMBOT v4  •  MATRIX EDITION",
            font=("Consolas", 20, "bold"),
            text_color=MATRIX_GREEN,
        )
        header.pack(pady=15)

        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color=PANEL_BG, corner_radius=8)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel - Controls
        control_frame = ctk.CTkFrame(main_frame, fg_color=MATRIX_DARK, width=320)
        control_frame.pack(side="left", fill="y", padx=10, pady=10)

        # Status
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="● Bereit",
            font=("Consolas", 14),
            text_color=MATRIX_GREEN,
        )
        self.status_label.pack(pady=10)

        # Monitor Selection
        self._create_monitor_dropdown(control_frame)

        # Toggles
        self.trigger_var = ctk.BooleanVar(value=settings.triggerbot_enabled)
        self.aim_var = ctk.BooleanVar(value=settings.aim_assist_enabled)
        self.headshot_var = ctk.BooleanVar(value=settings.headshot_mode)

        ctk.CTkCheckBox(
            control_frame, text="Triggerbot", variable=self.trigger_var,
            command=self._save_settings, text_color=MATRIX_TEXT
        ).pack(pady=6, anchor="w", padx=20)

        ctk.CTkCheckBox(
            control_frame, text="Aim Assist", variable=self.aim_var,
            command=self._save_settings, text_color=MATRIX_TEXT
        ).pack(pady=6, anchor="w", padx=20)

        ctk.CTkCheckBox(
            control_frame, text="Headshot Mode", variable=self.headshot_var,
            command=self._save_settings, text_color=MATRIX_TEXT
        ).pack(pady=6, anchor="w", padx=20)

        # Sliders
        self._create_slider(control_frame, "Confidence", 0.1, 0.8, settings.confidence, "confidence")
        self._create_slider(control_frame, "Aim Strength", 0.05, 0.6, settings.aim_strength, "aim_strength")
        self._create_slider(control_frame, "Screenshot Size", 200, 500, settings.screenshot_size, "screenshot_size", step=10)

        # Buttons
        btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ START AIMBOT",
            fg_color=MATRIX_GREEN_DARK,
            hover_color=MATRIX_GREEN,
            text_color="black",
            font=("Consolas", 14, "bold"),
            command=self.toggle_aimbot,
        )
        self.start_btn.pack(pady=8, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="⟲ RESET",
            fg_color="#1a2a1a",
            text_color=MATRIX_TEXT,
            command=self.reset_settings,
        ).pack(pady=4, fill="x")

        # Preview
        preview_frame = ctk.CTkFrame(main_frame, fg_color=MATRIX_DARK)
        preview_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Preview wird hier angezeigt...",
            font=("Consolas", 12),
            text_color=MATRIX_TEXT_DIM,
        )
        self.preview_label.pack(expand=True)

    def _create_monitor_dropdown(self, parent):
        mon_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mon_frame.pack(pady=10, fill="x", padx=20)

        ctk.CTkLabel(mon_frame, text="Monitor", text_color=MATRIX_TEXT_DIM).pack(anchor="w")

        monitor_options = [
            f"Monitor {m['index']} ({m['width']}x{m['height']})"
            for m in self.available_monitors
        ]

        current = settings.monitor_index
        default_value = monitor_options[current - 1] if current <= len(monitor_options) else monitor_options[0]

        self.monitor_var = ctk.StringVar(value=default_value)

        dropdown = ctk.CTkOptionMenu(
            mon_frame,
            values=monitor_options,
            variable=self.monitor_var,
            command=self._on_monitor_change,
            fg_color="#0f211b",
            button_color=MATRIX_GREEN_DARK,
            button_hover_color=MATRIX_GREEN
        )
        dropdown.pack(fill="x", pady=4)

    def _on_monitor_change(self, choice):
        for m in self.available_monitors:
            if f"Monitor {m['index']}" in choice:
                settings.monitor_index = m["index"]
                save_settings()
                break

    def _create_slider(self, parent, label, min_val, max_val, default, attr, step=0.01):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=8, fill="x", padx=20)

        ctk.CTkLabel(frame, text=label, text_color=MATRIX_TEXT_DIM).pack(anchor="w")

        var = ctk.DoubleVar(value=default)

        def update(val):
            setattr(settings, attr, round(float(val), 2))
            self._save_settings()

        steps = max(1, int((max_val - min_val) / step))
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=steps,
            variable=var,
            command=update,
            button_color=MATRIX_GREEN,
            button_hover_color=MATRIX_GREEN_DARK,
        )
        slider.pack(fill="x")

    def _save_settings(self):
        settings.triggerbot_enabled = self.trigger_var.get()
        settings.aim_assist_enabled = self.aim_var.get()
        settings.headshot_mode = self.headshot_var.get()
        save_settings()

    def reset_settings(self):
        for key, value in DEFAULT_SETTINGS.items():
            setattr(settings, key, value)
        save_settings()
        self.root.destroy()
        self.__init__()
        self.root.mainloop()

    def toggle_aimbot(self):
        if not self.running:
            if self.engine.model is None:
                if not self.engine.load_model():
                    return
            self.running = True
            self.start_btn.configure(text="■ STOP", fg_color="#aa0000")
            self.status_label.configure(text="● AKTIV", text_color=MATRIX_GREEN)
            threading.Thread(target=self._run_loop, daemon=True).start()
        else:
            self.running = False
            self.start_btn.configure(text="▶ START AIMBOT", fg_color=MATRIX_GREEN_DARK)
            self.status_label.configure(text="● Bereit", text_color=MATRIX_GREEN)

    def _run_loop(self):
        while self.running:
            try:
                frame, detections = self.engine.capture_and_detect()
                frame = self.engine.process_aim(frame, detections)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
                self.preview_label.configure(image=ctk_img, text="")

                time.sleep(0.03)
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(0.5)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("AI-Aimbot v4 - Matrix Dark Green Edition (YOLOv8n)")
    app = AimbotGUI()
    app.run()
