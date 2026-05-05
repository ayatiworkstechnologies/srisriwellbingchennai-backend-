from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..content_helpers import (
    as_active_flag,
    create_entity,
    delete_entity,
    get_entity_or_404,
    list_entities,
    update_entity,
)
from ...database import get_db
from ...models import (
    AdminUser,
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
    TherapistBlackout,
    TherapyBooking,
)
from ...schemas import (
    AdminLoginRequest,
    AlternativeTreatmentCreate,
    AlternativeTreatmentResponse,
    AlternativeTreatmentUpdate,
    BookingSlotCreate,
    BookingSlotResponse,
    BookingSlotUpdate,
    DashboardResponse,
    InquiryResponse,
    InquiryStatusUpdate,
    NadiCampCreate,
    NadiCampResponse,
    NadiCampUpdate,
    PanchakarmaCoreTherapyCreate,
    PanchakarmaCoreTherapyResponse,
    PanchakarmaCoreTherapyUpdate,
    PanchakarmaOtherTreatmentCreate,
    PanchakarmaOtherTreatmentResponse,
    PanchakarmaOtherTreatmentUpdate,
    RelaxationTherapyCreate,
    RelaxationTherapyResponse,
    RelaxationTherapyUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
    TherapistAvailabilityCreate,
    TherapistAvailabilityResponse,
    TherapistAvailabilityUpdate,
    TherapistBlackoutCreate,
    TherapistBlackoutResponse,
    TherapistBlackoutUpdate,
    TherapistCreate,
    TherapistResponse,
    TherapistUpdate,
    TestimonialCreate,
    TestimonialResponse,
    TestimonialUpdate,
    TherapyBookingResponse,
    TherapyBookingStatusUpdate,
    TokenResponse,
)
from ...services.booking import (
    as_booking_slot,
    as_therapy_booking,
    join_lines as join_booking_lines,
    serialize_availability,
    serialize_blackout,
    serialize_booking,
    serialize_therapist,
)
from ...security import create_access_token, verify_password
from ...services.content import (
    as_alt,
    as_nadi_camp,
    as_pk_core,
    as_pk_other,
    as_relax,
    as_service,
    as_testimonial,
    join_lines,
)
from ..deps import get_current_admin

router = APIRouter(prefix="/api/v1/admin")


@router.post("/login", response_model=TokenResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if not admin or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(admin.email))


