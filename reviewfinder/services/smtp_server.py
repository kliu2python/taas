import asyncio
import smtplib

from aiosmtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Union

from reviewfinder.common.conf import CONF
from utils.logger import get_logger


logger = get_logger()
REDDIT_CONF = CONF.get("reddit")
SMTP_CONF = CONF.get("smtp")

# Email settings
SMTP_SERVER = SMTP_CONF.get("server")
SMTP_PORT = SMTP_CONF.get("port")
SMTP_USERNAME = SMTP_CONF.get("username")
SMTP_PASSWORD = SMTP_CONF.get("password")

SENDER_EMAIL = SMTP_CONF.get("sender", 'fortireviewfinder_support@gmail.com')
DEFAULT_RECIPIENTS = SMTP_CONF.get("recipients", ['ljiahao@fortinet.com'])


class SMTPServer:
    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str,
        sender_email: str
    ):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.sender_email = sender_email

    async def send_email(
            self, subject: str, body: str,
            recipients: Union[str, List[str]] = None,
            use_bcc: bool = True) -> None:
        if recipients is None:
            recipients = DEFAULT_RECIPIENTS
        elif isinstance(recipients, str):
            recipients = [recipients]

        logger.info(f"Sending email to the recipients {recipients}")

        if not recipients:
            raise ValueError("No recipients specified")

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['Subject'] = subject

        if use_bcc:
            msg['To'] = self.sender_email
            msg['Bcc'] = ', '.join(recipients)
        else:
            msg['To'] = ', '.join(recipients)

        msg.attach(MIMEText(body, 'plain'))

        def sync_send():
            try:
                with smtplib.SMTP(self.server, self.port) as srv:
                    srv.starttls()
                    srv.login(self.username, self.password)
                    srv.send_message(msg)
                logger.info(
                    f"Email sent successfully to recipient {recipients}")
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
                raise

        # Run the synchronous email send in a separate thread to avoid blocking
        await asyncio.to_thread(sync_send)

    @classmethod
    def from_config(cls) -> 'SMTPServer':
        """
        Create an SMTPServer instance from configuration
        
        Returns:
            SMTPServer: Configured SMTP server instance
        """
        return cls(
            server=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            sender_email=SENDER_EMAIL
        )


# Convenience function to send email using configuration
def send_email(
    subject: str,
    body: str,
    recipients: Union[str, List[str]] = None,
    use_bcc: bool = True
) -> None:
    """
    Send email using configured SMTP server
    
    Args:
        subject: Email subject
        body: Email body content
        recipients: Single email address or list of email addresses
        use_bcc: If True, recipients will be added to BCC for privacy
    """
    smtp_server = SMTPServer.from_config()
    smtp_server.send_email(subject, body, recipients, use_bcc)

