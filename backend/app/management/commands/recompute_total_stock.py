from django.core.management.base import BaseCommand
from decouple import config
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime


class Command(BaseCommand):
    help = "Recompute products.total_stock from non-depleted batches and optionally unset legacy stock."

    def add_arguments(self, parser):
        parser.add_argument("--uri", default=None, help="Mongo URI (default: MONGODB_URI)")
        parser.add_argument("--db", default=None, help="Database name (default: MONGODB_DATABASE)")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--unset-stock", action="store_true")
        parser.add_argument("--product", default=None, help="Limit to one product id (PROD-#####)")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **opts):
        uri = opts.get("uri") or config("MONGODB_URI", default=config("MONGODB_LOCAL_URI", default="mongodb://127.0.0.1:27017"))
        db_name = opts.get("db") or config("MONGODB_DATABASE", default=config("MONGODB_LOCAL_DATABASE", default="pos_system_local"))
        dry = bool(opts.get("dry_run"))
        unset_stock = bool(opts.get("unset_stock"))
        prod = opts.get("product")
        limit = opts.get("limit")

        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            db = client[db_name]
        except PyMongoError as e:
            raise SystemExit(self.style.ERROR(f"DB connect failed: {e}"))

        products = db.products
        batches = db.batches

        query = {}
        if prod:
            query["_id"] = prod

        cursor = products.find(query, {"_id": 1, "total_stock": 1, "stock": 1})
        if limit:
            cursor = cursor.limit(int(limit))

        fixed = 0
        scanned = 0
        for p in cursor:
            scanned += 1
            pid = p["_id"]
            current_total = p.get("total_stock")
            legacy_stock = p.get("stock", None)

            active_batches = list(batches.find({
                "product_id": pid,
                "status": {"$ne": "depleted"},
                "quantity_remaining": {"$gt": 0}
            }, {"quantity_remaining": 1}))
            computed = sum(b.get("quantity_remaining", 0) for b in active_batches)

            if dry:
                self.stdout.write(f"{pid}: total_stock={current_total} → {computed} | legacy stock={legacy_stock}")
                continue

            update = {"total_stock": computed, "updated_at": datetime.utcnow()}
            if unset_stock:
                res = products.update_one({"_id": pid}, {"$set": update, "$unset": {"stock": ""}})
            else:
                res = products.update_one({"_id": pid}, {"$set": update})
            fixed += res.modified_count

        self.stdout.write(self.style.SUCCESS(f"Scanned {scanned}, updated {fixed} products"))