@router.get("/dashboard", response_model=DashboardResponse)
def admin_dashboard(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return DashboardResponse(
        total_inquiries=db.query(func.count(Inquiry.id)).scalar() or 0,
        new_inquiries=db.query(func.count(Inquiry.id)).filter(Inquiry.status == "new").scalar() or 0,
        contacted_inquiries=db.query(func.count(Inquiry.id)).filter(Inquiry.status == "contacted").scalar() or 0,
        closed_inquiries=db.query(func.count(Inquiry.id)).filter(Inquiry.status == "closed").scalar() or 0,
    )


@router.get("/inquiries", response_model=list[InquiryResponse])
def list_inquiries(
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = db.query(Inquiry).order_by(Inquiry.created_at.desc())
    if status_filter:
        query = query.filter(Inquiry.status == status_filter)
    return query.all()


@router.patch("/inquiries/{inquiry_id}", response_model=InquiryResponse)
def update_inquiry_status(
    inquiry_id: int,
    payload: InquiryStatusUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(Inquiry, inquiry_id, "Inquiry", db)
    return update_entity(item, payload, db)


@router.get("/services", response_model=list[ServiceResponse])
def list_admin_services(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(Service, db)
    return [as_service(item) for item in items]


@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(Service, payload, db, is_active=as_active_flag(payload.is_active))
    return as_service(item)


@router.put("/services/{entity_id}", response_model=ServiceResponse)
def update_service(entity_id: int, payload: ServiceUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(Service, entity_id, "Service", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_service(item)


@router.delete("/services/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(Service, entity_id, "Service", db)


@router.get("/testimonials", response_model=list[TestimonialResponse])
def list_admin_testimonials(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(Testimonial, db)
    return [as_testimonial(item) for item in items]


@router.post("/testimonials", response_model=TestimonialResponse, status_code=status.HTTP_201_CREATED)
def create_testimonial(payload: TestimonialCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(Testimonial, payload, db, is_active=as_active_flag(payload.is_active))
    return as_testimonial(item)


@router.put("/testimonials/{entity_id}", response_model=TestimonialResponse)
def update_testimonial(entity_id: int, payload: TestimonialUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(Testimonial, entity_id, "Testimonial", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_testimonial(item)


@router.delete("/testimonials/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_testimonial(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(Testimonial, entity_id, "Testimonial", db)


@router.get("/nadi-camps", response_model=list[NadiCampResponse])
def list_admin_nadi_camps(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(NadiCamp, db)
    return [as_nadi_camp(item) for item in items]


@router.post("/nadi-camps", response_model=NadiCampResponse, status_code=status.HTTP_201_CREATED)
def create_nadi_camp(payload: NadiCampCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(NadiCamp, payload, db, is_active=as_active_flag(payload.is_active))
    return as_nadi_camp(item)


@router.put("/nadi-camps/{entity_id}", response_model=NadiCampResponse)
def update_nadi_camp(entity_id: int, payload: NadiCampUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(NadiCamp, entity_id, "Nadi camp", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_nadi_camp(item)


@router.delete("/nadi-camps/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nadi_camp(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(NadiCamp, entity_id, "Nadi camp", db)


@router.get("/relaxation-therapies", response_model=list[RelaxationTherapyResponse])
def list_admin_relaxation_therapies(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(RelaxationTherapy, db)
    return [as_relax(item) for item in items]


@router.post("/relaxation-therapies", response_model=RelaxationTherapyResponse, status_code=status.HTTP_201_CREATED)
def create_relaxation_therapy(payload: RelaxationTherapyCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(
        RelaxationTherapy,
        payload,
        db,
        benefits=join_lines(payload.benefits),
        is_active=as_active_flag(payload.is_active),
    )
    return as_relax(item)


@router.put("/relaxation-therapies/{entity_id}", response_model=RelaxationTherapyResponse)
def update_relaxation_therapy(
    entity_id: int,
    payload: RelaxationTherapyUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(RelaxationTherapy, entity_id, "Relaxation therapy", db)
    item = update_entity(
        item,
        payload,
        db,
        benefits=join_lines(payload.benefits),
        is_active=as_active_flag(payload.is_active),
    )
    return as_relax(item)


@router.delete("/relaxation-therapies/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relaxation_therapy(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(RelaxationTherapy, entity_id, "Relaxation therapy", db)


@router.get("/alternative-treatments", response_model=list[AlternativeTreatmentResponse])
def list_admin_alternative_treatments(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(AlternativeTreatment, db)
    return [as_alt(item) for item in items]


@router.post("/alternative-treatments", response_model=AlternativeTreatmentResponse, status_code=status.HTTP_201_CREATED)
def create_alternative_treatment(payload: AlternativeTreatmentCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(AlternativeTreatment, payload, db, is_active=as_active_flag(payload.is_active))
    return as_alt(item)


@router.put("/alternative-treatments/{entity_id}", response_model=AlternativeTreatmentResponse)
def update_alternative_treatment(
    entity_id: int,
    payload: AlternativeTreatmentUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(AlternativeTreatment, entity_id, "Alternative treatment", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_alt(item)


@router.delete("/alternative-treatments/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alternative_treatment(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(AlternativeTreatment, entity_id, "Alternative treatment", db)


@router.get("/panchakarma-core-therapies", response_model=list[PanchakarmaCoreTherapyResponse])
def list_admin_panchakarma_core_therapies(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(PanchakarmaCoreTherapy, db)
    return [as_pk_core(item) for item in items]


@router.post("/panchakarma-core-therapies", response_model=PanchakarmaCoreTherapyResponse, status_code=status.HTTP_201_CREATED)
def create_panchakarma_core_therapy(
    payload: PanchakarmaCoreTherapyCreate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = create_entity(
        PanchakarmaCoreTherapy,
        payload,
        db,
        benefits=join_lines(payload.benefits),
        is_active=as_active_flag(payload.is_active),
    )
    return as_pk_core(item)


@router.put("/panchakarma-core-therapies/{entity_id}", response_model=PanchakarmaCoreTherapyResponse)
def update_panchakarma_core_therapy(
    entity_id: int,
    payload: PanchakarmaCoreTherapyUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(PanchakarmaCoreTherapy, entity_id, "Panchakarma core therapy", db)
    item = update_entity(
        item,
        payload,
        db,
        benefits=join_lines(payload.benefits),
        is_active=as_active_flag(payload.is_active),
    )
    return as_pk_core(item)


@router.delete("/panchakarma-core-therapies/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_panchakarma_core_therapy(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(PanchakarmaCoreTherapy, entity_id, "Panchakarma core therapy", db)


@router.get("/panchakarma-other-treatments", response_model=list[PanchakarmaOtherTreatmentResponse])
def list_admin_panchakarma_other_treatments(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(PanchakarmaOtherTreatment, db)
    return [as_pk_other(item) for item in items]


@router.post("/panchakarma-other-treatments", response_model=PanchakarmaOtherTreatmentResponse, status_code=status.HTTP_201_CREATED)
def create_panchakarma_other_treatment(
    payload: PanchakarmaOtherTreatmentCreate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = create_entity(PanchakarmaOtherTreatment, payload, db, is_active=as_active_flag(payload.is_active))
    return as_pk_other(item)


@router.put("/panchakarma-other-treatments/{entity_id}", response_model=PanchakarmaOtherTreatmentResponse)
def update_panchakarma_other_treatment(
    entity_id: int,
    payload: PanchakarmaOtherTreatmentUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(PanchakarmaOtherTreatment, entity_id, "Panchakarma other treatment", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_pk_other(item)


@router.delete("/panchakarma-other-treatments/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_panchakarma_other_treatment(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(PanchakarmaOtherTreatment, entity_id, "Panchakarma other treatment", db)


@router.get("/booking-slots", response_model=list[BookingSlotResponse])
def list_admin_booking_slots(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = (
        db.query(BookingSlot)
        .order_by(BookingSlot.booking_date.asc(), BookingSlot.start_time.asc(), BookingSlot.id.asc())
        .all()
    )
    return [as_booking_slot(item) for item in items]


@router.post("/booking-slots", response_model=BookingSlotResponse, status_code=status.HTTP_201_CREATED)
def create_booking_slot(payload: BookingSlotCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(BookingSlot, payload, db, is_active=as_active_flag(payload.is_active))
    return as_booking_slot(item)


@router.put("/booking-slots/{entity_id}", response_model=BookingSlotResponse)
def update_booking_slot(entity_id: int, payload: BookingSlotUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(BookingSlot, entity_id, "Booking slot", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_booking_slot(item)


@router.delete("/booking-slots/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking_slot(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(BookingSlot, entity_id, "Booking slot", db)


@router.get("/bookings", response_model=list[TherapyBookingResponse])
def list_admin_bookings(
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = db.query(TherapyBooking).order_by(TherapyBooking.booking_date.desc(), TherapyBooking.start_time.asc(), TherapyBooking.id.desc())
    if status_filter:
        query = query.filter(TherapyBooking.status == status_filter)
    return [as_therapy_booking(item) for item in query.all()]


@router.patch("/bookings/{booking_id}", response_model=TherapyBookingResponse)
def update_booking_status(
    booking_id: int,
    payload: TherapyBookingStatusUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(TherapyBooking, booking_id, "Booking", db)
    updates = payload.model_dump(exclude_none=True)
    therapist_name = item.therapist_name
    if payload.therapist_id:
        therapist = get_entity_or_404(Therapist, payload.therapist_id, "Therapist", db)
        therapist_name = therapist.full_name
        updates["therapist_name"] = therapist_name
    for field_name, field_value in updates.items():
        setattr(item, field_name, field_value)
    db.commit()
    db.refresh(item)
    return serialize_booking(item)


@router.get("/therapists", response_model=list[TherapistResponse])
def list_admin_therapists(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = db.query(Therapist).order_by(Therapist.full_name.asc(), Therapist.id.asc()).all()
    return [serialize_therapist(item) for item in items]


@router.post("/therapists", response_model=TherapistResponse, status_code=status.HTTP_201_CREATED)
def create_therapist(payload: TherapistCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(
        Therapist,
        payload,
        db,
        specialties=join_booking_lines(payload.specialties),
        is_active=as_active_flag(payload.is_active),
    )
    return serialize_therapist(item)


@router.put("/therapists/{entity_id}", response_model=TherapistResponse)
def update_therapist(entity_id: int, payload: TherapistUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(Therapist, entity_id, "Therapist", db)
    item = update_entity(
        item,
        payload,
        db,
        specialties=join_booking_lines(payload.specialties),
        is_active=as_active_flag(payload.is_active),
    )
    return serialize_therapist(item)


@router.delete("/therapists/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_therapist(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(Therapist, entity_id, "Therapist", db)


@router.get("/therapist-availabilities", response_model=list[TherapistAvailabilityResponse])
def list_admin_therapist_availabilities(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = (
        db.query(TherapistAvailability)
        .order_by(TherapistAvailability.day_of_week.asc(), TherapistAvailability.start_time.asc(), TherapistAvailability.id.asc())
        .all()
    )
    return [serialize_availability(item) for item in items]


@router.post("/therapist-availabilities", response_model=TherapistAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def create_therapist_availability(payload: TherapistAvailabilityCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(TherapistAvailability, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_availability(item)


@router.put("/therapist-availabilities/{entity_id}", response_model=TherapistAvailabilityResponse)
def update_therapist_availability(entity_id: int, payload: TherapistAvailabilityUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(TherapistAvailability, entity_id, "Therapist availability", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_availability(item)


@router.delete("/therapist-availabilities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_therapist_availability(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(TherapistAvailability, entity_id, "Therapist availability", db)


@router.get("/therapist-blackouts", response_model=list[TherapistBlackoutResponse])
def list_admin_therapist_blackouts(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = (
        db.query(TherapistBlackout)
        .order_by(TherapistBlackout.blackout_date.asc(), TherapistBlackout.start_time.asc(), TherapistBlackout.id.asc())
        .all()
    )
    return [serialize_blackout(item) for item in items]


@router.post("/therapist-blackouts", response_model=TherapistBlackoutResponse, status_code=status.HTTP_201_CREATED)
def create_therapist_blackout(payload: TherapistBlackoutCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(TherapistBlackout, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_blackout(item)


@router.put("/therapist-blackouts/{entity_id}", response_model=TherapistBlackoutResponse)
def update_therapist_blackout(entity_id: int, payload: TherapistBlackoutUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(TherapistBlackout, entity_id, "Therapist blackout", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_blackout(item)


@router.delete("/therapist-blackouts/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_therapist_blackout(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(TherapistBlackout, entity_id, "Therapist blackout", db)
