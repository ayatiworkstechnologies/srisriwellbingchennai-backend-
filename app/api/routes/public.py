from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..content_helpers import create_entity, list_active_entities
from ...database import get_db
from ...models import (
    AlternativeTreatment,
    BookingSlot,
    Inquiry,
    NadiCamp,
    PanchakarmaCoreTherapy,
    PanchakarmaOtherTreatment,
    RelaxationTherapy,
    Service,
    Testimonial,
    Therapist,
    TherapistAvailability,
    TherapyBooking,
)
from ...schemas import (
    AlternativeTreatmentResponse,
    BookingCancelRequest,
    BookingCancelResponse,
    InquiryCreate,
    InquiryResponse,
    NadiCampResponse,
    PanchakarmaCoreTherapyResponse,
    PanchakarmaOtherTreatmentResponse,
    PublicBookingSlotResponse,
    PublicTherapyAvailabilityResponse,
    RelaxationTherapyResponse,
    ServiceResponse,
    TestimonialResponse,
    TherapyBookingCreate,
    TherapyBookingResponse,
)
from ...services.booking import (
    as_public_booking_slot,
    build_public_availability,
    build_cancel_token,
    build_reference_code,
    get_remaining_capacity,
    serialize_booking,
    serialize_cancel_response,
)
from ...services.content import (
    as_alt,
    as_nadi_camp,
    as_pk_core,
    as_pk_other,
    as_relax,
    as_service,
    as_testimonial,
)

router = APIRouter(prefix="/api/v1")


@router.post("/inquiries", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(payload: InquiryCreate, db: Session = Depends(get_db)):
    return create_entity(Inquiry, payload, db)


@router.get("/public/services", response_model=list[ServiceResponse])
def list_public_services(db: Session = Depends(get_db)):
    items = list_active_entities(Service, db)
    return [as_service(item) for item in items]


@router.get("/public/testimonials", response_model=list[TestimonialResponse])
def list_public_testimonials(db: Session = Depends(get_db)):
    items = list_active_entities(Testimonial, db)
    return [as_testimonial(item) for item in items]


@router.get("/public/nadi-camps", response_model=list[NadiCampResponse])
def list_public_nadi_camps(db: Session = Depends(get_db)):
    items = list_active_entities(NadiCamp, db)
    return [as_nadi_camp(item) for item in items]


@router.get("/public/relaxation-therapies", response_model=list[RelaxationTherapyResponse])
def list_public_relaxation_therapies(db: Session = Depends(get_db)):
    items = list_active_entities(RelaxationTherapy, db)
    return [as_relax(item) for item in items]


@router.get("/public/alternative-treatments", response_model=list[AlternativeTreatmentResponse])
def list_public_alternative_treatments(db: Session = Depends(get_db)):
    items = list_active_entities(AlternativeTreatment, db)
    return [as_alt(item) for item in items]


@router.get("/public/panchakarma-core-therapies", response_model=list[PanchakarmaCoreTherapyResponse])
def list_public_panchakarma_core_therapies(db: Session = Depends(get_db)):
    items = list_active_entities(PanchakarmaCoreTherapy, db)
    return [as_pk_core(item) for item in items]


@router.get("/public/panchakarma-other-treatments", response_model=list[PanchakarmaOtherTreatmentResponse])
def list_public_panchakarma_other_treatments(db: Session = Depends(get_db)):
    items = list_active_entities(PanchakarmaOtherTreatment, db)
    return [as_pk_other(item) for item in items]


@router.get("/public/booking-slots", response_model=list[PublicBookingSlotResponse])
def list_public_booking_slots(
    therapy_name: str = Query(min_length=2),
    booking_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(BookingSlot)
        .filter(BookingSlot.is_active == "true", BookingSlot.therapy_name == therapy_name)
        .order_by(BookingSlot.booking_date.asc(), BookingSlot.start_time.asc(), BookingSlot.id.asc())
    )
    if booking_date:
        query = query.filter(BookingSlot.booking_date == booking_date)

    items = query.all()
    return [as_public_booking_slot(item, db) for item in items if get_remaining_capacity(item, db) > 0]


@router.get("/public/therapy-availability", response_model=list[PublicTherapyAvailabilityResponse])
def list_public_therapy_availability(
    therapy_name: str = Query(min_length=2),
    booking_date: date = Query(),
    db: Session = Depends(get_db),
):
    return build_public_availability(therapy_name, booking_date, db)


@router.post("/public/bookings", response_model=TherapyBookingResponse, status_code=status.HTTP_201_CREATED)
def create_public_booking(payload: TherapyBookingCreate, db: Session = Depends(get_db)):
    therapist = db.query(Therapist).filter(Therapist.id == payload.therapist_id, Therapist.is_active == "true").first()
    if not therapist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected therapist not found")

    matching_windows = [
        slot
        for slot in build_public_availability(payload.therapy_name, payload.booking_date, db)
        if slot.therapist_id == payload.therapist_id and slot.start_time == payload.start_time and slot.end_time == payload.end_time
    ]
    if not matching_windows:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected therapist slot is no longer available")

    item = TherapyBooking(
        reference_code=build_reference_code(),
        cancel_token=build_cancel_token(),
        therapy_name=payload.therapy_name,
        customer_name=payload.customer_name,
        phone=payload.phone,
        email=payload.email,
        therapist_id=therapist.id,
        therapist_name=therapist.full_name,
        booking_date=payload.booking_date,
        slot_id=payload.slot_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        notes=payload.notes,
        status="pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_booking(item)


@router.post("/public/bookings/cancel", response_model=BookingCancelResponse)
def cancel_public_booking(payload: BookingCancelRequest, db: Session = Depends(get_db)):
    item = (
        db.query(TherapyBooking)
        .filter(TherapyBooking.reference_code == payload.reference_code, TherapyBooking.email == payload.email)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if item.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is already cancelled")
    if item.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Completed bookings cannot be cancelled")

    item.status = "cancelled"
    item.cancellation_reason = payload.reason
    db.commit()
    db.refresh(item)
    return serialize_cancel_response(item)
