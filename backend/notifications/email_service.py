"""
Email service for SendGrid integration.

Provides helper methods for sending transactional emails from the POS system,
including shift summary emails for administrators.
"""
import logging
from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


class EmailService:
    """Wrapper around SendGrid for sending transactional emails."""

    def __init__(self):
        self.api_key = config('SENDGRID_API_KEY', default='')
        self.from_email = config('SENDGRID_FROM_EMAIL', default='test@example.com')
        self.from_name = config('SENDGRID_FROM_NAME', default='PANN POS System')
        self.sg = None

        if self.api_key:
            try:
                self.sg = SendGridAPIClient(self.api_key)
            except Exception as exc:
                logger.error("Failed to initialize SendGrid client: %s", exc)
        else:
            logger.warning("SENDGRID_API_KEY is not set. Email sending will be disabled.")

    def send_email(self, to_email, subject, html_content, plain_text_content=None):
        """
        Send an email through SendGrid.

        Args:
            to_email (str): Recipient email address.
            subject (str): Email subject line.
            html_content (str): HTML content for the email.
            plain_text_content (str, optional): Plain text fallback content.

        Returns:
            dict: Result payload indicating success or error details.
        """
        if not self.sg:
            logger.error("SendGrid client not initialized. Cannot send email.")
            return {
                'success': False,
                'error': 'SendGrid client not initialized'
            }

        if not to_email:
            logger.error("Recipient email is required to send email.")
            return {
                'success': False,
                'error': 'Recipient email is required'
            }

        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if plain_text_content:
                message.plain_text_content = Content("text/plain", plain_text_content)

            # ✅ Add Reply-To header
            message.reply_to = Email(self.from_email, self.from_name)
            
            # ✅ Add categories for SendGrid tracking
            message.add_category("shift-summary")
            message.add_category("transactional")
            
            # ✅ Add custom headers to improve deliverability
            # Note: SendGrid Mail object uses header property, not add_header method
            from sendgrid.helpers.mail import Header
            message.header = Header("X-Mailer", "PANN POS System")
            message.header = Header("X-Priority", "3")  # Normal priority
            message.header = Header("X-MSMail-Priority", "Normal")
            
            # ✅ Add List-Unsubscribe header (best practice even for transactional emails)
            unsubscribe_url = config('EMAIL_UNSUBSCRIBE_URL', default='')
            if unsubscribe_url:
                message.header = Header("List-Unsubscribe", f"<{unsubscribe_url}>")
                message.header = Header("List-Unsubscribe-Post", "List-Unsubscribe=One-Click")

            response = self.sg.send(message)
            status_code = response.status_code

            if status_code in (200, 201, 202):
                logger.info("Email sent successfully to %s. Status: %s", to_email, status_code)
                return {
                    'success': True,
                    'message': 'Email sent successfully',
                    'status_code': status_code
                }

            error_body = response.body.decode('utf-8') if response.body else 'No error details'
            logger.error(
                "Failed to send email to %s. Status: %s. Body: %s",
                to_email,
                status_code,
                error_body
            )
            return {
                'success': False,
                'status_code': status_code,
                'error': f'Failed to send email. Details: {error_body}'
            }

        except Exception as exc:
            logger.error("Error sending email to %s: %s", to_email, exc)
            return {
                'success': False,
                'error': str(exc)
            }

    def send_shift_summary_email(self, to_email, shift_data, admin_name=None):
        """
        Send a shift summary email when a POS shift is closed.

        Args:
            to_email (str): Recipient email.
            shift_data (dict): Summary payload with the following keys:
                - shift_id (str)
                - cashier_name (str)
                - shift_start (str)
                - shift_end (str)
                - session_duration (str)
                - total_sales (float)
                - total_transactions (int)
                - opening_cash (float, optional)
                - closing_cash (float, optional)
                - expected_cash (float, optional)
                - cash_variance (float, optional)
                - payment_breakdown (dict, optional)
            admin_name (str, optional): Name of the admin for personalization.

        Returns:
            dict: Result payload from the email send attempt.
        """
        subject = (
            f"Daily Shift Report: {shift_data.get('shift_id', '')} - "
            f"{shift_data.get('cashier_name', 'Unknown')}"
        ).strip()

        total_sales = shift_data.get('total_sales', 0)
        formatted_sales = (
            f"₱{total_sales:,.2f}" if isinstance(total_sales, (int, float)) else str(total_sales)
        )

        def format_currency(value):
            if isinstance(value, (int, float)):
                return f"₱{value:,.2f}"
            return value if value is not None else 'N/A'

        payment_breakdown = shift_data.get('payment_breakdown', {})
        payment_rows = "".join(
            f"""
            <div class="summary-item">
                <span class="summary-label">{method.upper()} Sales:</span>
                <span class="summary-value">{format_currency(amount)}</span>
            </div>
            """
            for method, amount in payment_breakdown.items()
        )

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <title>Shift Summary Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 640px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    border-radius: 8px;
                    padding: 30px;
                    margin: 20px 0;
                }}
                .header {{
                    background-color: #2196F3;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .summary-box {{
                    background-color: #f5f5f5;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .summary-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #ddd;
                }}
                .summary-item:last-child {{
                    border-bottom: none;
                }}
                .summary-label {{
                    font-weight: 600;
                    color: #555;
                }}
                .summary-value {{
                    color: #333;
                    font-size: 1.05em;
                }}
                .total-sales {{
                    font-size: 1.5em;
                    color: #4CAF50;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Shift Summary Report</h1>
                </div>
                <div class="content">
                    <p>Hello {admin_name or 'Admin'},</p>
                    <p>The following shift has been closed. Here are the details:</p>

                    <div class="summary-box">
                        <div class="summary-item">
                            <span class="summary-label">Shift ID:</span>
                            <span class="summary-value">{shift_data.get('shift_id', 'N/A')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Cashier:</span>
                            <span class="summary-value">{shift_data.get('cashier_name', 'Unknown')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Shift Start:</span>
                            <span class="summary-value">{shift_data.get('shift_start', 'N/A')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Shift End:</span>
                            <span class="summary-value">{shift_data.get('shift_end', 'N/A')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Duration:</span>
                            <span class="summary-value">{shift_data.get('session_duration', 'N/A')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Total Transactions:</span>
                            <span class="summary-value">{shift_data.get('total_transactions', 0)}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Total Sales:</span>
                            <span class="summary-value total-sales">{formatted_sales}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Opening Cash:</span>
                            <span class="summary-value">{format_currency(shift_data.get('opening_cash'))}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Closing Cash:</span>
                            <span class="summary-value">{format_currency(shift_data.get('closing_cash'))}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Expected Cash:</span>
                            <span class="summary-value">{format_currency(shift_data.get('expected_cash'))}</span>
                        </div>
                        <div class="summary-item">
                            <span class="summary-label">Cash Variance:</span>
                            <span class="summary-value">{format_currency(shift_data.get('cash_variance'))}</span>
                        </div>
                        {payment_rows}
                    </div>

                    <p>This is an automated notification from the PANN POS System.</p>
                </div>
                <div class="footer">
                    <p>© 2025 PANN POS System. All rights reserved.</p>
                    <p style="font-size: 10px; color: #999; margin-top: 10px;">
                        This is an automated transactional email. 
                        If you no longer wish to receive these notifications, please contact your system administrator.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_text_content = f"""
        Hello {admin_name or 'Admin'},

        The following shift has been closed:

        Shift ID: {shift_data.get('shift_id', 'N/A')}
        Cashier: {shift_data.get('cashier_name', 'Unknown')}
        Shift Start: {shift_data.get('shift_start', 'N/A')}
        Shift End: {shift_data.get('shift_end', 'N/A')}
        Duration: {shift_data.get('session_duration', 'N/A')}
        Total Transactions: {shift_data.get('total_transactions', 0)}
        Total Sales: {formatted_sales}
        Opening Cash: {format_currency(shift_data.get('opening_cash'))}
        Closing Cash: {format_currency(shift_data.get('closing_cash'))}
        Expected Cash: {format_currency(shift_data.get('expected_cash'))}
        Cash Variance: {format_currency(shift_data.get('cash_variance'))}

        This is an automated notification from the PANN POS System.

        © 2025 PANN POS System. All rights reserved.
        """

        return self.send_email(to_email, subject, html_content, plain_text_content)


email_service = EmailService()

