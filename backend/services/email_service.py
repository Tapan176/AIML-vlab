"""
Email service — free SMTP sender for OTP codes, password resets, and invoices.

Design goals
------------
* **Free providers only.** Works with any SMTP host that has a free tier:
  Gmail (App Password), Brevo/Sendinblue (300 emails/day free), Mailtrap (test
  inbox), etc. Configure via SMTP_* in backend/.env.
* **Safe dev fallback.** When SMTP_HOST is not configured, emails are printed to
  the console instead of being sent. This keeps the OTP/invoice flows working
  end-to-end locally without any mail account, and guarantees we never crash a
  request just because mail isn't set up.
* **Never blocks the request thread for long / never raises into the caller.**
  send_email() returns a bool and swallows transport errors (logged), so a flaky
  SMTP server can't 500 a signup or a webhook.

Public API
----------
    send_email(to, subject, html, text=None, attachments=None) -> bool
    send_otp_email(to, code, purpose) -> bool
    send_password_reset_email(to, reset_url) -> bool
    send_invoice_email(to, invoice) -> bool   # invoice = dict from invoice_service
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_USE_TLS,
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    APP_PUBLIC_URL,
)


def is_configured():
    """True only when SMTP host AND credentials are present.

    We require the credentials too (not just the host) so that pre-filling the
    Brevo host in .env without yet pasting the SMTP key keeps the safe console
    fallback active instead of attempting a real send that fails auth. As soon
    as SMTP_USER + SMTP_PASSWORD are set, real delivery turns on automatically.
    """
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _brand_wrapper(inner_html, title="AIML Lab"):
    """Wrap body HTML in a minimal, email-client-safe responsive shell."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1f2937;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fb;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
        <tr><td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:20px 28px;">
          <span style="color:#fff;font-size:18px;font-weight:700;letter-spacing:0.3px;">🤖 {title}</span>
        </td></tr>
        <tr><td style="padding:28px;">{inner_html}</td></tr>
        <tr><td style="padding:16px 28px;border-top:1px solid #eef0f5;color:#9ca3af;font-size:12px;">
          You're receiving this because you have an account at
          <a href="{APP_PUBLIC_URL}" style="color:#6366f1;text-decoration:none;">{APP_PUBLIC_URL}</a>.
          If this wasn't you, you can safely ignore this email.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


