import smtplib
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

    def send_email(
        self,
        subject: str,
        body: str,
        recipients: Union[str, List[str]] = None,
        use_bcc: bool = True
    ) -> None:
        """
        Send email to one or multiple recipients
        
        Args:
            subject: Email subject
            body: Email body content
            recipients: Single email address or list of email addresses
            use_bcc: If True, recipients will be added to BCC for privacy
        
        Raises:
            ValueError: If no recipients are provided
            SMTPException: If email sending fails
        """
        if recipients is None:
            recipients = DEFAULT_RECIPIENTS
        elif isinstance(recipients, str):
            recipients = [recipients]

        logger.info(f"send to the recipients {recipients}")
            
        if not recipients:
            raise ValueError("No recipients specified")

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['Subject'] = subject

        if use_bcc:
            # Set sender as visible recipient for privacy
            msg['To'] = self.sender_email
            msg['Bcc'] = ', '.join(recipients)
        else:
            msg['To'] = ', '.join(recipients)

        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(self.server, self.port) as srv:
                srv.starttls()
                srv.login(self.username, self.password)
                srv.send_message(msg)
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            raise

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

