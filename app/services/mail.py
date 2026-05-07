from email.message import EmailMessage
import smtplib

from fastapi import HTTPException, status

from ..config import get_settings
from ..models import AdminUser, TherapyBooking


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
        smtp_client = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
        with smtp_client(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to send email: {exc}",
        ) from exc


def send_email_safe(*, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    try:
        send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        return True
    except HTTPException:
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
        f"<li><strong>Reference code:</strong> {booking.reference_code}</li>"
        f"<li><strong>Therapy:</strong> {booking.therapy_name}</li>"
        f"<li><strong>Date:</strong> {_format_booking_date(booking)}</li>"
        f"<li><strong>Time:</strong> {_format_booking_time(booking)}</li>"
        f"<li><strong>Assigned therapist:</strong> {_assigned_therapist_label(booking)}</li>"
        f"<li><strong>Customer:</strong> {booking.customer_name}</li>"
        f"<li><strong>Phone:</strong> {booking.phone}</li>"
        f"<li><strong>Email:</strong> {booking.email}</li>"
        f"<li><strong>Notes:</strong> {booking.notes or 'No additional notes'}</li>"
        "</ul>"
    )


def _customer_status_copy(status_value: str) -> tuple[str, str]:
    status_map = {
        "pending": (
            "Booking Requested!",
            "We have received your booking request. Our team will review it and share the next update shortly.",
        ),
        "confirmed": (
            "Booking Confirmed!",
            "Your booking has been confirmed. We look forward to welcoming you at Sri Sri Wellbeing Chennai.",
        ),
        "rescheduled": (
            "Booking Rescheduled",
            "Your booking schedule has been updated. Please review the revised appointment details below.",
        ),
        "completed": (
            "Booking Completed",
            "Your booking has been marked as completed. Thank you for choosing Sri Sri Wellbeing Chennai.",
        ),
        "cancelled": (
            "Booking Cancelled",
            "Your booking has been cancelled. If you would like to reschedule, please contact our team.",
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
        "Thank you,",
        "Sri Sri Wellbeing Chennai",
    ]

    html = (
        f"<p>Dear {booking.customer_name},</p>"
        f"<p><strong>{heading}</strong></p>"
        f"<p>{message}</p>"
        f"{_booking_summary_html(booking)}"
        "<p>Thank you,<br/>Sri Sri Wellbeing Chennai</p>"
    )

    return {
        "subject": subject,
        "text": "\n".join(text_lines),
        "html": html,
    }


def build_booking_admin_email(booking: TherapyBooking, custom_message: str | None = None):
    status_label = booking.status.replace("_", " ").title()
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

    html = (
        "<p>Hello Admin,</p>"
        f"<p><strong>{status_label}</strong></p>"
        f"<p>{message}</p>"
        f"{_booking_summary_html(booking)}"
    )
    if booking.status == "cancelled":
        html += f"<p><strong>Cancellation reason:</strong> {booking.cancellation_reason or 'Not provided'}</p>"
    html += "<p>Sri Sri Wellbeing Chennai</p>"

    return {
        "subject": subject,
        "text": "\n".join(text_lines),
        "html": html,
    }


def get_admin_notification_emails() -> list[str]:
    settings = get_settings()
    return [email.strip() for email in settings.admin_email.split(",") if email.strip()]


def send_booking_notifications(
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
        result["customer"] = send_email_safe(
            to_email=booking.email,
            subject=customer_email["subject"],
            html_body=customer_email["html"],
            text_body=customer_email["text"],
        )

    if notify_admin:
        admin_email = build_booking_admin_email(booking, admin_message)
        admin_recipients = get_admin_notification_emails()
        sent_any = False
        for recipient in admin_recipients:
            sent_any = send_email_safe(
                to_email=recipient,
                subject=admin_email["subject"],
                html_body=admin_email["html"],
                text_body=admin_email["text"],
            ) or sent_any
        result["admin"] = sent_any

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
        "text": f"Dear {booking.customer_name},\n\n{safe_message}\n\n{summary_text}\n\nSri Sri Wellbeing Chennai",
        "html": (
            f"<p>Dear {booking.customer_name},</p>"
            f"<p>{safe_message}</p>"
            f"{summary_html}"
            "<p>Sri Sri Wellbeing Chennai</p>"
        ),
    }


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
