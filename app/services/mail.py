from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from html import escape
import logging
import smtplib

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import AdminUser, BookingEmailLog, EmailNotificationSettings, Inquiry, TherapyBooking

logger = logging.getLogger(__name__)


def _require_mail_settings():
    settings = get_settings()

    if not settings.mail_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mail sending is disabled. Enable MAIL_ENABLED in backend environment settings.",
        )

    if not settings.smtp_host or not settings.smtp_from_email:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mail settings are incomplete. Configure SMTP_HOST and SMTP_FROM_EMAIL.",
        )

    return settings


def _normalize_email_list(values: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        raw_values = values.split(",")
    else:
        raw_values = values
    return [value.strip() for value in raw_values if isinstance(value, str) and value.strip()]


def _email_domain(email_address: str | None) -> str | None:
    if not email_address or "@" not in email_address:
        return None
    return email_address.rsplit("@", 1)[1].strip().lower() or None


def _decode_smtp_message(message: bytes | str | object) -> str:
    if isinstance(message, bytes):
        return message.decode("utf-8", errors="replace")
    return str(message)


def _format_recipient_errors(recipients: dict[str, tuple[int, bytes | str]]) -> str:
    return "; ".join(
        f"{email}: {code} {_decode_smtp_message(response)}"
        for email, (code, response) in recipients.items()
    )


def _format_smtp_exception(exc: Exception) -> str:
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        return (
            "SMTP login succeeded, but the mail server refused all recipients. "
            f"Recipient errors: {_format_recipient_errors(exc.recipients)}"
        )
    if isinstance(exc, smtplib.SMTPSenderRefused):
        return (
            "SMTP login succeeded, but the mail server refused the sender address "
            f"{exc.sender}: {exc.smtp_code} {_decode_smtp_message(exc.smtp_error)}"
        )
    if isinstance(exc, smtplib.SMTPResponseException):
        return f"SMTP server error {exc.smtp_code}: {_decode_smtp_message(exc.smtp_error)}"
    return str(exc)


def send_email(
    *,
    to_email: str | list[str],
    subject: str,
    html_body: str,
    text_body: str,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
):
    settings = _require_mail_settings()
    to_recipients = _normalize_email_list(to_email)
    cc_recipients = _normalize_email_list(cc)
    bcc_recipients = _normalize_email_list(bcc)

    if not to_recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one recipient email is required.",
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )
    message["To"] = ", ".join(to_recipients)
    if cc_recipients:
        message["Cc"] = ", ".join(cc_recipients)
    if settings.smtp_reply_to_email:
        message["Reply-To"] = settings.smtp_reply_to_email
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=_email_domain(settings.smtp_from_email))
    message["X-Mailer"] = "Sri Sri Wellbeing Chennai API"
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        smtp_client = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
        client_kwargs = {"timeout": settings.smtp_timeout_seconds}
        if settings.smtp_local_hostname:
            client_kwargs["local_hostname"] = settings.smtp_local_hostname
        with smtp_client(settings.smtp_host, settings.smtp_port, **client_kwargs) as server:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message, to_addrs=to_recipients + cc_recipients + bcc_recipients)
    except Exception as exc:
        detail = _format_smtp_exception(exc)
        logger.exception("Unable to send email via SMTP: %s", detail)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to send email: {detail}",
        ) from exc


def send_email_safe(
    *,
    to_email: str | list[str],
    subject: str,
    html_body: str,
    text_body: str,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
) -> bool:
    try:
        send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            cc=cc,
            bcc=bcc,
        )
        return True
    except HTTPException as exc:
        logger.warning("Email send failed and was suppressed: %s", exc.detail)
        return False


