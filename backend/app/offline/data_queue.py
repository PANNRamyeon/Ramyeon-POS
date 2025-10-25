import os, json, threading
from datetime import datetime, timezone

DATA_FILE = os.path.join("backend", "offline", "Data.json")
LOCK = threading.Lock()

class OfflineFileQueue:
    """Handles writing and reading offline sales identical to cloud schema."""

    @staticmethod
    def _ensure_file():
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    @staticmethod
    def add_sale(sale_doc: dict):
        """
        Append a new sale to the offline Data.json file.
        Ensures consistent structure with cloud sales collection.
        """
        OfflineFileQueue._ensure_file()

        # Ensure proper sale structure
        sale_doc.setdefault("status", "completed")
        sale_doc.setdefault("source", "pos")
        sale_doc.setdefault("is_voided", False)
        sale_doc.setdefault("points_awarded", False)
        sale_doc.setdefault("transaction_date", datetime.now(timezone.utc).isoformat())
        sale_doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        sale_doc.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

        # Payment structure
        if "payment_details" not in sale_doc:
            sale_doc["payment_details"] = {
                "method": sale_doc.get("payment_method", "cash"),
                "amount_paid": sale_doc.get("total_amount", 0),
                "change": 0
            }

        with LOCK:
            with open(DATA_FILE, "r+", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

                sale_doc["queued_at"] = datetime.utcnow().isoformat()
                data.append(sale_doc)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()

    @staticmethod
    def get_all_sales():
        """Return all queued offline sales."""
        OfflineFileQueue._ensure_file()
        with LOCK:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []

    @staticmethod
    def clear_sales():
        """Erase queued sales after successful sync."""
        with LOCK:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
