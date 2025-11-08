"""
Shift summary email service for the POS system.

Generates the data needed for shift summary emails and sends them to all
verified administrators whenever a shift is closed.
"""
import logging
from datetime import datetime, timezone
from decouple import config
from app.database import db_manager
from notifications.email_service import email_service

logger = logging.getLogger(__name__)


class ShiftSummaryService:
    """Helper service that prepares and sends shift summary emails."""

    def __init__(self):
        self.db = db_manager.get_database()
        self.user_collection = self.db.users
        self.shift_collection = self.db.shifts

    def _format_datetime(self, dt):
        if not dt:
            return 'N/A'

        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return dt

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc).strftime('%b %d, %Y %I:%M %p %Z')

    def _format_duration(self, start, end):
        if not start or not end:
            return 'N/A'

        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace('Z', '+00:00'))

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        total_seconds = int((end - start).total_seconds())
        if total_seconds < 0:
            total_seconds = abs(total_seconds)

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours and minutes:
            return f"{hours}h {minutes}m"
        if hours:
            return f"{hours}h"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def _get_cashier_display_name(self, cashier_id):
        if not cashier_id:
            return 'Unknown'

        user = self.user_collection.find_one({"_id": cashier_id})
        if not user:
            return cashier_id

        return user.get('full_name') or user.get('username') or cashier_id

    def get_verified_admin_emails(self):
        """
        Fetch verified admin email addresses.

        Returns:
            list[str]: Unique list of verified admin emails.
        """
        try:
            admins = list(self.user_collection.find({
                "role": "admin",
                "status": "active",
                "isDeleted": {"$ne": True},
                "email_verified": True
            }))

            emails = []
            for admin in admins:
                email = admin.get("email")
                if email and email not in emails:
                    emails.append(email)

            # Include any additional recipients specified via environment variable
            additional_recipients = config("SHIFT_SUMMARY_ADMIN_EMAILS", default="")
            if additional_recipients:
                for raw_email in additional_recipients.split(","):
                    email = raw_email.strip()
                    if email and email not in emails:
                        emails.append(email)

            logger.info("ShiftSummaryService: Found %s verified admin email(s)", len(emails))
            return emails

        except Exception as exc:
            logger.error("ShiftSummaryService: Error fetching admin emails: %s", exc)
            return []

    def build_shift_summary_payload(self, shift_doc):
        """
        Prepare the payload sent to the email template.
        """
        if not shift_doc:
            raise ValueError("Shift document is required to build summary payload.")

        shift_id = shift_doc.get('_id', 'N/A')
        start_time = shift_doc.get('start_time')
        end_time = shift_doc.get('end_time')

        summary = {
            "shift_id": shift_id,
            "cashier_name": self._get_cashier_display_name(shift_doc.get('cashier_id')),
            "shift_start": self._format_datetime(start_time),
            "shift_end": self._format_datetime(end_time),
            "session_duration": self._format_duration(start_time, end_time),
            "total_sales": float(shift_doc.get('total_sales', 0) or 0),
            "total_transactions": int(shift_doc.get('total_transactions', 0) or 0),
            "opening_cash": float(shift_doc.get('opening_cash', 0) or 0),
            "closing_cash": float(shift_doc.get('closing_cash', 0) or 0),
            "expected_cash": float(shift_doc.get('expected_cash', 0) or 0),
            "cash_variance": float(shift_doc.get('cash_variance', 0) or 0),
            "payment_breakdown": shift_doc.get('payment_breakdown', {}) or {},
        }

        return summary

    def send_shift_summary_email(self, shift_doc):
        """
        Send the shift summary email to all verified admins.
        """
        try:
            admin_emails = self.get_verified_admin_emails()
            if not admin_emails:
                logger.warning("ShiftSummaryService: No verified admin emails found; skipping email send.")
                return {
                    "success": False,
                    "error": "No verified admin emails found",
                    "sent_count": 0,
                    "results": []
                }

            summary_payload = self.build_shift_summary_payload(shift_doc)
            results = []

            for email in admin_emails:
                admin = self.user_collection.find_one({"email": email})
                admin_name = admin.get('full_name') or admin.get('username', 'Admin') if admin else 'Admin'
                send_result = email_service.send_shift_summary_email(
                    to_email=email,
                    shift_data=summary_payload,
                    admin_name=admin_name
                )

                results.append({
                    "email": email,
                    "success": send_result.get('success', False),
                    "error": send_result.get('error')
                })

                if send_result.get('success'):
                    logger.info("ShiftSummaryService: Shift summary sent to %s", email)
                else:
                    logger.error(
                        "ShiftSummaryService: Failed to send shift summary to %s: %s",
                        email,
                        send_result.get('error')
                    )

            sent_count = sum(1 for result in results if result.get('success'))
            return {
                "success": sent_count > 0,
                "sent_count": sent_count,
                "results": results
            }

        except Exception as exc:
            logger.error("ShiftSummaryService: Error sending shift summary email: %s", exc, exc_info=True)
            return {
                "success": False,
                "error": str(exc)
            }


shift_summary_service = ShiftSummaryService()

