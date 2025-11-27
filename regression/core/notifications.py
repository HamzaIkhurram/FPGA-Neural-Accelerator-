Email Notification System - Production Quality
Senior Staff Engineer: SMTP, HTML emails, error handling
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from pathlib import Path

from regression.core.reporter import RegressionSummary, RegressionReporter

logger = logging.getLogger(__name__)


class EmailNotifier:
    Send email notifications for regression results
    
    Features:
    - HTML email support
    - SMTP configuration
    - Error handling
    - Multiple recipients
    """
    
    def __init__(self, smtp_server: str, smtp_port: int = 587,
                 username: Optional[str] = None, password: Optional[str] = None,
                 from_email: Optional[str] = None, use_tls: bool = True):
        Initialize email notifier
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username (optional)
            password: SMTP password (optional)
            from_email: From email address
            use_tls: Use TLS encryption
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email or username
        self.use_tls = use_tls
        
        logger.info(f"Initialized EmailNotifier: server={smtp_server}:{smtp_port}")
    
    def send_regression_report(self, summary: RegressionSummary,
                              recipients: List[str],
                              reporter: RegressionReporter) -> bool:
        Send regression report via email
        
        Args:
            summary: Regression summary
            recipients: List of email addresses
            reporter: Reporter instance for email content
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Generate email content
            email_html = reporter.generate_email_summary(summary)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Regression {summary.name}: {'PASSED' if summary.failed == 0 else 'FAILED'}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            
            # Attach HTML content
            html_part = MIMEText(email_html, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
            
            logger.info(f"Sent regression email to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False
    
    def send_simple_notification(self, subject: str, body: str,
                                 recipients: List[str]) -> bool:
        Send simple text notification
        
        Args:
            subject: Email subject
            body: Email body text
            recipients: List of email addresses
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
            
            logger.info(f"Sent notification to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}", exc_info=True)
            return False

