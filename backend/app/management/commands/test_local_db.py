from django.core.management.base import BaseCommand
from decouple import config
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import json


class Command(BaseCommand):
    help = "Test connectivity to the local MongoDB and show collections."

    def add_arguments(self, parser):
        parser.add_argument(
            "--uri",
            dest="uri",
            default=None,
            help="Mongo URI to test (overrides MONGODB_LOCAL_URI)",
        )
        parser.add_argument(
            "--db",
            dest="db_name",
            default=None,
            help="Database name to use (overrides MONGODB_LOCAL_DATABASE)",
        )

    def handle(self, *args, **options):
        uri = options.get("uri") or config(
            "MONGODB_LOCAL_URI", default="mongodb://127.0.0.1:27017"
        )
        db_name = options.get("db_name") or config(
            "MONGODB_LOCAL_DATABASE", default="pos_system_local"
        )

        self.stdout.write(self.style.NOTICE(f"Testing local MongoDB: {uri} / {db_name}"))

        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            db = client[db_name]
            collections = db.list_collection_names()

            info = {
                "ok": True,
                "db": db_name,
                "collections": collections,
            }

            self.stdout.write(self.style.SUCCESS(json.dumps(info, indent=2)))

            self.stdout.write("")
            self.stdout.write(
                self.style.NOTICE(
                    "To force the backend to use local DB for this session:"
                )
            )
            self.stdout.write(
                "  PowerShell:\n"
                "    $env:FORCE_LOCAL_DB='true'\n"
                "    $env:MONGODB_LOCAL_URI='%s'\n"
                "    $env:MONGODB_LOCAL_DATABASE='%s'\n"
                "    python backend/manage.py runserver 0.0.0.0:8000\n"
                % (uri, db_name)
            )

        except PyMongoError as e:
            self.stderr.write(self.style.ERROR(f"Local MongoDB connection failed: {e}"))
            self.stderr.write(
                "Check that mongod is running and that your URI/DB name are correct."
            )
            raise SystemExit(1)


