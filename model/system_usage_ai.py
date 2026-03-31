import os
import tkinter as tk
import psutil
import joblib
import pandas as pd


class TelemetryLivePredictor:
    def __init__(self, root: tk.Tk, model_path: str):
        self.root = root
        self.root.title("System usage ai predictor")
        self.root.geometry("650x450")
        self.root.configure(bg="#2b2b2b")

        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file {model_path} not found.")
            self.model = joblib.load(model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load AI model: {e}")

        try:
            self.disk_start = psutil.disk_io_counters()
            self.net_start = psutil.net_io_counters()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize sensors: {e}")

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
            1: "[ STATE 1 ]  Klid",
            2: "[ STATE 2 ]  těžká CPU Zátěž",
            3: "[ STATE 3 ]  Síťová zátěž"
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
            text="Hledání senzorů",
            font=("Courier", 11, "bold"),
            bg="#2b2b2b",
            fg="#00ffff"
        )
        self.metrics_lbl.pack(side=tk.BOTTOM, pady=20)

        self.root.after(1000, self.update_telemetry)

    def update_telemetry(self) -> None:
        try:
            cpu_p = psutil.cpu_percent(interval=None)
            ram_p = psutil.virtual_memory().percent

            disk_curr = psutil.disk_io_counters()
            net_curr = psutil.net_io_counters()

            d_read = (disk_curr.read_bytes - self.disk_start.read_bytes) / 1048576.0
            d_write = (disk_curr.write_bytes - self.disk_start.write_bytes) / 1048576.0

            n_sent = (net_curr.bytes_sent - self.net_start.bytes_sent) / 1048576.0
            n_recv = (net_curr.bytes_recv - self.net_start.bytes_recv) / 1048576.0

            self.disk_start = disk_curr
            self.net_start = net_curr

            features = pd.DataFrame([[cpu_p, ram_p, d_read, d_write, n_sent, n_recv]],
                                    columns=[
                                        "cpu_usage_percent",
                                        "ram_usage_percent",
                                        "disk_read_mb",
                                        "disk_write_mb",
                                        "network_sent_mb",
                                        "network_recv_mb"
                                    ])

            prediction = int(self.model.predict(features)[0])

            for s_id, panel in self.ui_panels.items():
                if s_id == prediction:
                    panel.config(bg="#00cc00", fg="black", font=("Arial", 14, "bold"))
                else:
                    panel.config(bg="#404040", fg="#888888", font=("Arial", 14, "normal"))

            metrics_text = f"CPU: {cpu_p:05.1f}% | RAM: {ram_p:05.1f}% | NET IN: {n_recv:05.2f} MB/s"
            self.metrics_lbl.config(text=metrics_text)

        except Exception as e:
            print(f"Polling error: {e}")
        finally:
            self.root.after(1000, self.update_telemetry)


if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_file = os.path.join(current_dir, "system_usage_model.pkl")

        root_window = tk.Tk()
        app = TelemetryLivePredictor(root_window, model_file)
        root_window.mainloop()
    except Exception as e:
        print(f"Application crash: {e}")