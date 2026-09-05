import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from backend.config import settings

logger = logging.getLogger("samachar.email")


def _send_smtp_email_sync(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """Synchronous worker that connects to SMTP server and sends the message."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(f"📧 [DEV / SIMULATION MODE] Verification email for {to_email}: {subject}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL or settings.SMTP_USER, [to_email], msg.as_string())
        server.quit()
        logger.info(f"✅ Real verification email successfully delivered to {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to deliver email to {to_email}: {e}")
        return False


async def send_verification_otp_email(to_email: str, otp_code: str, user_name: str = "Reader") -> bool:
    """Dispatches a 6-digit account activation OTP email to the user asynchronously."""
    subject = f"🔐 Your Samachar Verification Code: {otp_code}"

    text_content = f"""
Hello {user_name},

Thank you for registering on Samachar Truth Intelligence Platform.

Your 6-digit account verification code is: {otp_code}

This code is valid for 10 minutes. If you did not request this account registration, please ignore this email.

— The Samachar Intelligence Team
https://samachar-news-2026.web.app
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #080B10; color: #E2E8F0; margin: 0; padding: 24px; }}
    .card {{ max-width: 520px; margin: 0 auto; background: #0E131F; border: 1px solid #1E293B; border-radius: 16px; padding: 36px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); }}
    .logo {{ font-size: 22px; font-weight: 900; letter-spacing: 2px; color: #FFFFFF; text-decoration: none; display: inline-block; margin-bottom: 24px; }}
    .logo span {{ color: #00F59B; }}
    .tag {{ font-size: 10px; font-weight: 800; letter-spacing: 1.5px; background: rgba(0, 245, 155, 0.15); color: #00F59B; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 16px; }}
    .title {{ font-size: 20px; font-weight: 700; color: #FFFFFF; margin: 0 0 12px 0; }}
    .desc {{ font-size: 14px; color: #94A3B8; line-height: 1.6; margin: 0 0 24px 0; }}
    .otp-box {{ background: #161D2E; border: 1.5px solid #00F59B; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; }}
    .otp-code {{ font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 900; letter-spacing: 8px; color: #00F59B; margin: 0; }}
    .otp-expiry {{ font-size: 12px; color: #64748B; margin-top: 8px; }}
    .footer {{ font-size: 12px; color: #64748B; border-top: 1px solid #1E293B; padding-top: 16px; margin-top: 24px; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">SAMACHAR<span>.</span></div>
    <div><span class="tag">ONE-TIME VERIFICATION</span></div>
    <h1 class="title">Verify Your Email Address</h1>
    <p class="desc">Hello <strong>{user_name}</strong>, please use the following 6-digit One-Time Password to complete your account registration and activate your verified news dashboard access:</p>
    
    <div class="otp-box">
      <div class="otp-code">{otp_code}</div>
      <div class="otp-expiry">⏱️ Valid for 10 minutes · Do not share this code</div>
    </div>

    <p class="desc" style="font-size: 12px;">If you did not initiate this request, you can safely ignore this email.</p>

    <div class="footer">
      &copy; 2026 Samachar News Platform. Obsidian Truth Engine 2.0.<br>
      Automated system email — please do not reply.
    </div>
  </div>
</body>
</html>
"""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _send_smtp_email_sync, to_email, subject, html_content, text_content)


async def send_password_reset_email(to_email: str, reset_token: str, user_name: str = "Reader") -> bool:
    """Dispatches a password reset link and token to the user asynchronously."""
    subject = "🔑 Reset Your Samachar Account Password"
    reset_url = f"{settings.API_DOMAIN}/login.html?reset_token={reset_token}"

    text_content = f"""
Hello {user_name},

A request was made to reset the password for your Samachar account.

Use the following security token to reset your password:
{reset_token}

Or visit: {reset_url}

This token will expire in 1 hour. If you did not request this, please disregard this email.

— The Samachar Intelligence Team
https://samachar-news-2026.web.app
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #080B10; color: #E2E8F0; margin: 0; padding: 24px; }}
    .card {{ max-width: 520px; margin: 0 auto; background: #0E131F; border: 1px solid #1E293B; border-radius: 16px; padding: 36px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); }}
    .logo {{ font-size: 22px; font-weight: 900; letter-spacing: 2px; color: #FFFFFF; text-decoration: none; display: inline-block; margin-bottom: 24px; }}
    .logo span {{ color: #00F59B; }}
    .tag {{ font-size: 10px; font-weight: 800; letter-spacing: 1.5px; background: rgba(0, 245, 155, 0.15); color: #00F59B; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 16px; }}
    .title {{ font-size: 20px; font-weight: 700; color: #FFFFFF; margin: 0 0 12px 0; }}
    .desc {{ font-size: 14px; color: #94A3B8; line-height: 1.6; margin: 0 0 24px 0; }}
    .token-box {{ background: #161D2E; border: 1.5px solid #00F59B; border-radius: 12px; padding: 16px; word-break: break-all; font-family: monospace; color: #00F59B; font-size: 13px; text-align: center; margin-bottom: 24px; }}
    .btn {{ display: inline-block; background: #00F59B; color: #080B10; font-weight: 700; text-decoration: none; padding: 12px 24px; border-radius: 8px; margin-bottom: 20px; }}
    .footer {{ font-size: 12px; color: #64748B; border-top: 1px solid #1E293B; padding-top: 16px; margin-top: 24px; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">SAMACHAR<span>.</span></div>
    <div><span class="tag">SECURITY ACTION</span></div>
    <h1 class="title">Reset Account Password</h1>
    <p class="desc">Hello <strong>{user_name}</strong>, a password reset request was received for your Samachar account. Click the button below or copy the security token to choose a new password:</p>
    
    <div style="text-align: center;">
      <a href="{reset_url}" class="btn">Reset Password</a>
    </div>

    <div class="token-box">{reset_token}</div>
    <p class="desc" style="font-size: 12px;">This token expires in 1 hour. If you did not initiate this change, your account remains safe and you can ignore this email.</p>

    <div class="footer">
      &copy; 2026 Samachar News Platform. Obsidian Truth Engine 2.0.<br>
      Automated system email — please do not reply.
    </div>
  </div>
</body>
</html>
"""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _send_smtp_email_sync, to_email, subject, html_content, text_content)