def log_booking_email(
    db: Session,
    *,
    booking_id: int,
    audience: str,
    event_key: str,
    recipient_email: str,
    subject: str,
    delivery_status: str,
    error_message: str | None = None,
):
    log = BookingEmailLog(
        booking_id=booking_id,
        audience=audience,
        event_key=event_key,
        recipient_email=recipient_email,
        subject=subject,
        delivery_status=delivery_status,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _log_booking_email_many(
    db: Session,
    *,
    booking_id: int,
    audience: str,
    event_key: str,
    recipient_emails: list[str],
    subject: str,
    delivery_status: str,
    error_message: str | None = None,
):
    logs = []
    for recipient_email in recipient_emails:
        logs.append(
            BookingEmailLog(
                booking_id=booking_id,
                audience=audience,
                event_key=event_key,
                recipient_email=recipient_email,
                subject=subject,
                delivery_status=delivery_status,
                error_message=error_message,
            )
        )
    if logs:
        db.add_all(logs)
        db.commit()


def send_logged_email_safe(
    db: Session,
    *,
    booking: TherapyBooking,
    audience: str,
    event_key: str,
    to_email: str | list[str],
    subject: str,
    html_body: str,
    text_body: str,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
) -> bool:
    to_recipients = _normalize_email_list(to_email)
    cc_recipients = _normalize_email_list(cc)
    bcc_recipients = _normalize_email_list(bcc)

    try:
        send_email(
            to_email=to_recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            cc=cc_recipients,
            bcc=bcc_recipients,
        )
        _log_booking_email_many(
            db,
            booking_id=booking.id,
            audience=audience,
            event_key=event_key,
            recipient_emails=to_recipients,
            subject=subject,
            delivery_status="sent",
        )
        _log_booking_email_many(
            db,
            booking_id=booking.id,
            audience=f"{audience}_cc",
            event_key=event_key,
            recipient_emails=cc_recipients,
            subject=subject,
            delivery_status="sent",
        )
        _log_booking_email_many(
            db,
            booking_id=booking.id,
            audience=f"{audience}_bcc",
            event_key=event_key,
            recipient_emails=bcc_recipients,
            subject=subject,
            delivery_status="sent",
        )
        return True
    except HTTPException as exc:
        _log_booking_email_many(
            db,
            booking_id=booking.id,
            audience=audience,
            event_key=event_key,
            recipient_emails=to_recipients or cc_recipients or bcc_recipients,
            subject=subject,
            delivery_status="failed",
            error_message=str(exc.detail),
        )
        return False


def _format_booking_date(booking: TherapyBooking) -> str:
    return booking.booking_date.strftime("%d %b %Y")


def _format_booking_time(booking: TherapyBooking) -> str:
    return (
        f"{booking.start_time.strftime('%I:%M %p').lstrip('0')} - "
        f"{booking.end_time.strftime('%I:%M %p').lstrip('0')}"
    )


def _assigned_therapist_label(booking: TherapyBooking) -> str:
    return booking.therapist_name or "Will be shared shortly"


def _customer_closing_message(booking: TherapyBooking) -> str:
    status_messages = {
        "pending": (
            "Welcome to Sri Sri Wellbeing Chennai. Thank you for choosing us for your wellbeing journey. "
            "Our team will review your request and share the next update soon."
        ),
        "confirmed": (
            "We are happy to welcome you to Sri Sri Wellbeing Chennai. Please arrive a few minutes early "
            "so we can make your visit calm, comfortable, and well prepared."
        ),
        "rescheduled": (
            "Thank you for your understanding. We look forward to welcoming you at the updated appointment time."
        ),
        "completed": (
            "Thank you for visiting Sri Sri Wellbeing Chennai. We hope your therapy experience was peaceful, "
            "restorative, and supportive for your wellbeing."
        ),
        "cancelled": (
            "Thank you for considering Sri Sri Wellbeing Chennai. If you would like to book again, "
            "our team will be happy to help you choose a suitable therapy and time."
        ),
        "no_show": (
            "We missed welcoming you for your appointment. Please contact our team if you would like help booking another visit."
        ),
    }
    return status_messages.get(
        booking.status,
        "Thank you for choosing Sri Sri Wellbeing Chennai. Our team is here to support your wellbeing journey.",
    )


def _booking_summary_text(booking: TherapyBooking) -> list[str]:
    return [
        f"Reference code: {booking.reference_code}",
        f"Therapy: {booking.therapy_name}",
        f"Date: {_format_booking_date(booking)}",
        f"Time: {_format_booking_time(booking)}",
        f"Assigned therapist: {_assigned_therapist_label(booking)}",
        f"Customer: {booking.customer_name}",
        f"Phone: {booking.phone}",
        f"Email: {booking.email}",
        f"Notes: {booking.notes or 'No additional notes'}",
    ]


def _booking_summary_html(booking: TherapyBooking) -> str:
    return (
        "<ul>"
        f"<li><strong>Reference code:</strong> {escape(booking.reference_code)}</li>"
        f"<li><strong>Therapy:</strong> {escape(booking.therapy_name)}</li>"
        f"<li><strong>Date:</strong> {escape(_format_booking_date(booking))}</li>"
        f"<li><strong>Time:</strong> {escape(_format_booking_time(booking))}</li>"
        f"<li><strong>Assigned therapist:</strong> {escape(_assigned_therapist_label(booking))}</li>"
        f"<li><strong>Customer:</strong> {escape(booking.customer_name)}</li>"
        f"<li><strong>Phone:</strong> {escape(booking.phone)}</li>"
        f"<li><strong>Email:</strong> {escape(booking.email)}</li>"
        f"<li><strong>Notes:</strong> {escape(booking.notes or 'No additional notes')}</li>"
        "</ul>"
    )


def _build_branded_email_html(*, heading: str, intro_message: str, booking: TherapyBooking, audience_label: str | None = None) -> str:
    audience_note = (
        f"<p style=\"margin:0 0 12px;color:#7a6f67;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;\">{escape(audience_label)}</p>"
        if audience_label
        else ""
    )
    notes_html = ""
    if booking.notes:
        notes_html = (
            "<div style=\"margin-top:16px;padding-top:16px;border-top:1px solid #eadfce;\">"
            "<div style=\"font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;\">Notes</div>"
            f"<div style=\"margin-top:8px;color:#4b413a;font-size:14px;line-height:1.7;\">{escape(booking.notes)}</div>"
            "</div>"
        )

    cancellation_html = ""
    if booking.status == "cancelled" and booking.cancellation_reason:
        cancellation_html = (
            "<div style=\"margin-top:16px;padding-top:16px;border-top:1px solid #eadfce;\">"
            "<div style=\"font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;\">Cancellation Reason</div>"
            f"<div style=\"margin-top:8px;color:#4b413a;font-size:14px;line-height:1.7;\">{escape(booking.cancellation_reason)}</div>"
            "</div>"
        )

    closing_message = _customer_closing_message(booking)
    status_label = booking.status.replace("_", " ").title()

    return f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f4efe7;font-family:Arial,sans-serif;color:#1f1a17;">
    <div style="padding:32px 16px;">
      <div style="max-width:700px;margin:0 auto;background:#ffffff;border-radius:28px;overflow:hidden;box-shadow:0 18px 52px rgba(59,34,24,0.14);">
        <div style="background:linear-gradient(135deg,#3b2218 0%,#5b321d 72%,#c6a14a 100%);padding:28px 32px;">
          <div style="display:inline-block;padding:7px 12px;border-radius:999px;background:rgba(255,255,255,0.12);color:#f7e7b2;font-size:11px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;">Appointment Care</div>
          <div style="margin-top:18px;font-size:24px;font-weight:800;color:#ffffff;letter-spacing:0.01em;">Sri Sri Wellbeing Chennai</div>
          <div style="margin-top:8px;color:#f3d98a;font-size:13px;letter-spacing:0.14em;text-transform:uppercase;">Ayurveda | Relaxation | Panchakarma</div>
        </div>
        <div style="padding:38px 32px 34px;">
          {audience_note}
          <div style="font-size:34px;line-height:1;color:#c6a14a;">&#10043;</div>
          <h1 style="margin:16px 0 0;font-size:31px;line-height:1.2;color:#1f1a17;">{escape(heading)}</h1>
          <p style="margin:18px 0 0;color:#564d47;font-size:16px;line-height:1.8;">{escape(intro_message)}</p>

          <div style="margin-top:26px;border:1px solid #eadfce;border-radius:24px;background:#fcfaf6;padding:24px;">
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
              <div style="display:inline-block;padding:11px 16px;border-radius:999px;background:#f1ebe2;color:#3b2218;font-size:14px;font-weight:800;">
                Reference: {escape(booking.reference_code)}
              </div>
              <div style="display:inline-block;padding:11px 16px;border-radius:999px;background:#fff5db;color:#8a6510;font-size:14px;font-weight:800;">
                Status: {escape(status_label)}
              </div>
            </div>
            <div style="margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div>
                <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Therapy</div>
                <div style="margin-top:8px;color:#1f1a17;font-size:16px;font-weight:700;">{escape(booking.therapy_name)}</div>
              </div>
              <div>
                <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Guest</div>
                <div style="margin-top:8px;color:#1f1a17;font-size:16px;font-weight:700;">{escape(booking.customer_name)}</div>
              </div>
              <div>
                <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Date</div>
                <div style="margin-top:8px;color:#1f1a17;font-size:16px;font-weight:700;">{escape(_format_booking_date(booking))}</div>
              </div>
              <div>
                <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Time Slot</div>
                <div style="margin-top:8px;color:#1f1a17;font-size:16px;font-weight:700;">{escape(_format_booking_time(booking))}</div>
              </div>
              <div>
                <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Therapist</div>
                <div style="margin-top:8px;color:#1f1a17;font-size:16px;font-weight:700;">{escape(_assigned_therapist_label(booking))}</div>
              </div>
              <div>
                <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Contact</div>
                <div style="margin-top:8px;color:#1f1a17;font-size:16px;font-weight:700;">{escape(booking.phone)}</div>
              </div>
            </div>
            {notes_html}
            {cancellation_html}
          </div>

          <div style="margin-top:24px;border-radius:22px;background:#f7f1e7;border:1px solid #eadfce;padding:22px;">
            <div style="font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:#9b7b2b;font-weight:800;">A Note From Our Team</div>
            <p style="margin:10px 0 0;color:#4f443d;font-size:15px;line-height:1.8;">{escape(closing_message)}</p>
          </div>

          <div style="margin-top:26px;color:#6d625c;font-size:14px;line-height:1.8;">
            <p style="margin:0;">Warm regards,</p>
            <p style="margin:4px 0 0;font-weight:800;color:#3b2218;">Sri Sri Wellbeing Chennai</p>
            <p style="margin:10px 0 0;color:#8a7c73;font-size:13px;">Please keep this email for your appointment reference.</p>
          </div>
        </div>
        <div style="background:#2f190f;padding:18px 32px;color:#d8c8b8;font-size:12px;line-height:1.7;text-align:center;">
          Thank you for choosing Sri Sri Wellbeing Chennai for your healing and wellbeing journey.
        </div>
      </div>
    </div>
  </body>
</html>
"""


def _customer_status_copy(status_value: str) -> tuple[str, str]:
    status_map = {
        "pending": (
            "Booking Request Received",
            "Welcome to Sri Sri Wellbeing Chennai. We have received your appointment request and our team will review it shortly.",
        ),
        "confirmed": (
            "Booking Confirmed",
            "Your appointment is confirmed. Thank you for choosing Sri Sri Wellbeing Chennai. We look forward to welcoming you.",
        ),
        "rescheduled": (
            "Booking Rescheduled",
            "Your appointment schedule has been updated. Please review the revised date and time below.",
        ),
        "completed": (
            "Booking Completed",
            "Thank you for visiting Sri Sri Wellbeing Chennai. Your appointment has been completed, and we are grateful you chose us for your wellbeing care.",
        ),
        "cancelled": (
            "Booking Cancelled",
            "Your booking has been cancelled. If you would like to book a new appointment, please contact our team.",
        ),
        "no_show": (
            "Booking Update",
            "Your booking has been marked as no-show. Please contact our team if you would like help rescheduling.",
        ),
    }
    return status_map.get(
        status_value,
        ("Booking Update", f"Your booking status is now {status_value.replace('_', ' ').title()}."),
    )


def _booking_event_copy(event_key: str, booking: TherapyBooking | None = None) -> dict[str, str]:
    status_label = booking.status.replace("_", " ").title() if booking else "Updated"
    event_map = {
        "request_received": {
            "customer_subject": "Welcome - Your Booking Request Has Been Received",
            "customer_heading": "Booking Request Received",
            "customer_message": "Welcome to Sri Sri Wellbeing Chennai. Thank you for choosing us. We have received your appointment request and our team will review it shortly.",
            "admin_subject": "New Booking Request Received",
            "admin_heading": "New Booking Request",
            "admin_message": "A new appointment booking has been created from the website and is awaiting review.",
        },
        "approved": {
            "customer_subject": "Your Appointment Is Confirmed",
            "customer_heading": "Booking Confirmed",
            "customer_message": "Your appointment has been confirmed by our team. Thank you for choosing Sri Sri Wellbeing Chennai. Please review the appointment details below.",
            "admin_subject": "Booking Approved By Admin",
            "admin_heading": "Booking Approved",
            "admin_message": "The appointment has been approved by the admin team.",
        },
        "therapist_assigned": {
            "customer_subject": "Your Therapist Has Been Assigned",
            "customer_heading": "Therapist Assigned",
            "customer_message": "Your therapist has been assigned for the appointment. We look forward to welcoming you to Sri Sri Wellbeing Chennai.",
            "admin_subject": "Therapist Assigned To Booking",
            "admin_heading": "Therapist Assigned",
            "admin_message": "A therapist has been assigned to the booking.",
        },
        "slot_assigned": {
            "customer_subject": "Your Appointment Time Slot Is Confirmed",
            "customer_heading": "Time Slot Confirmed",
            "customer_message": "Your appointment time slot has been finalized. Please review the updated details and keep this email for reference.",
            "admin_subject": "Appointment Slot Assigned",
            "admin_heading": "Time Slot Assigned",
            "admin_message": "A final appointment slot has been assigned to the booking.",
        },
        "therapist_and_slot_assigned": {
            "customer_subject": "Your Therapist And Time Slot Are Confirmed",
            "customer_heading": "Final Appointment Details Confirmed",
            "customer_message": "Your therapist and appointment time slot are confirmed. We look forward to welcoming you to Sri Sri Wellbeing Chennai.",
            "admin_subject": "Therapist And Slot Assigned",
            "admin_heading": "Final Booking Details Assigned",
            "admin_message": "The booking now has both therapist and final slot details assigned.",
        },
        "completed": {
            "customer_subject": "Thank You For Visiting Sri Sri Wellbeing Chennai",
            "customer_heading": "Thank You For Visiting",
            "customer_message": "Your appointment has been completed. Thank you for visiting Sri Sri Wellbeing Chennai and choosing us for your wellbeing journey.",
            "admin_subject": "Booking Completed",
            "admin_heading": "Booking Completed",
            "admin_message": "The appointment has been marked as completed.",
        },
        "cancelled_by_customer": {
            "customer_subject": "Your Appointment Has Been Cancelled",
            "customer_heading": "Booking Cancelled",
            "customer_message": "Your appointment has been cancelled successfully. Thank you for considering Sri Sri Wellbeing Chennai. If you would like to book again, our team will be happy to help.",
            "admin_subject": "Booking Cancelled By Customer",
            "admin_heading": "Booking Cancelled",
            "admin_message": "The appointment has been cancelled by the customer.",
        },
        "cancelled_by_admin": {
            "customer_subject": "Your Appointment Has Been Cancelled",
            "customer_heading": "Booking Cancelled",
            "customer_message": "Your appointment has been cancelled by our team. Thank you for choosing Sri Sri Wellbeing Chennai. Please contact us if you would like help booking another suitable time.",
            "admin_subject": "Booking Cancelled By Admin",
            "admin_heading": "Booking Cancelled",
            "admin_message": "The appointment has been cancelled by the admin team.",
        },
        "rescheduled": {
            "customer_subject": "Your Appointment Has Been Rescheduled",
            "customer_heading": "Booking Rescheduled",
            "customer_message": "Your appointment schedule has been updated. Thank you for your understanding. Please review the revised details below.",
            "admin_subject": "Booking Rescheduled",
            "admin_heading": "Booking Rescheduled",
            "admin_message": "The appointment has been rescheduled.",
        },
        "manual_status_update": {
            "customer_subject": "Your Appointment Status Has Been Updated",
            "customer_heading": "Booking Status Updated",
            "customer_message": f"Your booking status is now {status_label}. Please review the latest appointment details below.",
            "admin_subject": "Booking Status Update Sent",
            "admin_heading": "Booking Status Updated",
            "admin_message": f"A booking status update has been sent. Current status: {status_label}.",
        },
    }
    return event_map.get(event_key, {
        "customer_subject": "Booking Update",
        "customer_heading": "Booking Update",
        "customer_message": "There is an update to your booking.",
        "admin_subject": "Booking Update",
        "admin_heading": "Booking Update",
        "admin_message": "There is an update to a booking.",
    })


def build_booking_customer_email(booking: TherapyBooking, custom_message: str | None = None):
    heading, default_message = _customer_status_copy(booking.status)
    message = custom_message.strip() if custom_message else default_message
    subject = f"{heading} - {booking.reference_code}"

    text_lines = [
        f"Dear {booking.customer_name},",
        "",
        message,
        "",
        *_booking_summary_text(booking),
        "",
        _customer_closing_message(booking),
        "",
        "Thank you,",
        "Sri Sri Wellbeing Chennai",
    ]

    html = _build_branded_email_html(
        heading=heading,
        intro_message=message,
        booking=booking,
        audience_label="Customer Update",
    )

    return {
        "subject": subject,
        "text": "\n".join(text_lines),
        "html": html,
    }


def build_booking_admin_email(booking: TherapyBooking, custom_message: str | None = None):
    status_label = booking.status.replace("_", " ").title()
    heading = f"Booking {status_label}"
    message = custom_message.strip() if custom_message else (
        f"A booking has been {status_label.lower()}."
    )
    subject = f"Booking {status_label} - {booking.reference_code}"
    cancellation_line = (
        f"Cancellation reason: {booking.cancellation_reason}"
        if booking.cancellation_reason
        else "Cancellation reason: Not provided"
    )

    text_lines = [
        "Hello Admin,",
        "",
        message,
        "",
        *_booking_summary_text(booking),
    ]
    if booking.status == "cancelled":
        text_lines.append(cancellation_line)
    text_lines.extend(["", "Sri Sri Wellbeing Chennai"])

    html = _build_branded_email_html(
        heading=heading,
        intro_message=message,
        booking=booking,
        audience_label="Admin Notification",
    )

    return {
        "subject": subject,
        "text": "\n".join(text_lines),
        "html": html,
    }


def build_booking_event_email(
    booking: TherapyBooking,
    *,
    event_key: str,
    audience: str,
    custom_message: str | None = None,
):
    event_copy = _booking_event_copy(event_key, booking)
    if audience == "customer":
        subject = f"{event_copy['customer_subject']} - {booking.reference_code}"
        heading = event_copy["customer_heading"]
        message = custom_message.strip() if custom_message else event_copy["customer_message"]
        text_lines = [
            f"Dear {booking.customer_name},",
            "",
            heading,
            "",
            message,
            "",
            *_booking_summary_text(booking),
            "",
            _customer_closing_message(booking),
            "",
            "Thank you,",
            "Sri Sri Wellbeing Chennai",
        ]
        html = _build_branded_email_html(
            heading=heading,
            intro_message=message,
            booking=booking,
            audience_label="Customer Update",
        )
        return {"subject": subject, "text": "\n".join(text_lines), "html": html}

    subject = f"{event_copy['admin_subject']} - {booking.reference_code}"
    heading = event_copy["admin_heading"]
    message = custom_message.strip() if custom_message else event_copy["admin_message"]
    text_lines = [
        "Hello Admin,",
        "",
        heading,
        "",
        message,
        "",
        *_booking_summary_text(booking),
    ]
    if booking.status == "cancelled":
        text_lines.append(f"Cancellation reason: {booking.cancellation_reason or 'Not provided'}")
    text_lines.extend(["", "Sri Sri Wellbeing Chennai"])
    html = _build_branded_email_html(
        heading=heading,
        intro_message=message,
        booking=booking,
        audience_label="Admin Notification",
    )
    return {"subject": subject, "text": "\n".join(text_lines), "html": html}


def get_admin_notification_emails() -> list[str]:
    settings = get_settings()
    return [email.strip() for email in settings.admin_email.split(",") if email.strip()]


def _join_emails(emails: list[str]) -> str:
    return "\n".join(email.strip() for email in emails if email.strip())


def split_stored_emails(value: str | None) -> list[str]:
    return _normalize_email_list((value or "").replace("\n", ","))


def get_email_notification_settings(db: Session) -> EmailNotificationSettings:
    settings_row = db.query(EmailNotificationSettings).order_by(EmailNotificationSettings.id.asc()).first()
    if settings_row:
        return settings_row

    settings_row = EmailNotificationSettings(
        id=1,
        booking_to_emails=_join_emails(get_admin_notification_emails()),
        booking_cc_emails="",
        booking_bcc_emails="",
    )
    db.add(settings_row)
    db.commit()
    db.refresh(settings_row)
    return settings_row


def serialize_email_notification_settings(settings_row: EmailNotificationSettings) -> dict:
    return {
        "id": settings_row.id,
        "booking_to_emails": split_stored_emails(settings_row.booking_to_emails),
        "booking_cc_emails": split_stored_emails(settings_row.booking_cc_emails),
        "booking_bcc_emails": split_stored_emails(settings_row.booking_bcc_emails),
        "updated_at": settings_row.updated_at,
        "created_at": settings_row.created_at,
    }


def update_email_notification_settings(
    db: Session,
    *,
    booking_to_emails: list[str],
    booking_cc_emails: list[str],
    booking_bcc_emails: list[str],
) -> EmailNotificationSettings:
    settings_row = get_email_notification_settings(db)
    settings_row.booking_to_emails = _join_emails(booking_to_emails)
    settings_row.booking_cc_emails = _join_emails(booking_cc_emails)
    settings_row.booking_bcc_emails = _join_emails(booking_bcc_emails)
    db.commit()
    db.refresh(settings_row)
    return settings_row


def get_booking_notification_recipients(db: Session) -> dict[str, list[str]]:
    settings_row = get_email_notification_settings(db)
    to_emails = split_stored_emails(settings_row.booking_to_emails)
    if not to_emails:
        to_emails = get_admin_notification_emails()
    return {
        "to": to_emails,
        "cc": split_stored_emails(settings_row.booking_cc_emails),
        "bcc": split_stored_emails(settings_row.booking_bcc_emails),
    }


def send_booking_notifications(
    db: Session,
    booking: TherapyBooking,
    *,
    notify_customer: bool = True,
    notify_admin: bool = True,
    customer_message: str | None = None,
    admin_message: str | None = None,
) -> dict[str, bool]:
    result = {"customer": False, "admin": False}

    if notify_customer and booking.email:
        customer_email = build_booking_customer_email(booking, customer_message)
        result["customer"] = send_logged_email_safe(
            db,
            booking=booking,
            audience="customer",
            event_key="status_update",
            to_email=booking.email,
            subject=customer_email["subject"],
            html_body=customer_email["html"],
            text_body=customer_email["text"],
        )

    if notify_admin:
        admin_email = build_booking_admin_email(booking, admin_message)
        admin_recipients = get_booking_notification_recipients(db)
        if admin_recipients["to"]:
            result["admin"] = send_logged_email_safe(
                db,
                booking=booking,
                audience="admin",
                event_key="status_update",
                to_email=admin_recipients["to"],
                cc=admin_recipients["cc"],
                bcc=admin_recipients["bcc"],
                subject=admin_email["subject"],
                html_body=admin_email["html"],
                text_body=admin_email["text"],
            )

    return result


def send_booking_event_notifications(
    db: Session,
    booking: TherapyBooking,
    *,
    event_key: str,
    notify_customer: bool = True,
    notify_admin: bool = True,
    customer_message: str | None = None,
    admin_message: str | None = None,
) -> dict[str, bool]:
    result = {"customer": False, "admin": False}

    if notify_customer and booking.email:
        customer_email = build_booking_event_email(
            booking,
            event_key=event_key,
            audience="customer",
            custom_message=customer_message,
        )
        result["customer"] = send_logged_email_safe(
            db,
            booking=booking,
            audience="customer",
            event_key=event_key,
            to_email=booking.email,
            subject=customer_email["subject"],
            html_body=customer_email["html"],
            text_body=customer_email["text"],
        )

    if notify_admin:
        admin_email = build_booking_event_email(
            booking,
            event_key=event_key,
            audience="admin",
            custom_message=admin_message,
        )
        admin_recipients = get_booking_notification_recipients(db)
        if admin_recipients["to"]:
            result["admin"] = send_logged_email_safe(
                db,
                booking=booking,
                audience="admin",
                event_key=event_key,
                to_email=admin_recipients["to"],
                cc=admin_recipients["cc"],
                bcc=admin_recipients["bcc"],
                subject=admin_email["subject"],
                html_body=admin_email["html"],
                text_body=admin_email["text"],
            )

    return result


def build_booking_status_email(booking: TherapyBooking, custom_message: str | None = None):
    return build_booking_customer_email(booking, custom_message)


def build_custom_booking_email(booking: TherapyBooking, subject: str, message: str):
    safe_message = message.strip()
    summary_html = (
        "<ul>"
        f"<li><strong>Reference code:</strong> {booking.reference_code}</li>"
        f"<li><strong>Therapy:</strong> {booking.therapy_name}</li>"
        f"<li><strong>Date:</strong> {booking.booking_date}</li>"
        f"<li><strong>Time:</strong> {booking.start_time} - {booking.end_time}</li>"
        "</ul>"
    )
    summary_text = (
        f"Reference code: {booking.reference_code}\n"
        f"Therapy: {booking.therapy_name}\n"
        f"Date: {booking.booking_date}\n"
        f"Time: {booking.start_time} - {booking.end_time}"
    )

    return {
        "subject": subject.strip(),
        "text": (
            f"Dear {booking.customer_name},\n\n"
            f"{safe_message}\n\n"
            f"{summary_text}\n\n"
            f"{_customer_closing_message(booking)}\n\n"
            "Thank you,\n"
            "Sri Sri Wellbeing Chennai"
        ),
        "html": _build_branded_email_html(
            heading=subject.strip(),
            intro_message=safe_message,
            booking=booking,
            audience_label="Customer Update",
        ),
    }


def build_inquiry_email(inquiry: Inquiry, subject: str, message: str):
    safe_subject = subject.strip()
    safe_message = message.strip()
    summary_text = (
        f"Enquiry ID: {inquiry.id}\n"
        f"Name: {inquiry.name}\n"
        f"Phone: {inquiry.phone}\n"
        f"Email: {inquiry.email}\n"
        f"Topic: {inquiry.topic}\n"
        f"Service interest: {inquiry.service_interest or 'General enquiry'}\n"
        f"Source: {inquiry.source or 'Website'}\n"
        f"Page path: {inquiry.page_path or 'Not captured'}\n"
        f"Status: {inquiry.status}\n"
        f"Original message: {inquiry.message}"
    )
    html = f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f5f2ec;font-family:Arial,sans-serif;color:#1f1a17;">
    <div style="padding:32px 16px;">
      <div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:24px;overflow:hidden;box-shadow:0 16px 50px rgba(59,34,24,0.12);">
        <div style="background:#3b2218;padding:24px 32px;">
          <div style="font-size:22px;font-weight:800;color:#ffffff;">Sri Sri Wellbeing Chennai</div>
          <div style="margin-top:8px;color:#e5cc82;font-size:13px;letter-spacing:0.14em;text-transform:uppercase;">Enquiry Follow Up</div>
        </div>
        <div style="padding:36px 32px;">
          <h1 style="margin:0;font-size:28px;line-height:1.25;color:#1f1a17;">{escape(safe_subject)}</h1>
          <p style="margin:18px 0 0;color:#564d47;font-size:16px;line-height:1.8;">{escape(safe_message).replace(chr(10), "<br/>")}</p>

          <div style="margin-top:28px;border:1px solid #eadfce;border-radius:20px;background:#fcfaf6;padding:22px;">
            <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Enquiry Details</div>
            <ul style="margin:14px 0 0;padding-left:18px;color:#3f352f;font-size:14px;line-height:1.8;">
              <li><strong>Name:</strong> {escape(inquiry.name)}</li>
              <li><strong>Phone:</strong> {escape(inquiry.phone)}</li>
              <li><strong>Email:</strong> {escape(inquiry.email)}</li>
              <li><strong>Topic:</strong> {escape(inquiry.topic)}</li>
              <li><strong>Service interest:</strong> {escape(inquiry.service_interest or "General enquiry")}</li>
              <li><strong>Source:</strong> {escape(inquiry.source or "Website")}</li>
              <li><strong>Page path:</strong> {escape(inquiry.page_path or "Not captured")}</li>
              <li><strong>Status:</strong> {escape(inquiry.status)}</li>
            </ul>
            <div style="margin-top:16px;padding-top:16px;border-top:1px solid #eadfce;">
              <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9b8b7e;font-weight:700;">Original Message</div>
              <div style="margin-top:8px;color:#4b413a;font-size:14px;line-height:1.7;">{escape(inquiry.message).replace(chr(10), "<br/>")}</div>
            </div>
          </div>

          <p style="margin:26px 0 0;color:#6d625c;font-size:14px;line-height:1.8;">
            Thank you,<br/>
            Sri Sri Wellbeing Chennai
          </p>
        </div>
      </div>
    </div>
  </body>
</html>
"""
    text = (
        f"{safe_message}\n\n"
        f"{summary_text}\n\n"
        "Thank you,\n"
        "Sri Sri Wellbeing Chennai"
    )
    return {"subject": safe_subject, "text": text, "html": html}


def build_password_reset_email(admin_user: AdminUser, reset_link: str):
    subject = "Reset your Sri Sri Wellbeing admin password"
    text = (
        f"Hello {admin_user.full_name},\n\n"
        "We received a request to reset your admin password.\n\n"
        f"Reset link: {reset_link}\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "Sri Sri Wellbeing Chennai"
    )
    html = (
        f"<p>Hello {admin_user.full_name},</p>"
        "<p>We received a request to reset your admin password.</p>"
        f"<p><a href=\"{reset_link}\">Reset your password</a></p>"
        f"<p>If the button does not work, use this link:</p><p>{reset_link}</p>"
        "<p>If you did not request this, you can ignore this email.</p>"
        "<p>Sri Sri Wellbeing Chennai</p>"
    )
    return {"subject": subject, "text": text, "html": html}


def build_admin_login_welcome_email(
    admin_user: AdminUser,
    *,
    temporary_password: str,
    login_link: str,
):
    role_label = admin_user.role.replace("_", " ").title()
    subject = "Your Sri Sri Wellbeing Admin Login Details"
    text = (
        f"Dear {admin_user.full_name},\n\n"
        "Welcome to Sri Sri Wellbeing Chennai.\n\n"
        "Your team login has been created. Please use the details below to sign in:\n\n"
        f"Name: {admin_user.full_name}\n"
        f"Role: {role_label}\n"
        f"Email: {admin_user.email}\n"
        f"Temporary password: {temporary_password}\n"
        f"Login link: {login_link}\n\n"
        "After logging in, please review your assigned appointments and keep your details up to date. "
        "If any profile detail needs correction, please contact the Sri Sri Wellbeing admin team.\n\n"
        "For security, change your password after your first login or use Forgot password from the login page.\n\n"
        "Thank you,\n"
        "Sri Sri Wellbeing Chennai"
    )
    html = f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f4efe7;font-family:Arial,sans-serif;color:#1f1a17;">
    <div style="padding:32px 16px;">
      <div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:26px;overflow:hidden;box-shadow:0 18px 52px rgba(59,34,24,0.14);">
        <div style="background:linear-gradient(135deg,#3b2218 0%,#5b321d 72%,#c6a14a 100%);padding:28px 32px;">
          <div style="display:inline-block;padding:7px 12px;border-radius:999px;background:rgba(255,255,255,0.12);color:#f7e7b2;font-size:11px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;">Team Access</div>
          <div style="margin-top:18px;font-size:24px;font-weight:800;color:#ffffff;">Sri Sri Wellbeing Chennai</div>
          <div style="margin-top:8px;color:#f3d98a;font-size:13px;letter-spacing:0.14em;text-transform:uppercase;">Admin Portal Login Details</div>
        </div>
        <div style="padding:36px 32px;">
          <h1 style="margin:0;font-size:30px;line-height:1.2;color:#1f1a17;">Welcome, {escape(admin_user.full_name)}</h1>
          <p style="margin:18px 0 0;color:#564d47;font-size:16px;line-height:1.8;">
            Your Sri Sri Wellbeing Chennai team login has been created. Use the details below to access the admin portal.
          </p>

          <div style="margin-top:26px;border:1px solid #eadfce;border-radius:22px;background:#fcfaf6;padding:22px;">
            <div style="font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:#9b7b2b;font-weight:800;">Login Credentials</div>
            <table style="margin-top:14px;width:100%;border-collapse:collapse;color:#3f352f;font-size:14px;line-height:1.8;">
              <tr><td style="padding:8px 0;color:#8a7c73;font-weight:700;">Name</td><td style="padding:8px 0;font-weight:800;">{escape(admin_user.full_name)}</td></tr>
              <tr><td style="padding:8px 0;color:#8a7c73;font-weight:700;">Role</td><td style="padding:8px 0;font-weight:800;">{escape(role_label)}</td></tr>
              <tr><td style="padding:8px 0;color:#8a7c73;font-weight:700;">Email</td><td style="padding:8px 0;font-weight:800;">{escape(admin_user.email)}</td></tr>
              <tr><td style="padding:8px 0;color:#8a7c73;font-weight:700;">Temporary Password</td><td style="padding:8px 0;font-weight:800;">{escape(temporary_password)}</td></tr>
            </table>
            <a href="{escape(login_link)}" style="display:inline-block;margin-top:18px;border-radius:999px;background:#3b2218;color:#ffffff;text-decoration:none;padding:13px 20px;font-size:13px;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;">Open Admin Login</a>
          </div>

          <div style="margin-top:22px;border-radius:20px;background:#f7f1e7;border:1px solid #eadfce;padding:20px;">
            <div style="font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:#9b7b2b;font-weight:800;">Next Steps</div>
            <p style="margin:10px 0 0;color:#4f443d;font-size:15px;line-height:1.8;">
              After logging in, please review your assigned appointments and keep your details updated. If your profile, phone, qualification, or speciality needs correction, contact the Sri Sri Wellbeing admin team.
            </p>
            <p style="margin:10px 0 0;color:#4f443d;font-size:15px;line-height:1.8;">
              For security, change your password after your first login or use Forgot password from the login page.
            </p>
          </div>

          <p style="margin:26px 0 0;color:#6d625c;font-size:14px;line-height:1.8;">
            Thank you,<br/>
            <strong style="color:#3b2218;">Sri Sri Wellbeing Chennai</strong>
          </p>
        </div>
      </div>
    </div>
  </body>
</html>
"""
    return {"subject": subject, "text": text, "html": html}
