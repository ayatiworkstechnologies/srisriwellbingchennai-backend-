from datetime import date, datetime, time, timedelta
from secrets import token_hex

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..legacy import ACTIVE_FLAG_TRUE, is_active_flag
from ..models import BookingSlot, Therapist, TherapistAvailability, TherapistBlackout, TherapyBooking
from ..schemas import (
    BookingCancelResponse,
    BookingSlotResponse,
    PublicBookingSlotResponse,
    PublicTherapyAvailabilityResponse,
    TherapistAvailabilityResponse,
    TherapistBlackoutResponse,
    TherapistResponse,
    TherapyBookingResponse,
)


ACTIVE_BOOKING_STATUSES = ("pending", "confirmed", "rescheduled")
WEEKDAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DEFAULT_DAILY_SLOT_STARTS = (
    time(9, 0),
    time(11, 0),
    time(13, 0),
    time(15, 0),
    time(17, 0),
)
DEFAULT_SLOT_DURATION_MINUTES = 45
UNASSIGNED_THERAPIST_ID = 0
UNASSIGNED_THERAPIST_NAME = "Sri Sri Wellbeing Team"


def build_reference_code() -> str:
    return f"SSW-{datetime.utcnow():%Y%m%d}-{token_hex(3).upper()}"


def build_cancel_token() -> str:
    return token_hex(16)


def split_lines(value: str) -> list[str]:
    return [item.strip() for item in value.splitlines() if item.strip()]


def join_lines(items: list[str]) -> str:
    return "\n".join(item.strip() for item in items if item.strip())


def normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").split())


def combine_time(value: date, clock: time) -> datetime:
    return datetime.combine(value, clock)


def add_minutes(clock: time, minutes: int) -> time:
    return (combine_time(date.today(), clock) + timedelta(minutes=minutes)).time()


