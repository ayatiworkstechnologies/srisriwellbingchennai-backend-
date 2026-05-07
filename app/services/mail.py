from email.message import EmailMessage
from html import escape
import smtplib

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import AdminUser, BookingEmailLog, TherapyBooking


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


def send_logged_email_safe(
    db: Session,
    *,
    booking: TherapyBooking,
    audience: str,
    event_key: str,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> bool:
    try:
        send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        log_booking_email(
            db,
            booking_id=booking.id,
            audience=audience,
            event_key=event_key,
            recipient_email=to_email,
            subject=subject,
            delivery_status="sent",
        )
        return True
    except HTTPException as exc:
        log_booking_email(
            db,
            booking_id=booking.id,
            audience=audience,
            event_key=event_key,
            recipient_email=to_email,
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

    return f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f5f2ec;font-family:Arial,sans-serif;color:#1f1a17;">
    <div style="padding:32px 16px;">
      <div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:28px;overflow:hidden;box-shadow:0 16px 50px rgba(59,34,24,0.12);">
        <div style="background:linear-gradient(135deg,#4b2411 0%,#34190d 100%);padding:24px 32px;">
          <div style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:0.01em;">Sri Sri Wellbeing Chennai</div>
          <div style="margin-top:8px;color:#e5cc82;font-size:13px;letter-spacing:0.14em;text-transform:uppercase;">Holistic Healing Appointment Update</div>
        </div>
        <div style="padding:40px 32px 36px;">
          {audience_note}
          <div style="font-size:34px;line-height:1;color:#d0a93d;">&#10043;</div>
          <h1 style="margin:16px 0 0;font-size:32px;line-height:1.2;color:#1f1a17;">{escape(heading)}</h1>
          <p style="margin:18px 0 0;color:#564d47;font-size:16px;line-height:1.8;">{escape(intro_message)}</p>

          <div style="margin-top:28px;border:1px solid #eadfce;border-radius:24px;background:#fcfaf6;padding:24px;">
            <div style="display:inline-block;padding:12px 18px;border-radius:999px;background:#f1ebe2;color:#3b2218;font-size:15px;font-weight:700;">
              Reference: {escape(booking.reference_code)}
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

          <p style="margin:28px 0 0;color:#6d625c;font-size:14px;line-height:1.8;">
            Thank you,<br/>
            Sri Sri Wellbeing Chennai
          </p>
        </div>
      </div>
    </div>
  </body>
</html>
"""


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


def _booking_event_copy(event_key: str) -> dict[str, str]:
    event_map = {
        "request_received": {
            "customer_subject": "Appointment Booked Successfully",
            "customer_heading": "Booking Requested!",
            "customer_message": "Your appointment request has been received successfully. Our team will review it and share the next update shortly.",
            "admin_subject": "New Booking Request Received",
            "admin_heading": "New Booking Request",
            "admin_message": "A new appointment booking has been created and is awaiting review.",
        },
        "approved": {
            "customer_subject": "Your Appointment Is Successfully Approved",
            "customer_heading": "Booking Approved!",
            "customer_message": "Your appointment has been successfully approved by our team.",
            "admin_subject": "Booking Approved By Admin",
            "admin_heading": "Booking Approved",
            "admin_message": "The appointment has been approved by the admin team.",
        },
        "therapist_assigned": {
            "customer_subject": "Your Therapist Has Been Assigned",
            "customer_heading": "Therapist Assigned!",
            "customer_message": "Your appointment therapist has now been assigned. Please review the final booking details below.",
            "admin_subject": "Therapist Assigned To Booking",
            "admin_heading": "Therapist Assigned",
            "admin_message": "A therapist has been assigned to the booking.",
        },
        "slot_assigned": {
            "customer_subject": "Your Appointment Time Slot Is Confirmed",
            "customer_heading": "Time Slot Confirmed!",
            "customer_message": "Your appointment time slot has now been finalized. Please review the updated booking details below.",
            "admin_subject": "Appointment Slot Assigned",
            "admin_heading": "Time Slot Assigned",
            "admin_message": "A final appointment slot has been assigned to the booking.",
        },
        "therapist_and_slot_assigned": {
            "customer_subject": "Your Therapist And Time Slot Are Confirmed",
            "customer_heading": "Final Appointment Details Confirmed!",
            "customer_message": "Your therapist and appointment time slot have now been finalized. Please review the final booking details below.",
            "admin_subject": "Therapist And Slot Assigned",
            "admin_heading": "Final Booking Details Assigned",
            "admin_message": "The booking now has both therapist and final slot details assigned.",
        },
        "completed": {
            "customer_subject": "Your Appointment Has Been Completed",
            "customer_heading": "Booking Completed",
            "customer_message": "Your appointment has been marked as completed. Thank you for choosing Sri Sri Wellbeing Chennai.",
            "admin_subject": "Booking Completed",
            "admin_heading": "Booking Completed",
            "admin_message": "The appointment has been marked as completed.",
        },
        "cancelled_by_customer": {
            "customer_subject": "Your Appointment Has Been Cancelled",
            "customer_heading": "Booking Cancelled",
            "customer_message": "Your appointment has been cancelled successfully. If you would like to reschedule, please contact our team.",
            "admin_subject": "Booking Cancelled By Customer",
            "admin_heading": "Booking Cancelled",
            "admin_message": "The appointment has been cancelled by the customer.",
        },
        "cancelled_by_admin": {
            "customer_subject": "Your Appointment Has Been Cancelled",
            "customer_heading": "Booking Cancelled",
            "customer_message": "Your appointment has been cancelled by our team. Please contact us if you would like help rescheduling.",
            "admin_subject": "Booking Cancelled By Admin",
            "admin_heading": "Booking Cancelled",
            "admin_message": "The appointment has been cancelled by the admin team.",
        },
        "rescheduled": {
            "customer_subject": "Your Appointment Has Been Rescheduled",
            "customer_heading": "Booking Rescheduled",
            "customer_message": "Your appointment schedule has been updated. Please review the revised details below.",
            "admin_subject": "Booking Rescheduled",
            "admin_heading": "Booking Rescheduled",
            "admin_message": "The appointment has been rescheduled.",
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
    event_copy = _booking_event_copy(event_key)
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
        admin_recipients = get_admin_notification_emails()
        sent_any = False
        for recipient in admin_recipients:
            sent_any = send_logged_email_safe(
                db,
                booking=booking,
                audience="admin",
                event_key="status_update",
                to_email=recipient,
                subject=admin_email["subject"],
                html_body=admin_email["html"],
                text_body=admin_email["text"],
            ) or sent_any
        result["admin"] = sent_any

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
        admin_recipients = get_admin_notification_emails()
        sent_any = False
        for recipient in admin_recipients:
            sent_any = send_logged_email_safe(
                db,
                booking=booking,
                audience="admin",
                event_key=event_key,
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
        "html": _build_branded_email_html(
            heading=subject.strip(),
            intro_message=safe_message,
            booking=booking,
            audience_label="Customer Update",
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
