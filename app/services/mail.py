from email.message import EmailMessage
import smtplib

from fastapi import HTTPException, status

from ..config import get_settings
from ..models import TherapyBooking


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


def send_email(*, to_email: str, subject: str, html_body: str, text_body: str):
    settings = _require_mail_settings()

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to send email: {exc}",
        ) from exc


def build_booking_status_email(booking: TherapyBooking, custom_message: str | None = None):
    status_label = booking.status.replace("_", " ").title()
    subject = f"Your Sri Sri Wellbeing booking is {status_label}"

    therapist_line = (
        f"Assigned therapist: {booking.therapist_name}"
        if booking.therapist_name
        else "Assigned therapist: Will be shared shortly"
    )
    notes_line = booking.notes or "No additional notes"
    custom_block = custom_message.strip() if custom_message else ""

    text_lines = [
        f"Dear {booking.customer_name},",
        "",
        f"Your booking for {booking.therapy_name} is now {status_label}.",
        f"Reference code: {booking.reference_code}",
        f"Date: {booking.booking_date}",
        f"Time: {booking.start_time} - {booking.end_time}",
        therapist_line,
        f"Notes: {notes_line}",
    ]

    if custom_block:
        text_lines.extend(["", custom_block])

    text_lines.extend(
        [
            "",
            "Thank you,",
            "Sri Sri Wellbeing Chennai",
        ]
    )

    html_parts = [
        f"<p>Dear {booking.customer_name},</p>",
        f"<p>Your booking for <strong>{booking.therapy_name}</strong> is now <strong>{status_label}</strong>.</p>",
        "<ul>",
        f"<li><strong>Reference code:</strong> {booking.reference_code}</li>",
        f"<li><strong>Date:</strong> {booking.booking_date}</li>",
        f"<li><strong>Time:</strong> {booking.start_time} - {booking.end_time}</li>",
        f"<li><strong>Assigned therapist:</strong> {booking.therapist_name or 'Will be shared shortly'}</li>",
        f"<li><strong>Notes:</strong> {notes_line}</li>",
        "</ul>",
    ]

    if custom_block:
        html_parts.append(f"<p>{custom_block}</p>")

    html_parts.append("<p>Thank you,<br/>Sri Sri Wellbeing Chennai</p>")

    return {
        "subject": subject,
        "text": "\n".join(text_lines),
        "html": "".join(html_parts),
    }


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
        "text": f"Dear {booking.customer_name},\n\n{safe_message}\n\n{summary_text}\n\nSri Sri Wellbeing Chennai",
        "html": (
            f"<p>Dear {booking.customer_name},</p>"
            f"<p>{safe_message}</p>"
            f"{summary_html}"
            "<p>Sri Sri Wellbeing Chennai</p>"
        ),
    }
