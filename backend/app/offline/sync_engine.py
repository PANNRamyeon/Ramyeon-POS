import threading, time, json, os
from datetime import datetime
from app.database import db_manager
from app.offline.data_queue import OfflineFileQueue
from app.offline.connectivity import Connectivity

ARCHIVE_DIR = os.getenv("OFFLINE_ARCHIVE_DIR", "backend/archive")

class SyncEngine:
    """
    Periodically syncs offline sales (from Data.json) to the cloud when online,
    and pulls updated products/categories if needed.
    """

    def __init__(self, net: Connectivity, interval_minutes=30):
        self.net = net
        self.cloud = db_manager.get_database()
        self.interval = max(5, interval_minutes)  # minutes
        self._stop = False
        self._thread = None

        # subscribe to connectivity changes
        self.net.on_online(self.on_online)
        self.net.on_offline(self.on_offline)

    def _archive(self, kind: str, doc: dict):
        """Append logs to NDJSON archive."""
        day = datetime.utcnow().strftime("%Y-%m-%d")
        folder = os.path.join(ARCHIVE_DIR, day)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{kind}.ndjson")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(doc, default=str) + "\n")

    def pull_catalog(self):
        """Optional: refresh products & categories from cloud."""
        try:
            self.cloud.products.find_one()
            self.cloud.category.find_one()
        except Exception as e:
            print(f"⚠️ Failed to pull catalog: {e}")

    def push_sales(self):
        """Sync offline Data.json sales to API endpoint."""
        import requests
        from app.offline.data_queue import OfflineFileQueue

        offline_sales = OfflineFileQueue.get_all_sales()
        if not offline_sales:
            return

        print(f"🔄 Syncing {len(offline_sales)} offline sale(s) to API endpoint...")

        # ✅ Archive Data.json before syncing
        day = datetime.utcnow().strftime("%Y-%m-%d")
        archive_folder = os.path.join(ARCHIVE_DIR, day)
        os.makedirs(archive_folder, exist_ok=True)
        archive_path = os.path.join(archive_folder, f"offline_sales_synced_backup_{day}.ndjson")

        with open(archive_path, "a", encoding="utf-8") as f:
            for sale in offline_sales:
                f.write(json.dumps(sale, default=str) + "\n")

        print(f"🗃️ Archived offline sales to {archive_path}")

        # ✅ Step 2: Sync each sale via API
        synced_sales = []
        api_url = os.getenv("SYNC_SALES_URL", "http://127.0.0.1:8000/api/v1/pos/sales/create/")

        for sale in offline_sales:
            sale_id = sale.get("_id", "UNKNOWN-ID")
            try:
                print(f"📤 Sending {sale_id} to API...")
                response = requests.post(api_url, json=sale, timeout=15)
                if response.status_code in (200, 201):
                    print(f"✅ Synced {sale_id} successfully through API.")
                    self._archive("offline_sales_synced", {"sale_id": sale_id, "ts": datetime.utcnow()})
                    synced_sales.append(sale)
                else:
                    print(f"⚠️ API rejected sale {sale_id}: {response.status_code} | {response.text}")
                    self._archive("offline_sales_errors", {
                        "sale_id": sale_id,
                        "error": response.text,
                        "ts": datetime.utcnow()
                    })
            except Exception as e:
                print(f"❌ Failed to sync {sale_id}: {e}")
                self._archive("offline_sales_errors", {
                    "sale_id": sale_id,
                    "error": str(e),
                    "ts": datetime.utcnow()
                })

        # ✅ Step 3: Remove synced sales from Data.json
        if synced_sales:
            print(f"🧹 {len(synced_sales)} sale(s) synced. Clearing from Data.json...")
            OfflineFileQueue.clear_sales()



    def on_online(self):
        """Triggered when connection returns."""
        self.push_sales()
        self.pull_catalog()

    def on_offline(self):
        """Triggered when connection drops."""
        print("📴 Offline mode: sales will be saved locally to Data.json")

    def start(self):
        """Start periodic sync thread."""
        if self._thread:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop background thread."""
        self._stop = True
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self):
        """Periodic task loop."""
        if self.net.is_online():
            self.pull_catalog()

        while not self._stop:
            time.sleep(self.interval * 60)
            if self.net.is_online():
                self.push_sales()
