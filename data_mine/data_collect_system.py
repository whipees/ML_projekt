import os
import csv
import time
import psutil


class SystemTelemetryCollector:
    def __init__(self, output_file: str):
        self.output_file = output_file
        self.headers = [
            "label_id",
            "cpu_usage_percent",
            "ram_usage_percent",
            "disk_read_mb",
            "disk_write_mb",
            "network_sent_mb",
            "network_recv_mb"
        ]

    def init_csv(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            if not os.path.exists(self.output_file):
                with open(self.output_file, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.headers)
        except OSError as e:
            raise OSError(f"File system error initializing CSV: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error initializing CSV: {e}")

    def collect_data(self, label_id: int, duration_seconds: int) -> None:
        try:
            self.init_csv()

            try:
                disk_start = psutil.disk_io_counters()
                net_start = psutil.net_io_counters()
                if not disk_start or not net_start:
                    raise RuntimeError("Failed to read initial hardware counters.")
            except Exception as e:
                raise RuntimeError(f"Hardware sensor initialization failed: {e}")

            print(f"Starting hardware telemetry collection for label ID: {label_id}")
            print(f"Duration: {duration_seconds} seconds. Please perform the requested activity.")

            for i in range(duration_seconds):
                try:
                    time.sleep(1)

                    cpu_percent = psutil.cpu_percent(interval=None)
                    ram_percent = psutil.virtual_memory().percent

                    disk_current = psutil.disk_io_counters()
                    net_current = psutil.net_io_counters()

                    if not disk_current or not net_current:
                        continue

                    disk_read_mb = (disk_current.read_bytes - disk_start.read_bytes) / (1024 * 1024)
                    disk_write_mb = (disk_current.write_bytes - disk_start.write_bytes) / (1024 * 1024)

                    net_sent_mb = (net_current.bytes_sent - net_start.bytes_sent) / (1024 * 1024)
                    net_recv_mb = (net_current.bytes_recv - net_start.bytes_recv) / (1024 * 1024)

                    disk_start = disk_current
                    net_start = net_current

                    row = [
                        label_id,
                        round(cpu_percent, 2),
                        round(ram_percent, 2),
                        round(disk_read_mb, 4),
                        round(disk_write_mb, 4),
                        round(net_sent_mb, 4),
                        round(net_recv_mb, 4)
                    ]

                    with open(self.output_file, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(row)

                    print(
                        f"[{i + 1}/{duration_seconds}] Logged: CPU {cpu_percent}% | NET Recv {round(net_recv_mb, 2)}MB")

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(f"Permission error accessing system metrics: {e}")
                    continue
                except csv.Error as e:
                    print(f"Error writing to CSV: {e}")
                    continue
                except KeyboardInterrupt:
                    print("\nData collection manually interrupted by user.")
                    break
                except Exception as e:
                    print(f"Unexpected error during data polling: {e}")
                    continue

        except Exception as e:
            raise RuntimeError(f"Data collection pipeline failed: {e}")


if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_csv = os.path.join(current_dir, "telemetry_dataset.csv")

        print("=== OS Telemetry AI Profiler ===")
        print("1 = Klid / Kancelář (Idle, čtení textu, Word)")
        print("2 = Hraní / Náročný program (CPU zátěž, rendering, zipování obří složky)")
        print("3 = Síťová zátěž (Stahování velkého souboru, test rychlosti internetu)")

        try:
            user_label = int(input("Enter activity ID (1-3): "))
            user_duration = int(input("Enter collection duration in seconds: "))
        except ValueError:
            raise ValueError("Invalid input. Must be an integer.")

        collector = SystemTelemetryCollector(output_csv)
        collector.collect_data(user_label, user_duration)

        print(f"Collection complete. Data saved to {output_csv}")
    except Exception as e:
        print(f"Application terminated with error: {e}")