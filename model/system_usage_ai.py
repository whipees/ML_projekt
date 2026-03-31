import os
import tkinter as tk
import psutil
import joblib
import pandas as pd
import threading
import time
from datetime import datetime


class TelemetryLivePredictor:
    def __init__(self, root: tk.Tk, model_path: str):
        self.root = root
        self.root.title("AI OS Usage Profiler")
        self.root.geometry("650x450")
        self.root.configure(bg="#2b2b2b")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.running = True
        self.current_prediction = 1
        self.last_logged_state = 1
        self.metrics_text = "Initializing sensors..."

        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file {model_path} not found.")
            self.model = joblib.load(model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load AI model: {e}")

        self.title_lbl = tk.Label(
            self.root,
            text="Live AI Activity Detection",
            font=("Arial", 18, "bold"),
            bg="#2b2b2b",
            fg="white"
        )
        self.title_lbl.pack(pady=20)

        self.ui_panels = {}
        state_config = {
            1: "[ STATE 1 ]  Idle / Office Work",
            2: "[ STATE 2 ]  Heavy CPU Load / Rendering",
            3: "[ STATE 3 ]  Network Download / Stream"
        }

        for s_id, text in state_config.items():
            lbl = tk.Label(
                self.root,
                text=text,
                font=("Arial", 14),
                bg="#404040",
                fg="#888888",
                width=45,
                pady=15
            )
            lbl.pack(pady=10)
            self.ui_panels[s_id] = lbl

        self.metrics_lbl = tk.Label(
            self.root,
            text=self.metrics_text,
            font=("Courier", 11, "bold"),
            bg="#2b2b2b",
            fg="#00ffff"
        )
        self.metrics_lbl.pack(side=tk.BOTTOM, pady=20)

        self.sensor_thread = threading.Thread(target=self.poll_sensors, daemon=True)
        self.sensor_thread.start()

        self.root.after(100, self.update_ui)

    def log_alert(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] ALERT: {message}\n"

        try:
            with open("security_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(log_entry)
            print(log_entry.strip())
        except Exception as e:
            print(f"Failed to write log: {e}")

    def poll_sensors(self) -> None:
        try:
            disk_start = psutil.disk_io_counters()
            net_start = psutil.net_io_counters()
        except Exception as e:
            print(f"Failed to initialize sensors: {e}")
            return

        while self.running:
            try:
                time.sleep(1.0)

                cpu_p = psutil.cpu_percent(interval=None)
                ram_p = psutil.virtual_memory().percent

                disk_curr = psutil.disk_io_counters()
                net_curr = psutil.net_io_counters()

                d_read = (disk_curr.read_bytes - disk_start.read_bytes) / 1048576.0
                d_write = (disk_curr.write_bytes - disk_start.write_bytes) / 1048576.0

                n_sent = (net_curr.bytes_sent - net_start.bytes_sent) / 1048576.0
                n_recv = (net_curr.bytes_recv - net_start.bytes_recv) / 1048576.0

                disk_start = disk_curr
                net_start = net_curr

                features = pd.DataFrame([[cpu_p, ram_p, d_read, d_write, n_sent, n_recv]],
                                        columns=[
                                            "cpu_usage_percent",
                                            "ram_usage_percent",
                                            "disk_read_mb",
                                            "disk_write_mb",
                                            "network_sent_mb",
                                            "network_recv_mb"
                                        ])

                self.current_prediction = int(self.model.predict(features)[0])
                self.metrics_text = f"CPU: {cpu_p:05.1f}% | RAM: {ram_p:05.1f}% | NET IN: {n_recv:05.2f} MB/s"

                if self.current_prediction != 1 and self.current_prediction != self.last_logged_state:
                    if self.current_prediction == 2:
                        self.log_alert(f"Detekováno abnormální vytížení CPU ({cpu_p} %)")
                    elif self.current_prediction == 3:
                        self.log_alert(f"Detekován masivní síťový tok (Stahování {n_recv:.2f} MB/s)")

                self.last_logged_state = self.current_prediction

            except Exception as e:
                print(f"Polling error: {e}")

    def update_ui(self) -> None:
        if not self.running:
            return

        for s_id, panel in self.ui_panels.items():
            if s_id == self.current_prediction:
                panel.config(bg="#00cc00", fg="black", font=("Arial", 14, "bold"))
            else:
                panel.config(bg="#404040", fg="#888888", font=("Arial", 14, "normal"))

        self.metrics_lbl.config(text=self.metrics_text)
        self.root.after(100, self.update_ui)

    def on_closing(self) -> None:
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_file = os.path.join(current_dir, "system_usage_model.pkl")

        root_window = tk.Tk()
        app = TelemetryLivePredictor(root_window, model_file)
        root_window.mainloop()
    except Exception as e:
        print(f"Application crash: {e}")