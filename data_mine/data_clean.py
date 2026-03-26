import os
import csv
from typing import List, Dict


def load_data(filepath: str) -> List[Dict[str, str]]:
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Input file not found: {e}")
    except csv.Error as e:
        raise RuntimeError(f"CSV parsing error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error loading data: {e}")


def filter_data(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    filtered_data = []
    try:
        for row in data:
            try:
                engine_ccm_str = row.get("objem_motoru", "0.0")
                engine_ccm_val = float(engine_ccm_str)

                if engine_ccm_val > 0.0:
                    filtered_data.append(row)
            except ValueError:
                continue
        return filtered_data
    except Exception as e:
        raise RuntimeError(f"Error filtering data: {e}")


def save_data(data: List[Dict[str, str]], filepath: str, fieldnames: List[str]) -> None:
    try:
        if not data:
            raise ValueError("No data to save after filtering.")

        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    except OSError as e:
        raise OSError(f"File system error saving CSV: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error saving CSV: {e}")


if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        input_csv = os.path.join(current_dir, "autoesa_dataset.csv")
        output_csv = os.path.join(current_dir, "autoesa_cleaned.csv")

        print(f"Loading raw data from {input_csv}...")
        raw_dataset = load_data(input_csv)
        print(f"Loaded {len(raw_dataset)} rows.")

        if not raw_dataset:
            raise ValueError("Input dataset is completely empty.")

        columns = list(raw_dataset[0].keys())

        print("Filtering out records with engine_ccm == 0.0...")
        cleaned_dataset = filter_data(raw_dataset)
        print(f"Remaining clean records: {len(cleaned_dataset)}")

        save_data(cleaned_dataset, output_csv, columns)
        print(f"Cleaned dataset successfully saved to {output_csv}")

    except Exception as e:
        print(f"Execution failed: {e}")