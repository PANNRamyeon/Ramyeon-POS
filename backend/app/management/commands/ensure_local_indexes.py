from django.core.management.base import BaseCommand
from decouple import config
from pymongo import MongoClient
from pymongo.errors import PyMongoError


INDEX_PLANS = {
    "products": [
        {"keys": [("sku", 1)], "name": "sku_idx"},
        {"keys": [("updated_at", -1)], "name": "updated_at_desc"},
        {"keys": [("name", "text")], "name": "name_text", "optional": True},
        # Compound index to accelerate category page loads
        {"keys": [("category_id", 1), ("isDeleted", 1), ("total_stock", -1), ("product_name", 1)], "name": "cat_deleted_total_name"},
    ],
    "batches": [
        {"keys": [("product_id", 1), ("created_at", 1)], "name": "prod_created"},
        {"keys": [("product_id", 1), ("expiry_date", 1)], "name": "prod_expiry"},
    ],
    "category": [
        {"keys": [("name", 1)], "name": "name_idx"},
    ],
    "users": [
        {"keys": [("email", 1)], "name": "email_idx"},
        {"keys": [("role", 1), ("status", 1)], "name": "role_status"},
    ],
    "customers": [
        {"keys": [("email", 1)], "name": "email_idx"},
        {"keys": [("phone", 1)], "name": "phone_idx"},
    ],
    "shifts": [
        {"keys": [("status", 1)], "name": "status_idx"},
        {"keys": [("cashier_id", 1), ("status", 1)], "name": "cashier_status"},
        {"keys": [("next_seq", 1)], "name": "next_seq_idx"},
    ],
    "sales": [
        {"keys": [("transaction_date", -1)], "name": "tx_date_desc"},
        {"keys": [("cashier_id", 1), ("transaction_date", -1)], "name": "cashier_date"},
        {"keys": [("shift_id", 1), ("transaction_date", 1)], "name": "shift_date"},
        {"keys": [("shift_id", 1), ("shift_seq", 1)], "name": "shift_seq_unique", "unique": False},
        {"keys": [("sync_state", 1)], "name": "sync_state_idx"},
    ],
}


class Command(BaseCommand):
    help = "Ensure essential indexes exist in the local MongoDB (and optionally cloud)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--uri",
            dest="uri",
            default=None,
            help="Local Mongo URI (default: env MONGODB_LOCAL_URI)",
        )
        parser.add_argument(
            "--db",
            dest="db_name",
            default=None,
            help="Local DB name (default: env MONGODB_LOCAL_DATABASE)",
        )
        parser.add_argument(
            "--collections",
            dest="collections",
            default=None,
            help="Comma-separated list; default applies to all planned collections",
        )
        parser.add_argument(
            "--unique-shift-seq",
            action="store_true",
            help="Make (shift_id, shift_seq) unique (fails if duplicates exist)",
        )

    def handle(self, *args, **opts):
        uri = opts.get("uri") or config("MONGODB_LOCAL_URI", default="mongodb://127.0.0.1:27017")
        db_name = opts.get("db_name") or config("MONGODB_LOCAL_DATABASE", default="pos_system_local")
        collections_arg = opts.get("collections")
        only = None
        if collections_arg:
            only = set([s.strip() for s in collections_arg.split(",") if s.strip()])

        self.stdout.write(self.style.NOTICE(f"Ensuring indexes on local: {uri} / {db_name}"))

        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            db = client[db_name]
        except PyMongoError as e:
            raise SystemExit(self.style.ERROR(f"Local MongoDB connection failed: {e}"))

        unique_shift_seq = bool(opts.get("unique_shift_seq"))

        created = 0
        skipped = 0

        for coll_name, plans in INDEX_PLANS.items():
            if only and coll_name not in only:
                continue

            coll = db[coll_name]
            self.stdout.write(self.style.NOTICE(f"Collection: {coll_name}"))

            try:
                existing = {idx.get("name") for idx in coll.list_indexes()}
            except Exception:
                existing = set()

            for plan in plans:
                name = plan.get("name")
                keys = plan.get("keys")
                if not name or not keys:
                    continue

                # Handle special toggle for unique shift_seq
                kwargs = {}
                if name == "shift_seq_unique":
                    if unique_shift_seq:
                        kwargs["unique"] = True
                    else:
                        kwargs["unique"] = False

                for flag in ("unique", "sparse", "expireAfterSeconds", "partialFilterExpression"):
                    if flag in plan:
                        kwargs[flag] = plan[flag]

                if name in existing:
                    skipped += 1
                    continue

                try:
                    coll.create_index(keys, name=name, **kwargs)
                    created += 1
                except PyMongoError as e:
                    self.stdout.write(self.style.WARNING(f"  - Index '{name}' skipped: {e}"))
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(f"Indexes created: {created}, skipped: {skipped}"))



