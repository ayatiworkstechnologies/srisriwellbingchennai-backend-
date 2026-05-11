import asyncio
from app.config import get_settings
import smtplib
from email.message import EmailMessage

def test():
    settings = get_settings()
    print("SMTP Host:", settings.smtp_host)
    print("SMTP Port:", settings.smtp_port)
    print("SMTP User:", settings.smtp_username)
    print("SMTP Password:", settings.smtp_password)
    print("Use SSL:", settings.smtp_use_ssl)
    print("Use TLS:", settings.smtp_use_tls)
    
    msg = EmailMessage()
    msg['Subject'] = 'Test Mail'
    msg['From'] = settings.smtp_from_email
    msg['To'] = settings.admin_email
    msg.set_content('Test email from settings.')
    
    smtp_client = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    try:
        with smtp_client(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
            print('Mail sent successfully!')
    except Exception as e:
        print('Error:', e)

test()
