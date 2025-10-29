from django.core.management.base import BaseCommand
from decouple import config
from pymongo import MongoClient, ReplaceOne
from pymongo.errors import PyMongoError
from bson.son import SON
import time


SYSTEM_COLLECTION_PREFIX = "system."


def _bool_env(name: str, default: bool = False) -> bool:
    try:
        return config(name, default=default, cast=bool)
    except Exception:
        return default


class Command(BaseCommand):
    help = (
        "Clone all collections from CLOUD MongoDB to LOCAL MongoDB (1:1 upsert).\n"
        "- Reads MONGODB_URI / MONGODB_DATABASE for cloud.\n"
        "- Reads MONGODB_LOCAL_URI / MONGODB_LOCAL_DATABASE for local.\n"
        "- Skips system collections.\n"
        "- Supports dropping local collections first or upserting in batches."
    )

    def add_arguments(self, parser):
        parser.add_argument("--drop-local", action="store_true", help="Drop each local collection before cloning")
        parser.add_argument(
            "--only",
            type=str,
            default=None,
            help="Comma-separated allowlist of collections to clone (default: all user collections)",
        )
        parser.add_argument(
            "--exclude",
            type=str,
            default=None,
            help="Comma-separated list of collections to skip",
        )
        parser.add_argument("--batch-size", type=int, default=1000)
        parser.add_argument("--copy-indexes", action="store_true", help="Copy non-_id_ indexes to local")
        parser.add_argument("--dry-run", action="store_true", help="List what would be done without writing")

    def handle(self, *args, **opts):
        t0 = time.time()

        # Resolve cloud/local URIs and DB names
        cloud_uri = config("MONGODB_URI")
        cloud_dbname = config("MONGODB_DATABASE", default="pos_system")
        local_uri = config("MONGODB_LOCAL_URI", default="mongodb://127.0.0.1:27017")
        local_dbname = config("MONGODB_LOCAL_DATABASE", default="pos_system_local")

        self.stdout.write(self.style.NOTICE(f"Cloud: {cloud_uri} / {cloud_dbname}"))
        self.stdout.write(self.style.NOTICE(f"Local: {local_uri} / {local_dbname}"))

        try:
            cloud = MongoClient(cloud_uri, serverSelectionTimeoutMS=5000)
            cloud.admin.command("ping")
            cdb = cloud[cloud_dbname]
        except PyMongoError as e:
            raise SystemExit(self.style.ERROR(f"Failed to connect to cloud DB: {e}"))

        try:
            local = MongoClient(local_uri, serverSelectionTimeoutMS=5000)
            local.admin.command("ping")
            ldb = local[local_dbname]
        except PyMongoError as e:
            raise SystemExit(self.style.ERROR(f"Failed to connect to local DB: {e}"))

        # Collection selection
        only = set([s.strip() for s in (opts.get("only") or "").split(",") if s.strip()])
        exclude = set([s.strip() for s in (opts.get("exclude") or "").split(",") if s.strip()])

        # List all collections from cloud (skip system.*)
        try:
            cloud_collections = [
                c["name"]
                for c in cdb.list_collections()
                if not c["name"].startswith(SYSTEM_COLLECTION_PREFIX)
            ]
        except TypeError:
            # Older server versions: fall back
            cloud_collections = [
                name for name in cdb.list_collection_names() if not name.startswith(SYSTEM_COLLECTION_PREFIX)
            ]

        if only:
            cloud_collections = [c for c in cloud_collections if c in only]
        if exclude:
            cloud_collections = [c for c in cloud_collections if c not in exclude]

        if not cloud_collections:
            self.stdout.write(self.style.WARNING("No collections selected."))
            return

        self.stdout.write(self.style.NOTICE(f"Collections: {', '.join(sorted(cloud_collections))}"))

        drop_local = bool(opts.get("drop_local"))
        copy_indexes = bool(opts.get("copy_indexes"))
        dry_run = bool(opts.get("dry_run"))
        batch_size = max(1, int(opts.get("batch_size") or 1000))

        total_docs = 0
        for name in cloud_collections:
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE(f"Cloning collection: {name}"))
            src = cdb[name]
            dst = ldb[name]

            if drop_local and not dry_run:
                try:
                    dst.drop()
                    self.stdout.write(self.style.NOTICE("  - Dropped local collection"))
                except PyMongoError as e:
                    self.stdout.write(self.style.WARNING(f"  - Drop failed (continuing): {e}"))

            # Copy index definitions (non _id_)
            if copy_indexes:
                try:
                    for idx in src.list_indexes():
                        name_i = idx.get("name")
                        if not name_i or name_i == "_id_":
                            continue
                        keys = idx.get("key") or idx.get("keys")
                        if not keys:
                            continue
                        # keys may be SON like [(field, direction)]
                        keys_list = list(keys.items()) if isinstance(keys, SON) else list(keys)
                        idx_kwargs = {}
                        for flag in ("unique", "sparse", "expireAfterSeconds", "partialFilterExpression"):
                            if flag in idx:
                                idx_kwargs[flag] = idx[flag]
                        if not dry_run:
                            try:
                                dst.create_index(keys_list, name=name_i, **idx_kwargs)
                            except PyMongoError as e:
                                self.stdout.write(self.style.WARNING(f"  - Index {name_i} skipped: {e}"))
                    if not dry_run:
                        self.stdout.write(self.style.NOTICE("  - Indexes copied"))
                except PyMongoError as e:
                    self.stdout.write(self.style.WARNING(f"  - Could not read indexes: {e}"))

            # Copy documents via bulk upsert
            try:
                estimated = src.estimated_document_count()
            except Exception:
                estimated = None

            self.stdout.write(self.style.NOTICE(f"  - Copying documents (batch={batch_size}, est={estimated})"))

            if dry_run:
                continue

            copied = 0
            ops = []
            try:
                # Use a standard cursor (no noTimeout) to be compatible with Atlas free tiers
                cursor = src.find({}, batch_size=batch_size)
                for doc in cursor:
                    ops.append(ReplaceOne({"_id": doc.get("_id")}, doc, upsert=True))
                    if len(ops) >= batch_size:
                        dst.bulk_write(ops, ordered=False)
                        copied += len(ops)
                        ops = []
                if ops:
                    dst.bulk_write(ops, ordered=False)
                    copied += len(ops)
                try:
                    cursor.close()
                except Exception:
                    pass
            except PyMongoError as e:
                self.stdout.write(self.style.ERROR(f"  - Bulk write failed: {e}"))
                raise SystemExit(1)

            total_docs += copied
            self.stdout.write(self.style.SUCCESS(f"  - Done: {copied} docs"))

        dt = time.time() - t0
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Completed clone: {len(cloud_collections)} collections, {total_docs} docs in {dt:.1f}s"))
        self.stdout.write(self.style.NOTICE("You can now run the backend with FORCE_LOCAL_DB=true to use local DB."))


