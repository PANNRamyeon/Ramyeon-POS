from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from app.database import db_manager


class Command(BaseCommand):
    help = "Set email_verified status for a specific user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email address of the user to update",
        )
        parser.add_argument(
            "--verified",
            type=str,
            required=True,
            choices=["True", "False", "true", "false"],
            help="Desired email_verified value (True or False)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        verified = options["verified"].lower() == "true"

        db = db_manager.get_database()
        users_collection = db.users

        user = users_collection.find_one({"email": email})

        if not user:
            self.stdout.write(self.style.ERROR(f"User with email {email} not found"))
            return

        update_payload = {
            "email_verified": verified,
            "last_updated": datetime.now(timezone.utc),
        }

        if verified:
            update_payload["email_verified_at"] = datetime.now(timezone.utc)
        else:
            update_payload["email_verified_at"] = None

        update_operations = {"$set": update_payload}
        if not verified:
            update_operations["$unset"] = {"email_verified_at": ""}

        result = users_collection.update_one({"_id": user["_id"]}, update_operations)

        if result.modified_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully set email_verified={verified} for {email}"
                )
            )
        elif result.matched_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"User found but email_verified was already {verified}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"Failed to update email verification for {email}")
            )

