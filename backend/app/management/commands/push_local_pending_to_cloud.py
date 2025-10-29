from django.core.management.base import BaseCommand
from app.offline.local_sync import push_pending_sales


class Command(BaseCommand):
    help = "Push local pending sales to cloud in (shift_id, shift_seq) order."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Max documents to push this run")

    def handle(self, *args, **opts):
        limit = opts.get("limit")
        summary = push_pending_sales(limit)
        self.stdout.write(self.style.SUCCESS(f"Pushed: {summary['success']} | Failed: {summary['failed']} | Total: {summary['total']}"))



