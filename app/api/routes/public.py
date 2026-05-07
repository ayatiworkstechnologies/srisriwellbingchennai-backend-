from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..content_helpers import create_entity, list_active_categories, list_active_entities, list_active_entities_by_category
from ...database import get_db
from ...legacy import ACTIVE_FLAG_TRUE
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
    ContentCategoryResponse,
    InquiryCreate,
    InquiryResponse,
    LeadInquiryCreate,
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
from ...services.mail import (
    build_booking_status_email,
    build_custom_booking_email,
    send_email,
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


@router.post("/contact/inquiries", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED, tags=["Public Contact"])
@router.post("/inquiries", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_inquiry(payload: InquiryCreate, db: Session = Depends(get_db)):
    return create_entity(Inquiry, payload, db)


@router.post("/contact/leads", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED, tags=["Public Contact"])
def create_contact_lead(payload: LeadInquiryCreate, db: Session = Depends(get_db)):
    topic = payload.topic or payload.service_interest or "General enquiry"
    message = payload.message or (
        f"Lead captured for service interest: {payload.service_interest}."
        if payload.service_interest
        else "Lead captured from website."
    )
    inquiry = InquiryCreate(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        topic=topic,
        message=message,
        source=payload.source,
        service_interest=payload.service_interest,
        page_path=payload.page_path,
    )
    return create_entity(Inquiry, inquiry, db)


@router.get("/content/services", response_model=list[ServiceResponse], tags=["Public Content"])
@router.get("/public/services", response_model=list[ServiceResponse], include_in_schema=False)
def list_public_services(db: Session = Depends(get_db)):
    items = list_active_entities(Service, db)
    return [as_service(item) for item in items]


@router.get("/content/testimonials", response_model=list[TestimonialResponse], tags=["Public Content"])
@router.get("/public/testimonials", response_model=list[TestimonialResponse], include_in_schema=False)
def list_public_testimonials(db: Session = Depends(get_db)):
    items = list_active_entities(Testimonial, db)
    return [as_testimonial(item) for item in items]


@router.get("/content/nadi-camps", response_model=list[NadiCampResponse], tags=["Public Content"])
@router.get("/public/nadi-camps", response_model=list[NadiCampResponse], include_in_schema=False)
def list_public_nadi_camps(db: Session = Depends(get_db)):
    items = list_active_entities(NadiCamp, db)
    return [as_nadi_camp(item) for item in items]


@router.get("/content/relaxation-therapies", response_model=list[RelaxationTherapyResponse], tags=["Public Content"])
@router.get("/public/relaxation-therapies", response_model=list[RelaxationTherapyResponse], include_in_schema=False)
def list_public_relaxation_therapies(db: Session = Depends(get_db)):
    items = list_active_entities(RelaxationTherapy, db)
    return [as_relax(item) for item in items]


@router.get("/content/alternative-treatments", response_model=list[AlternativeTreatmentResponse], tags=["Public Content"])
@router.get("/public/alternative-treatments", response_model=list[AlternativeTreatmentResponse], include_in_schema=False)
def list_public_alternative_treatments(
    category: str | None = Query(default=None, min_length=2),
    db: Session = Depends(get_db),
):
    items = list_active_entities_by_category(AlternativeTreatment, category, db)
    return [as_alt(item) for item in items]


@router.get("/content/alternative-treatment-categories", response_model=list[ContentCategoryResponse], tags=["Public Content"])
@router.get("/public/alternative-treatments/categories", response_model=list[ContentCategoryResponse], include_in_schema=False)
def list_public_alternative_treatment_categories(db: Session = Depends(get_db)):
    return [ContentCategoryResponse(category=category, item_count=item_count) for category, item_count in list_active_categories(AlternativeTreatment, db)]


@router.get("/content/panchakarma/core-therapies", response_model=list[PanchakarmaCoreTherapyResponse], tags=["Public Content"])
@router.get("/public/panchakarma-core-therapies", response_model=list[PanchakarmaCoreTherapyResponse], include_in_schema=False)
def list_public_panchakarma_core_therapies(db: Session = Depends(get_db)):
    items = list_active_entities(PanchakarmaCoreTherapy, db)
    return [as_pk_core(item) for item in items]


@router.get("/content/panchakarma/other-treatments", response_model=list[PanchakarmaOtherTreatmentResponse], tags=["Public Content"])
@router.get("/public/panchakarma-other-treatments", response_model=list[PanchakarmaOtherTreatmentResponse], include_in_schema=False)
def list_public_panchakarma_other_treatments(
    category: str | None = Query(default=None, min_length=2),
    db: Session = Depends(get_db),
):
    items = list_active_entities_by_category(PanchakarmaOtherTreatment, category, db)
    return [as_pk_other(item) for item in items]


@router.get("/content/panchakarma/other-treatment-categories", response_model=list[ContentCategoryResponse], tags=["Public Content"])
@router.get("/public/panchakarma-other-treatments/categories", response_model=list[ContentCategoryResponse], include_in_schema=False)
def list_public_panchakarma_other_treatment_categories(db: Session = Depends(get_db)):
    return [ContentCategoryResponse(category=category, item_count=item_count) for category, item_count in list_active_categories(PanchakarmaOtherTreatment, db)]


@router.get("/booking/slots", response_model=list[PublicBookingSlotResponse], tags=["Public Booking"])
@router.get("/public/booking-slots", response_model=list[PublicBookingSlotResponse], include_in_schema=False)
def list_public_booking_slots(
    therapy_name: str = Query(min_length=2),
    booking_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(BookingSlot)
        .filter(BookingSlot.is_active == ACTIVE_FLAG_TRUE, BookingSlot.therapy_name == therapy_name)
        .order_by(BookingSlot.booking_date.asc(), BookingSlot.start_time.asc(), BookingSlot.id.asc())
    )
    if booking_date:
        query = query.filter(BookingSlot.booking_date == booking_date)

    items = query.all()
    return [as_public_booking_slot(item, db) for item in items if get_remaining_capacity(item, db) > 0]


@router.get("/booking/availability", response_model=list[PublicTherapyAvailabilityResponse], tags=["Public Booking"])
@router.get("/public/therapy-availability", response_model=list[PublicTherapyAvailabilityResponse], include_in_schema=False)
def list_public_therapy_availability(
    therapy_name: str = Query(min_length=2),
    booking_date: date = Query(),
    db: Session = Depends(get_db),
):
    return build_public_availability(therapy_name, booking_date, db)


@router.post("/booking/appointments", response_model=TherapyBookingResponse, status_code=status.HTTP_201_CREATED, tags=["Public Booking"])
@router.post("/public/bookings", response_model=TherapyBookingResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_public_booking(payload: TherapyBookingCreate, db: Session = Depends(get_db)):
    therapist = None
    therapist_name = "Sri Sri Wellbeing Team"
    therapist_id = None
    if payload.therapist_id:
        therapist = db.query(Therapist).filter(Therapist.id == payload.therapist_id, Therapist.is_active == ACTIVE_FLAG_TRUE).first()
        if not therapist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected therapist not found")
        therapist_name = therapist.full_name
        therapist_id = therapist.id

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
        therapist_id=therapist_id,
        therapist_name=therapist_name,
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

    email_payload = build_custom_booking_email(
        item,
        subject=f"Booking received - {item.reference_code}",
        message=(
            "We have received your booking request. "
            "Our team will review it and contact you shortly with confirmation details."
        ),
    )
    try:
        send_email(
            to_email=item.email,
            subject=email_payload["subject"],
            html_body=email_payload["html"],
            text_body=email_payload["text"],
        )
    except HTTPException:
        pass

    return serialize_booking(item)


@router.post("/booking/appointments/cancel", response_model=BookingCancelResponse, tags=["Public Booking"])
@router.post("/public/bookings/cancel", response_model=BookingCancelResponse, include_in_schema=False)
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

    email_payload = build_booking_status_email(
        item,
        "Your booking has been cancelled. If you would like to reschedule, please contact our team.",
    )
    try:
        send_email(
            to_email=item.email,
            subject=email_payload["subject"],
            html_body=email_payload["html"],
            text_body=email_payload["text"],
        )
    except HTTPException:
        pass

    return serialize_cancel_response(item)
