from datetime import datetime, timezone
from app.offline.connectivity import Connectivity
from app.offline.data_queue import OfflineFileQueue
from app.offline.offline_id_generator import OfflineIDGenerator
from app.database import db_manager

class POSSaleAdapter:
    """
    Adapter that handles POS sales creation logic for both
    online (MongoDB Atlas) and offline (local Data.json) modes.
    """

    def __init__(self, connectivity: Connectivity):
        self.net = connectivity
        self.cloud = db_manager.get_database()

    def create_cash_sale(self, sale_data: dict, cashier_id: str):
        """Handles online/offline sale logic for POS."""
        from app.services.POS.pos_sales_service import POSSalesService

        payment_method = sale_data.get("payment_method", "cash").lower()
        if payment_method != "cash":
            raise Exception("Offline mode supports cash sales only.")

        sale_data["cashier_id"] = cashier_id

        # Add standard fields
        sale_data.setdefault("status", "completed")
        sale_data.setdefault("source", "pos")
        sale_data.setdefault("is_voided", False)
        sale_data.setdefault("points_awarded", False)
        sale_data.setdefault("transaction_date", datetime.now(timezone.utc).isoformat())
        sale_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        sale_data.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

        if not self.net.is_online():
            # 🔹 OFFLINE MODE: Save to Data.json
            from app.offline.data_queue import OfflineFileQueue
            from app.offline.offline_id_generator  import OfflineIDGenerator

            generator = OfflineIDGenerator()  # ID generation based on file
            sale_data["_id"] = generator.generate_sale_id()

            OfflineFileQueue.add_sale(sale_data)
            return {
                "offline": True,
                "data": sale_data,
                "message": f"Sale stored offline (Data.json): {sale_data['_id']}"
            }

        # 🔹 ONLINE MODE: Normal cloud process
        service = POSSalesService()
        result = service.create_sale(sale_data, cashier_id)

        return {
            "offline": False,
            "data": result.get("data", {}),
            "message": "Sale created online"
        }