def overlaps(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and start_b < end_a


def count_therapist_bookings(therapist_id: int, booking_date: date, start_time: time, end_time: time, db: Session, exclude_booking_id: int | None = None) -> int:
    query = db.query(func.count(TherapyBooking.id)).filter(
        TherapyBooking.therapist_id == therapist_id,
        TherapyBooking.booking_date == booking_date,
        TherapyBooking.status.in_(ACTIVE_BOOKING_STATUSES),
        TherapyBooking.start_time < end_time,
        TherapyBooking.end_time > start_time,
    )
    if exclude_booking_id:
        query = query.filter(TherapyBooking.id != exclude_booking_id)
    return query.scalar() or 0


def is_therapist_blocked(therapist_id: int, booking_date: date, start_time: time, end_time: time, db: Session) -> bool:
    blocks = (
        db.query(TherapistBlackout)
        .filter(
            TherapistBlackout.therapist_id == therapist_id,
            TherapistBlackout.blackout_date == booking_date,
            TherapistBlackout.is_active == ACTIVE_FLAG_TRUE,
        )
        .all()
    )
    for block in blocks:
        if block.start_time is None or block.end_time is None:
            return True
        if overlaps(start_time, end_time, block.start_time, block.end_time):
            return True
    return False


def has_capacity(availability: TherapistAvailability, booking_date: date, start_time: time, end_time: time, db: Session, exclude_booking_id: int | None = None) -> bool:
    booked = count_therapist_bookings(availability.therapist_id, booking_date, start_time, end_time, db, exclude_booking_id=exclude_booking_id)
    return booked < availability.max_bookings_per_slot


def therapist_supports_therapy(therapist: Therapist, therapy_name: str) -> bool:
    normalized_therapy = normalize_text(therapy_name)
    specialties = [normalize_text(item) for item in split_lines(therapist.specialties)]

    if not specialties:
        return True

    return any(
        specialty == normalized_therapy
        or normalized_therapy in specialty
        or specialty in normalized_therapy
        for specialty in specialties
    )


def serialize_therapist(item: Therapist) -> TherapistResponse:
    return TherapistResponse(
        id=item.id,
        full_name=item.full_name,
        email=item.email,
        phone=item.phone,
        specialties=split_lines(item.specialties),
        bio=item.bio,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def serialize_availability(item: TherapistAvailability) -> TherapistAvailabilityResponse:
    return TherapistAvailabilityResponse(
        id=item.id,
        therapist_id=item.therapist_id,
        therapy_name=item.therapy_name,
        day_of_week=item.day_of_week,
        start_time=item.start_time,
        end_time=item.end_time,
        slot_interval_minutes=item.slot_interval_minutes,
        max_bookings_per_slot=item.max_bookings_per_slot,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def serialize_blackout(item: TherapistBlackout) -> TherapistBlackoutResponse:
    return TherapistBlackoutResponse(
        id=item.id,
        therapist_id=item.therapist_id,
        blackout_date=item.blackout_date,
        start_time=item.start_time,
        end_time=item.end_time,
        reason=item.reason,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def serialize_booking(item: TherapyBooking) -> TherapyBookingResponse:
    return TherapyBookingResponse(
        id=item.id,
        reference_code=item.reference_code,
        therapy_name=item.therapy_name,
        customer_name=item.customer_name,
        phone=item.phone,
        email=item.email,
        therapist_id=item.therapist_id,
        therapist_name=item.therapist_name,
        booking_date=item.booking_date,
        slot_id=item.slot_id,
        start_time=item.start_time,
        end_time=item.end_time,
        notes=item.notes,
        status=item.status,
        cancellation_reason=item.cancellation_reason,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def serialize_cancel_response(item: TherapyBooking) -> BookingCancelResponse:
    return BookingCancelResponse(detail="Booking cancelled successfully", reference_code=item.reference_code, status=item.status)


def count_slot_bookings(slot_id: int, db: Session) -> int:
    return (
        db.query(func.count(TherapyBooking.id))
        .filter(TherapyBooking.slot_id == slot_id, TherapyBooking.status.in_(ACTIVE_BOOKING_STATUSES))
        .scalar()
        or 0
    )


def get_remaining_capacity(slot: BookingSlot, db: Session) -> int:
    return max(slot.capacity - count_slot_bookings(slot.id, db), 0)


def as_booking_slot(item: BookingSlot) -> BookingSlotResponse:
    return BookingSlotResponse(
        id=item.id,
        therapy_name=item.therapy_name,
        booking_date=item.booking_date,
        start_time=item.start_time,
        end_time=item.end_time,
        capacity=item.capacity,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_public_booking_slot(item: BookingSlot, db: Session) -> PublicBookingSlotResponse:
    return PublicBookingSlotResponse(
        id=item.id,
        therapy_name=item.therapy_name,
        booking_date=item.booking_date,
        start_time=item.start_time,
        end_time=item.end_time,
        capacity=item.capacity,
        remaining_capacity=get_remaining_capacity(item, db),
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_therapy_booking(item: TherapyBooking) -> TherapyBookingResponse:
    return serialize_booking(item)


def build_public_availability(therapy_name: str, booking_date: date, db: Session) -> list[PublicTherapyAvailabilityResponse]:
    weekday = booking_date.weekday()
    availabilities = (
        db.query(TherapistAvailability, Therapist)
        .join(Therapist, Therapist.id == TherapistAvailability.therapist_id)
        .filter(
            TherapistAvailability.is_active == ACTIVE_FLAG_TRUE,
            TherapistAvailability.therapy_name == therapy_name,
            TherapistAvailability.day_of_week == weekday,
            Therapist.is_active == ACTIVE_FLAG_TRUE,
        )
        .order_by(Therapist.full_name.asc(), TherapistAvailability.start_time.asc())
        .all()
    )

    slots: list[PublicTherapyAvailabilityResponse] = []
    for availability, therapist in availabilities:
        start = availability.start_time
        while add_minutes(start, availability.slot_interval_minutes) <= availability.end_time:
            end = add_minutes(start, availability.slot_interval_minutes)
            if not is_therapist_blocked(therapist.id, booking_date, start, end, db) and has_capacity(availability, booking_date, start, end, db):
                remaining = availability.max_bookings_per_slot - count_therapist_bookings(therapist.id, booking_date, start, end, db)
                slots.append(
                    PublicTherapyAvailabilityResponse(
                        therapist_id=therapist.id,
                        therapist_name=therapist.full_name,
                        therapy_name=availability.therapy_name,
                        booking_date=booking_date,
                        start_time=start,
                        end_time=end,
                        remaining_capacity=max(remaining, 0),
                    )
                )
            start = end

    if slots:
        return slots

    # Fallback: when no weekly therapist availability is configured yet,
    # expose five simple daytime slots so booking can still operate.
    therapists = (
        db.query(Therapist)
        .filter(Therapist.is_active == ACTIVE_FLAG_TRUE)
        .order_by(Therapist.full_name.asc(), Therapist.id.asc())
        .all()
    )
    matching_therapists = [item for item in therapists if therapist_supports_therapy(item, therapy_name)]
    fallback_therapist = (matching_therapists or therapists)[0] if therapists else None

    if not fallback_therapist:
        return [
            PublicTherapyAvailabilityResponse(
                therapist_id=UNASSIGNED_THERAPIST_ID,
                therapist_name=UNASSIGNED_THERAPIST_NAME,
                therapy_name=therapy_name,
                booking_date=booking_date,
                start_time=start,
                end_time=add_minutes(start, DEFAULT_SLOT_DURATION_MINUTES),
                remaining_capacity=5,
            )
            for start in DEFAULT_DAILY_SLOT_STARTS
        ]

    fallback_slots: list[PublicTherapyAvailabilityResponse] = []
    for start in DEFAULT_DAILY_SLOT_STARTS:
        end = add_minutes(start, DEFAULT_SLOT_DURATION_MINUTES)
        if is_therapist_blocked(fallback_therapist.id, booking_date, start, end, db):
            continue
        remaining = 1 - count_therapist_bookings(fallback_therapist.id, booking_date, start, end, db)
        if remaining <= 0:
            continue
        fallback_slots.append(
            PublicTherapyAvailabilityResponse(
                therapist_id=fallback_therapist.id,
                therapist_name=fallback_therapist.full_name,
                therapy_name=therapy_name,
                booking_date=booking_date,
                start_time=start,
                end_time=end,
                remaining_capacity=remaining,
            )
        )

    return fallback_slots