def send_email(to, subject, html, text=None, attachments=None):
    """Send an HTML email (with optional plain-text + attachments).

    attachments: list of dicts {filename, content (bytes), mimetype?} — used for
    PDF/HTML invoices. Returns True on success (or on console-fallback in dev),
    False if a configured SMTP send failed. Never raises.
    """
    if not isinstance(to, str) or '@' not in to:
        print(f"[email] refusing to send to invalid address: {to!r}")
        return False

    # --- Dev fallback: no SMTP configured → log instead of send -------------
    if not is_configured():
        print("\n" + "=" * 60)
        print(f"[email:DEV] To: {to}")
        print(f"[email:DEV] Subject: {subject}")
        if text:
            print(f"[email:DEV] Text:\n{text}")
        else:
            # Strip tags crudely so the OTP/links are readable in the console.
            import re
            print(f"[email:DEV] Body:\n{re.sub('<[^<]+?>', '', html)[:1500]}")
        if attachments:
            print(f"[email:DEV] Attachments: {[a.get('filename') for a in attachments]}")
        print("=" * 60 + "\n", flush=True)
        return True

    try:
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = formataddr((EMAIL_FROM_NAME, EMAIL_FROM))
        msg['To'] = to

        alt = MIMEMultipart('alternative')
        if text:
            alt.attach(MIMEText(text, 'plain', 'utf-8'))
        alt.attach(MIMEText(html, 'html', 'utf-8'))
        msg.attach(alt)

        for att in (attachments or []):
            part = MIMEApplication(att['content'])
            part.add_header('Content-Disposition', 'attachment',
                            filename=att.get('filename', 'attachment'))
            if att.get('mimetype'):
                part.set_type(att['mimetype'])
            msg.attach(part)

        context = ssl.create_default_context()
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15) as server:
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(EMAIL_FROM, [to], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                if SMTP_USE_TLS:
                    server.starttls(context=context)
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(EMAIL_FROM, [to], msg.as_string())
        return True
    except Exception as e:
        # Never let a mail failure break the request — log and report failure.
        print(f"[email] send failed to {to}: {e}", flush=True)
        return False


# ── Templated emails ────────────────────────────────────────────────────────

def send_otp_email(to, code, purpose="verify your email"):
    """Email a one-time verification code."""
    inner = f"""
      <h2 style="margin:0 0 8px;font-size:20px;">Your verification code</h2>
      <p style="margin:0 0 20px;color:#4b5563;font-size:14px;">
        Use the code below to {purpose}. It expires shortly, so enter it soon.
      </p>
      <div style="text-align:center;margin:8px 0 24px;">
        <span style="display:inline-block;font-size:32px;letter-spacing:10px;font-weight:700;
                     color:#4f46e5;background:#eef2ff;border-radius:10px;padding:14px 24px;">{code}</span>
      </div>
      <p style="margin:0;color:#9ca3af;font-size:13px;">
        Never share this code with anyone. We will never ask you for it.
      </p>"""
    text = f"Your AIML Lab verification code is {code}. It expires soon — enter it to {purpose}."
    return send_email(to, "Your AIML Lab verification code", _brand_wrapper(inner), text=text)


def send_password_reset_email(to, reset_url):
    """Email a password-reset link."""
    inner = f"""
      <h2 style="margin:0 0 8px;font-size:20px;">Reset your password</h2>
      <p style="margin:0 0 20px;color:#4b5563;font-size:14px;">
        We received a request to reset your password. Click the button below to
        choose a new one. This link expires in 1 hour.
      </p>
      <div style="text-align:center;margin:8px 0 24px;">
        <a href="{reset_url}" style="display:inline-block;background:#4f46e5;color:#fff;
           text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;">Reset password</a>
      </div>
      <p style="margin:0;color:#9ca3af;font-size:13px;word-break:break-all;">
        Or paste this link into your browser: {reset_url}
      </p>"""
    text = f"Reset your AIML Lab password (link expires in 1 hour): {reset_url}"
    return send_email(to, "Reset your AIML Lab password", _brand_wrapper(inner), text=text)


def send_invoice_email(to, invoice):
    """Email a billing invoice with an HTML invoice body + an .html attachment.

    `invoice` is the dict returned by services.invoice_service.build_invoice().
    """
    rows = "".join(
        f"""<tr>
              <td style="padding:8px 0;color:#374151;font-size:14px;">{li['description']}</td>
              <td style="padding:8px 0;color:#374151;font-size:14px;text-align:right;">{li['amount_display']}</td>
            </tr>"""
        for li in invoice.get('line_items', [])
    )
    inner = f"""
      <h2 style="margin:0 0 4px;font-size:20px;">Payment received — thank you!</h2>
      <p style="margin:0 0 4px;color:#4b5563;font-size:14px;">
        Invoice <strong>{invoice['invoice_number']}</strong> · {invoice['date']}
      </p>
      <p style="margin:0 0 20px;color:#4b5563;font-size:14px;">
        Plan: <strong>{invoice['plan_name']}</strong> · Paid via {invoice['provider_label']}
      </p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #eef0f5;border-bottom:1px solid #eef0f5;margin:0 0 12px;">
        {rows}
      </table>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:8px 0;font-weight:700;font-size:15px;">Total</td>
          <td style="padding:8px 0;font-weight:700;font-size:15px;text-align:right;">{invoice['total_display']}</td>
        </tr>
      </table>
      <p style="margin:16px 0 0;color:#9ca3af;font-size:13px;">
        A copy of this invoice is attached. Manage your subscription anytime from your profile.
      </p>"""
    text = (f"AIML Lab invoice {invoice['invoice_number']} ({invoice['date']}). "
            f"Plan: {invoice['plan_name']}. Total: {invoice['total_display']}. "
            f"Paid via {invoice['provider_label']}.")
    attachment = {
        'filename': f"invoice-{invoice['invoice_number']}.html",
        'content': _brand_wrapper(inner, title="AIML Lab — Invoice").encode('utf-8'),
        'mimetype': 'text/html',
    }
    return send_email(to, f"Your AIML Lab invoice {invoice['invoice_number']}",
                      _brand_wrapper(inner), text=text, attachments=[attachment])
