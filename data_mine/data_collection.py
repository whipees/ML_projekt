import os
import re
import csv
import time
import requests
from bs4 import BeautifulSoup


class AutoEsaScraper:
    def __init__(self, base_url: str, output_file: str):
        self.base_url = base_url
        self.output_file = output_file
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        self.data = []
        self.seen_signatures = set()

    def fetch_page(self, page_number: int) -> str:
        try:
            url = self.base_url if page_number == 1 else f"{self.base_url}?stranka={page_number}"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error fetching page {page_number}: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error fetching page {page_number}: {e}")

    def parse_price(self, text: str) -> float:
        try:
            match = re.search(r"(\d{1,3}(?:[\s\xa0]\d{3})*)\s*Kč", text, re.IGNORECASE)
            if match:
                clean_val = re.sub(r"[^\d]", "", match.group(1))
                return float(clean_val) * 10
            return 0.0
        except Exception:
            return 0.0

    def parse_year(self, text: str) -> int:
        try:
            match = re.search(r"\b(19[89]\d|20[0-2]\d)\b", text)
            if match:
                return int(match.group(1))
            return 0
        except Exception:
            return 0

    def parse_mileage(self, text: str) -> float:
        try:
            match = re.search(r"(\d{1,3}(?:[\s\xa0]\d{3})*)\s*km", text, re.IGNORECASE)
            if match:
                clean_val = re.sub(r"[^\d]", "", match.group(1))
                return float(clean_val)
            return -1.0
        except Exception:
            return -1.0

    def parse_power(self, text: str) -> float:
        try:
            match = re.search(r"(\d{2,4})\s*kW", text, re.IGNORECASE)
            if match:
                return float(match.group(1))
            return 0.0
        except Exception:
            return 0.0

    def parse_engine_volume(self, text: str) -> float:
        try:
            match = re.search(r"\b([0-9]\.[0-9])\b", text)
            if match:
                return float(match.group(1))
            return 0.0
        except Exception:
            return 0.0

    def extract_cars(self, html: str) -> int:
        try:
            soup = BeautifulSoup(html, "html.parser")
            price_elements = soup.find_all(string=re.compile(r"\d{1,3}(?:[\s\xa0]\d{3})*\s*Kč"))
            count = 0

            for price_elem in price_elements:
                try:
                    container = price_elem.parent
                    valid_container = False

                    for _ in range(6):
                        if not container:
                            break
                        text_content = container.get_text(separator=" ", strip=True)
                        if "km" in text_content and "kW" in text_content and re.search(r"\b20\d{2}\b", text_content):
                            valid_container = True
                            break
                        container = container.parent

                    if not valid_container or not container:
                        continue

                    full_text = container.get_text(separator=" ", strip=True)
                    signature = hash(full_text)

                    if signature in self.seen_signatures:
                        continue

                    price = self.parse_price(full_text)
                    year = self.parse_year(full_text)
                    mileage = self.parse_mileage(full_text)
                    power = self.parse_power(full_text)
                    engine_volume = self.parse_engine_volume(full_text)

                    if price > 10000 and year > 1950 and mileage >= 0 and power > 0:
                        self.data.append({
                            "year": year,
                            "mileage_km": mileage,
                            "power_kw": power,
                            "objem_motoru": engine_volume,
                            "price_czk": price
                        })
                        self.seen_signatures.add(signature)
                        count += 1
                except Exception:
                    continue

            return count
        except Exception as e:
            raise RuntimeError(f"Error parsing HTML: {e}")

    def save_to_csv(self) -> None:
        try:
            if not self.data:
                raise ValueError("No data to save")

            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            fieldnames = ["year", "mileage_km", "power_kw", "objem_motoru", "price_czk"]

            with open(self.output_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for row in self.data:
                    try:
                        writer.writerow(row)
                    except csv.Error:
                        continue
        except OSError as e:
            raise OSError(f"File system error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error saving CSV: {e}")

    def run(self) -> None:
        try:
            page = 1
            empty_pages = 0

            while True:
                try:
                    print(f"Scraping page {page}...")
                    html = self.fetch_page(page)
                    found = self.extract_cars(html)
                    print(f"Found {found} valid cars on page {page}. Total collected: {len(self.data)}")

                    if found == 0:
                        empty_pages += 1
                        if empty_pages >= 3:
                            print("End of catalog reached.")
                            break
                    else:
                        empty_pages = 0

                    if len(self.data) > 3000:
                        print("Sufficient data collected. Stopping scraper.")
                        break

                    page += 1
                    time.sleep(1.0)

                except Exception as e:
                    print(f"Error on page {page}: {e}")
                    page += 1
                    empty_pages += 1
                    if empty_pages >= 4:
                        break

            self.save_to_csv()
        except Exception as e:
            raise RuntimeError(f"Pipeline failed: {e}")


if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_csv = os.path.join(current_dir, "autoesa_dataset.csv")

        target_url = "https://www.autoesa.cz/vsechna-auta"

        scraper = AutoEsaScraper(target_url, output_csv)
        scraper.run()

        print(f"Dataset successfully saved to {output_csv}")
    except Exception as e:
        print(f"Execution failed: {e}")