import os, json, re
from app.offline.data_queue import LOCK  # IMPORT THE LOCK

DATA_FILE = os.path.join("backend", "offline", "Data.json")

class OfflineIDGenerator:
    """
    Generates sequential SALE-###### IDs for offline mode
    based on existing entries in Data.json.
    """

    def __init__(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def generate_sale_id(self):
        """Scan Data.json and generate next SALE-###### ID with thread safety."""
        with LOCK:  # ADDED LOCK FOR THREAD SAFETY
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    try:
                        sales = json.load(f)
                    except json.JSONDecodeError:
                        sales = []

                ids = [
                    int(re.search(r"SALE-(\d+)", s.get("_id", "")).group(1))
                    for s in sales if re.search(r"SALE-(\d+)", s.get("_id", ""))
                ]

                next_number = max(ids) + 1 if ids else 1
                return f"SALE-{next_number:06d}"

            except Exception:
                return "SALE-000001"