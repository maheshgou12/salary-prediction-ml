import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings


def _connect_smtp(host: str, port: int, timeout: int = 10):
    """Connect to SMTP forcing IPv4 to prevent Windows/ISP IPv6 routing drops."""
    orig_getaddrinfo = socket.getaddrinfo

    def ipv4_getaddrinfo(h, p, family=0, socktype=0, proto=0, flags=0):
        return orig_getaddrinfo(h, p, socket.AF_INET, socktype, proto, flags)

    socket.getaddrinfo = ipv4_getaddrinfo
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            server = smtplib.SMTP(host, port, timeout=timeout)
            server.ehlo()
            server.starttls()
            server.ehlo()
        return server
    finally:
        socket.getaddrinfo = orig_getaddrinfo


def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print(f"[email disabled] To: {to_email} | Subject: {subject}\n{body}")
        return False

    if html_body:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
    else:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email

    port = settings.SMTP_PORT or 587
    try:
        server = _connect_smtp(settings.SMTP_HOST, port, timeout=4)
        if settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD.strip())
        server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())
        server.quit()
        print(f"[email sent] Successfully delivered reset email via port {port} to {to_email}")
        return True
    except Exception as e587:
        # Fallback to SSL port 465
        try:
            server = _connect_smtp(settings.SMTP_HOST, 465, timeout=4)
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD.strip())
            server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())
            server.quit()
            print(f"[email sent ssl] Successfully delivered reset email via port 465 to {to_email}")
            return True
        except Exception as e465:
            print(f"[email error] Port {port} ({e587}) and Port 465 ({e465}) failed for {to_email}")
            return False
