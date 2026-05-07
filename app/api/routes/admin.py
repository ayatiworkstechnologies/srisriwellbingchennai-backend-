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
    AdminBootstrapResponse,
    AdminLoginRequest,
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    AlternativeTreatmentCreate,
    AlternativeTreatmentResponse,
    AlternativeTreatmentUpdate,
    BookingSlotCreate,
    BookingClientEmailRequest,
    BookingClientEmailResponse,
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
from ...services.mail import (
    build_booking_status_email,
    build_custom_booking_email,
    send_email,
)
from ...security import create_access_token, verify_password
from ...services.content import (
    as_admin_user,
    as_alt,
    as_nadi_camp,
    as_pk_core,
    as_pk_other,
    as_relax,
    as_service,
    as_testimonial,
    join_lines,
)
from ..deps import get_current_admin, get_current_super_admin
from ...legacy import ACTIVE_FLAG_TRUE
from ...security import get_password_hash

router = APIRouter(prefix="/api/v1/admin")


@router.post("/auth/login", response_model=TokenResponse, tags=["Admin Auth"])
@router.post("/login", response_model=TokenResponse, include_in_schema=False)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if not admin or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if admin.is_active != ACTIVE_FLAG_TRUE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return TokenResponse(
        access_token=create_access_token(admin.email, role=admin.role, therapist_id=admin.therapist_id),
        role=admin.role,
        full_name=admin.full_name,
        therapist_id=admin.therapist_id,
    )


@router.get("/dashboard/stats", response_model=DashboardResponse, tags=["Admin Dashboard"])
@router.get("/dashboard", response_model=DashboardResponse, include_in_schema=False)
def admin_dashboard(current_admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    if current_admin.role == "doctor" and current_admin.therapist_id:
        return DashboardResponse(
            total_inquiries=0,
            new_inquiries=0,
            contacted_inquiries=0,
            closed_inquiries=0,
        )
    return DashboardResponse(
        total_inquiries=db.query(func.count(Inquiry.id)).scalar() or 0,
        new_inquiries=db.query(func.count(Inquiry.id)).filter(Inquiry.status == "new").scalar() or 0,
        contacted_inquiries=db.query(func.count(Inquiry.id)).filter(Inquiry.status == "contacted").scalar() or 0,
        closed_inquiries=db.query(func.count(Inquiry.id)).filter(Inquiry.status == "closed").scalar() or 0,
    )


@router.get("/bootstrap", response_model=AdminBootstrapResponse, tags=["Admin Dashboard"])
def admin_bootstrap(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
    booking_status: str | None = Query(default=None, alias="booking_status"),
):
    booking_query = db.query(TherapyBooking).order_by(
        TherapyBooking.booking_date.desc(),
        TherapyBooking.start_time.asc(),
        TherapyBooking.id.desc(),
    )
    if booking_status:
        booking_query = booking_query.filter(TherapyBooking.status == booking_status)
    if current_admin.role == "doctor":
        if not current_admin.therapist_id:
            return AdminBootstrapResponse(
                services=[],
                relaxation_therapies=[],
                therapists=[],
                bookings=[],
            )
        booking_query = booking_query.filter(TherapyBooking.therapist_id == current_admin.therapist_id)

    return AdminBootstrapResponse(
        services=[] if current_admin.role == "doctor" else [as_service(item) for item in list_entities(Service, db)],
        relaxation_therapies=[] if current_admin.role == "doctor" else [as_relax(item) for item in list_entities(RelaxationTherapy, db)],
        therapists=[] if current_admin.role == "doctor" else [
            serialize_therapist(item)
            for item in db.query(Therapist).order_by(Therapist.full_name.asc(), Therapist.id.asc()).all()
        ],
        bookings=[as_therapy_booking(item) for item in booking_query.all()],
    )


@router.get("/users", response_model=list[AdminUserResponse], tags=["Admin Auth"])
def list_admin_users(_: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    items = db.query(AdminUser).order_by(AdminUser.role.asc(), AdminUser.full_name.asc(), AdminUser.id.asc()).all()
    return [as_admin_user(item) for item in items]


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Auth"])
def create_admin_user(payload: AdminUserCreate, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    existing = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")
    if payload.role == "doctor" and not payload.therapist_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor login must be linked to a therapist")
    if payload.therapist_id:
        get_entity_or_404(Therapist, payload.therapist_id, "Therapist", db)
    item = AdminUser(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        therapist_id=payload.therapist_id,
        is_active=as_active_flag(payload.is_active),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return as_admin_user(item)


@router.put("/users/{user_id}", response_model=AdminUserResponse, tags=["Admin Auth"])
def update_admin_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_admin: AdminUser = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(AdminUser, user_id, "User", db)
    existing = db.query(AdminUser).filter(AdminUser.email == payload.email, AdminUser.id != user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")
    if item.id == current_admin.id and payload.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot remove your own super admin role")
    if payload.role == "doctor" and not payload.therapist_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor login must be linked to a therapist")
    if payload.therapist_id:
        get_entity_or_404(Therapist, payload.therapist_id, "Therapist", db)
    item.email = payload.email
    item.full_name = payload.full_name
    item.role = payload.role
    item.therapist_id = payload.therapist_id
    item.is_active = as_active_flag(payload.is_active)
    if payload.password:
        item.hashed_password = get_password_hash(payload.password)
    db.commit()
    db.refresh(item)
    return as_admin_user(item)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Auth"])
def delete_admin_user(
    user_id: int,
    current_admin: AdminUser = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(AdminUser, user_id, "User", db)
    if item.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")
    db.delete(item)
    db.commit()
    return None


@router.get("/crm/inquiries", response_model=list[InquiryResponse], tags=["Admin CRM"])
@router.get("/inquiries", response_model=list[InquiryResponse], include_in_schema=False)
def list_inquiries(
    _: AdminUser = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    source_filter: str | None = Query(default=None, alias="source"),
):
    query = db.query(Inquiry).order_by(Inquiry.created_at.desc())
    if status_filter:
        query = query.filter(Inquiry.status == status_filter)
    if source_filter:
        query = query.filter(func.lower(Inquiry.source) == source_filter.strip().lower())
    return query.all()


@router.get("/crm/inquiries/{inquiry_id}", response_model=InquiryResponse, tags=["Admin CRM"])
@router.get("/inquiries/{inquiry_id}", response_model=InquiryResponse, include_in_schema=False)
def get_inquiry(inquiry_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return get_entity_or_404(Inquiry, inquiry_id, "Inquiry", db)


@router.patch("/crm/inquiries/{inquiry_id}", response_model=InquiryResponse, tags=["Admin CRM"])
@router.patch("/inquiries/{inquiry_id}", response_model=InquiryResponse, include_in_schema=False)
def update_inquiry_status(
    inquiry_id: int,
    payload: InquiryStatusUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(Inquiry, inquiry_id, "Inquiry", db)
    return update_entity(item, payload, db)


@router.delete("/crm/inquiries/{inquiry_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin CRM"])
@router.delete("/inquiries/{inquiry_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_inquiry(
    inquiry_id: int,
    _: AdminUser = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    return delete_entity(Inquiry, inquiry_id, "Inquiry", db)


@router.get("/content/services", response_model=list[ServiceResponse], tags=["Admin Content"])
@router.get("/services", response_model=list[ServiceResponse], include_in_schema=False)
def list_admin_services(_: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    items = list_entities(Service, db)
    return [as_service(item) for item in items]


@router.get("/content/services/{entity_id}", response_model=ServiceResponse, tags=["Admin Content"])
@router.get("/services/{entity_id}", response_model=ServiceResponse, include_in_schema=False)
def get_service(entity_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return as_service(get_entity_or_404(Service, entity_id, "Service", db))


@router.post("/content/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_service(payload: ServiceCreate, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    item = create_entity(Service, payload, db, is_active=as_active_flag(payload.is_active))
    return as_service(item)


@router.put("/content/services/{entity_id}", response_model=ServiceResponse, tags=["Admin Content"])
@router.put("/services/{entity_id}", response_model=ServiceResponse, include_in_schema=False)
def update_service(entity_id: int, payload: ServiceUpdate, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(Service, entity_id, "Service", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_service(item)


@router.delete("/content/services/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
@router.delete("/services/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_service(entity_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return delete_entity(Service, entity_id, "Service", db)


@router.get("/content/testimonials", response_model=list[TestimonialResponse], tags=["Admin Content"])
@router.get("/testimonials", response_model=list[TestimonialResponse], include_in_schema=False)
def list_admin_testimonials(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(Testimonial, db)
    return [as_testimonial(item) for item in items]


@router.get("/content/testimonials/{entity_id}", response_model=TestimonialResponse, tags=["Admin Content"])
@router.get("/testimonials/{entity_id}", response_model=TestimonialResponse, include_in_schema=False)
def get_testimonial(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return as_testimonial(get_entity_or_404(Testimonial, entity_id, "Testimonial", db))


@router.post("/content/testimonials", response_model=TestimonialResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
@router.post("/testimonials", response_model=TestimonialResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_testimonial(payload: TestimonialCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(Testimonial, payload, db, is_active=as_active_flag(payload.is_active))
    return as_testimonial(item)


@router.put("/content/testimonials/{entity_id}", response_model=TestimonialResponse, tags=["Admin Content"])
@router.put("/testimonials/{entity_id}", response_model=TestimonialResponse, include_in_schema=False)
def update_testimonial(entity_id: int, payload: TestimonialUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(Testimonial, entity_id, "Testimonial", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_testimonial(item)


@router.delete("/content/testimonials/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
@router.delete("/testimonials/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_testimonial(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(Testimonial, entity_id, "Testimonial", db)


@router.get("/content/nadi-camps", response_model=list[NadiCampResponse], tags=["Admin Content"])
@router.get("/nadi-camps", response_model=list[NadiCampResponse], include_in_schema=False)
def list_admin_nadi_camps(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(NadiCamp, db)
    return [as_nadi_camp(item) for item in items]


@router.get("/content/nadi-camps/{entity_id}", response_model=NadiCampResponse, tags=["Admin Content"])
@router.get("/nadi-camps/{entity_id}", response_model=NadiCampResponse, include_in_schema=False)
def get_nadi_camp(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return as_nadi_camp(get_entity_or_404(NadiCamp, entity_id, "Nadi camp", db))


@router.post("/content/nadi-camps", response_model=NadiCampResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
@router.post("/nadi-camps", response_model=NadiCampResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_nadi_camp(payload: NadiCampCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(NadiCamp, payload, db, is_active=as_active_flag(payload.is_active))
    return as_nadi_camp(item)


@router.put("/content/nadi-camps/{entity_id}", response_model=NadiCampResponse, tags=["Admin Content"])
@router.put("/nadi-camps/{entity_id}", response_model=NadiCampResponse, include_in_schema=False)
def update_nadi_camp(entity_id: int, payload: NadiCampUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(NadiCamp, entity_id, "Nadi camp", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_nadi_camp(item)


@router.delete("/content/nadi-camps/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
@router.delete("/nadi-camps/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_nadi_camp(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(NadiCamp, entity_id, "Nadi camp", db)


@router.get("/content/relaxation-therapies", response_model=list[RelaxationTherapyResponse], tags=["Admin Content"])
@router.get("/relaxation-therapies", response_model=list[RelaxationTherapyResponse], include_in_schema=False)
def list_admin_relaxation_therapies(_: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    items = list_entities(RelaxationTherapy, db)
    return [as_relax(item) for item in items]


@router.get("/content/relaxation-therapies/{entity_id}", response_model=RelaxationTherapyResponse, tags=["Admin Content"])
@router.get("/relaxation-therapies/{entity_id}", response_model=RelaxationTherapyResponse, include_in_schema=False)
def get_relaxation_therapy(entity_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return as_relax(get_entity_or_404(RelaxationTherapy, entity_id, "Relaxation therapy", db))


@router.post("/content/relaxation-therapies", response_model=RelaxationTherapyResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
@router.post("/relaxation-therapies", response_model=RelaxationTherapyResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_relaxation_therapy(payload: RelaxationTherapyCreate, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    item = create_entity(
        RelaxationTherapy,
        payload,
        db,
        benefits=join_lines(payload.benefits),
        is_active=as_active_flag(payload.is_active),
    )
    return as_relax(item)


@router.put("/content/relaxation-therapies/{entity_id}", response_model=RelaxationTherapyResponse, tags=["Admin Content"])
@router.put("/relaxation-therapies/{entity_id}", response_model=RelaxationTherapyResponse, include_in_schema=False)
def update_relaxation_therapy(
    entity_id: int,
    payload: RelaxationTherapyUpdate,
    _: AdminUser = Depends(get_current_super_admin),
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


@router.delete("/content/relaxation-therapies/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
@router.delete("/relaxation-therapies/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_relaxation_therapy(entity_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return delete_entity(RelaxationTherapy, entity_id, "Relaxation therapy", db)


@router.get("/content/alternative-treatments", response_model=list[AlternativeTreatmentResponse], tags=["Admin Content"])
@router.get("/alternative-treatments", response_model=list[AlternativeTreatmentResponse], include_in_schema=False)
def list_admin_alternative_treatments(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(AlternativeTreatment, db)
    return [as_alt(item) for item in items]


@router.get("/content/alternative-treatments/{entity_id}", response_model=AlternativeTreatmentResponse, tags=["Admin Content"])
@router.get("/alternative-treatments/{entity_id}", response_model=AlternativeTreatmentResponse, include_in_schema=False)
def get_alternative_treatment(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return as_alt(get_entity_or_404(AlternativeTreatment, entity_id, "Alternative treatment", db))


@router.post("/content/alternative-treatments", response_model=AlternativeTreatmentResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
@router.post("/alternative-treatments", response_model=AlternativeTreatmentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_alternative_treatment(payload: AlternativeTreatmentCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(AlternativeTreatment, payload, db, is_active=as_active_flag(payload.is_active))
    return as_alt(item)


@router.put("/content/alternative-treatments/{entity_id}", response_model=AlternativeTreatmentResponse, tags=["Admin Content"])
@router.put("/alternative-treatments/{entity_id}", response_model=AlternativeTreatmentResponse, include_in_schema=False)
def update_alternative_treatment(
    entity_id: int,
    payload: AlternativeTreatmentUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(AlternativeTreatment, entity_id, "Alternative treatment", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_alt(item)


@router.delete("/content/alternative-treatments/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
@router.delete("/alternative-treatments/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_alternative_treatment(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(AlternativeTreatment, entity_id, "Alternative treatment", db)


@router.get("/content/panchakarma/core-therapies", response_model=list[PanchakarmaCoreTherapyResponse], tags=["Admin Content"])
@router.get("/panchakarma-core-therapies", response_model=list[PanchakarmaCoreTherapyResponse], include_in_schema=False)
def list_admin_panchakarma_core_therapies(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(PanchakarmaCoreTherapy, db)
    return [as_pk_core(item) for item in items]


@router.get("/content/panchakarma/core-therapies/{entity_id}", response_model=PanchakarmaCoreTherapyResponse, tags=["Admin Content"])
@router.get("/panchakarma-core-therapies/{entity_id}", response_model=PanchakarmaCoreTherapyResponse, include_in_schema=False)
def get_panchakarma_core_therapy(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return as_pk_core(get_entity_or_404(PanchakarmaCoreTherapy, entity_id, "Panchakarma core therapy", db))


@router.post("/content/panchakarma/core-therapies", response_model=PanchakarmaCoreTherapyResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
@router.post("/panchakarma-core-therapies", response_model=PanchakarmaCoreTherapyResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
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


@router.put("/content/panchakarma/core-therapies/{entity_id}", response_model=PanchakarmaCoreTherapyResponse, tags=["Admin Content"])
@router.put("/panchakarma-core-therapies/{entity_id}", response_model=PanchakarmaCoreTherapyResponse, include_in_schema=False)
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


@router.delete("/content/panchakarma/core-therapies/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
@router.delete("/panchakarma-core-therapies/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_panchakarma_core_therapy(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(PanchakarmaCoreTherapy, entity_id, "Panchakarma core therapy", db)


@router.get("/content/panchakarma/other-treatments", response_model=list[PanchakarmaOtherTreatmentResponse], tags=["Admin Content"])
@router.get("/panchakarma-other-treatments", response_model=list[PanchakarmaOtherTreatmentResponse], include_in_schema=False)
def list_admin_panchakarma_other_treatments(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = list_entities(PanchakarmaOtherTreatment, db)
    return [as_pk_other(item) for item in items]


@router.get("/content/panchakarma/other-treatments/{entity_id}", response_model=PanchakarmaOtherTreatmentResponse, tags=["Admin Content"])
@router.get("/panchakarma-other-treatments/{entity_id}", response_model=PanchakarmaOtherTreatmentResponse, include_in_schema=False)
def get_panchakarma_other_treatment(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return as_pk_other(get_entity_or_404(PanchakarmaOtherTreatment, entity_id, "Panchakarma other treatment", db))


@router.post("/content/panchakarma/other-treatments", response_model=PanchakarmaOtherTreatmentResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Content"])
@router.post("/panchakarma-other-treatments", response_model=PanchakarmaOtherTreatmentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_panchakarma_other_treatment(
    payload: PanchakarmaOtherTreatmentCreate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = create_entity(PanchakarmaOtherTreatment, payload, db, is_active=as_active_flag(payload.is_active))
    return as_pk_other(item)


@router.put("/content/panchakarma/other-treatments/{entity_id}", response_model=PanchakarmaOtherTreatmentResponse, tags=["Admin Content"])
@router.put("/panchakarma-other-treatments/{entity_id}", response_model=PanchakarmaOtherTreatmentResponse, include_in_schema=False)
def update_panchakarma_other_treatment(
    entity_id: int,
    payload: PanchakarmaOtherTreatmentUpdate,
    _: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(PanchakarmaOtherTreatment, entity_id, "Panchakarma other treatment", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_pk_other(item)


@router.delete("/content/panchakarma/other-treatments/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Content"])
@router.delete("/panchakarma-other-treatments/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_panchakarma_other_treatment(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(PanchakarmaOtherTreatment, entity_id, "Panchakarma other treatment", db)


@router.get("/booking/slots", response_model=list[BookingSlotResponse], tags=["Admin Booking"])
@router.get("/booking-slots", response_model=list[BookingSlotResponse], include_in_schema=False)
def list_admin_booking_slots(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = (
        db.query(BookingSlot)
        .order_by(BookingSlot.booking_date.asc(), BookingSlot.start_time.asc(), BookingSlot.id.asc())
        .all()
    )
    return [as_booking_slot(item) for item in items]


@router.get("/booking/slots/{entity_id}", response_model=BookingSlotResponse, tags=["Admin Booking"])
@router.get("/booking-slots/{entity_id}", response_model=BookingSlotResponse, include_in_schema=False)
def get_booking_slot(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return as_booking_slot(get_entity_or_404(BookingSlot, entity_id, "Booking slot", db))


@router.post("/booking/slots", response_model=BookingSlotResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Booking"])
@router.post("/booking-slots", response_model=BookingSlotResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_booking_slot(payload: BookingSlotCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(BookingSlot, payload, db, is_active=as_active_flag(payload.is_active))
    return as_booking_slot(item)


@router.put("/booking/slots/{entity_id}", response_model=BookingSlotResponse, tags=["Admin Booking"])
@router.put("/booking-slots/{entity_id}", response_model=BookingSlotResponse, include_in_schema=False)
def update_booking_slot(entity_id: int, payload: BookingSlotUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(BookingSlot, entity_id, "Booking slot", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return as_booking_slot(item)


@router.delete("/booking/slots/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Booking"])
@router.delete("/booking-slots/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_booking_slot(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(BookingSlot, entity_id, "Booking slot", db)


@router.get("/booking/appointments", response_model=list[TherapyBookingResponse], tags=["Admin Booking"])
@router.get("/bookings", response_model=list[TherapyBookingResponse], include_in_schema=False)
def list_admin_bookings(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = db.query(TherapyBooking).order_by(TherapyBooking.booking_date.desc(), TherapyBooking.start_time.asc(), TherapyBooking.id.desc())
    if status_filter:
        query = query.filter(TherapyBooking.status == status_filter)
    if current_admin.role == "doctor":
        if not current_admin.therapist_id:
            return []
        query = query.filter(TherapyBooking.therapist_id == current_admin.therapist_id)
    return [as_therapy_booking(item) for item in query.all()]


@router.get("/booking/appointments/{booking_id}", response_model=TherapyBookingResponse, tags=["Admin Booking"])
@router.get("/bookings/{booking_id}", response_model=TherapyBookingResponse, include_in_schema=False)
def get_booking(booking_id: int, current_admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(TherapyBooking, booking_id, "Booking", db)
    if current_admin.role == "doctor" and item.therapist_id != current_admin.therapist_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this booking")
    return as_therapy_booking(item)


@router.patch("/booking/appointments/{booking_id}", response_model=TherapyBookingResponse, tags=["Admin Booking"])
@router.patch("/bookings/{booking_id}", response_model=TherapyBookingResponse, include_in_schema=False)
def update_booking_status(
    booking_id: int,
    payload: TherapyBookingStatusUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(TherapyBooking, booking_id, "Booking", db)
    if current_admin.role == "doctor" and item.therapist_id != current_admin.therapist_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this booking")
    updates = payload.model_dump(exclude_none=True)
    send_status_email = updates.pop("send_email", False)
    email_message = updates.pop("email_message", None)
    if "therapist_id" in payload.model_fields_set and payload.therapist_id is None:
        updates["therapist_id"] = None
        updates["therapist_name"] = None
    elif payload.therapist_id:
        therapist = get_entity_or_404(Therapist, payload.therapist_id, "Therapist", db)
        updates["therapist_name"] = therapist.full_name
    for field_name, field_value in updates.items():
        setattr(item, field_name, field_value)
    db.commit()
    db.refresh(item)

    if send_status_email:
        email_payload = build_booking_status_email(item, email_message)
        send_email(
            to_email=item.email,
            subject=email_payload["subject"],
            html_body=email_payload["html"],
            text_body=email_payload["text"],
        )

    return serialize_booking(item)


@router.post(
    "/booking/appointments/{booking_id}/send-email",
    response_model=BookingClientEmailResponse,
    tags=["Admin Booking"],
)
@router.post(
    "/bookings/{booking_id}/send-email",
    response_model=BookingClientEmailResponse,
    include_in_schema=False,
)
def send_booking_email(
    booking_id: int,
    payload: BookingClientEmailRequest,
    _: AdminUser = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    item = get_entity_or_404(TherapyBooking, booking_id, "Booking", db)
    email_payload = build_custom_booking_email(item, payload.subject, payload.message)
    send_email(
        to_email=item.email,
        subject=email_payload["subject"],
        html_body=email_payload["html"],
        text_body=email_payload["text"],
    )
    return BookingClientEmailResponse(
        detail="Email sent successfully",
        recipient=item.email,
        subject=email_payload["subject"],
    )


@router.delete("/booking/appointments/{booking_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Booking"])
@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_booking(booking_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return delete_entity(TherapyBooking, booking_id, "Booking", db)


@router.get("/booking/therapists", response_model=list[TherapistResponse], tags=["Admin Booking"])
@router.get("/therapists", response_model=list[TherapistResponse], include_in_schema=False)
def list_admin_therapists(_: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    items = db.query(Therapist).order_by(Therapist.full_name.asc(), Therapist.id.asc()).all()
    return [serialize_therapist(item) for item in items]


@router.get("/booking/therapists/{entity_id}", response_model=TherapistResponse, tags=["Admin Booking"])
@router.get("/therapists/{entity_id}", response_model=TherapistResponse, include_in_schema=False)
def get_therapist(entity_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return serialize_therapist(get_entity_or_404(Therapist, entity_id, "Therapist", db))


@router.post("/booking/therapists", response_model=TherapistResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Booking"])
@router.post("/therapists", response_model=TherapistResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_therapist(payload: TherapistCreate, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    item = create_entity(
        Therapist,
        payload,
        db,
        specialties=join_booking_lines(payload.specialties),
        is_active=as_active_flag(payload.is_active),
    )
    return serialize_therapist(item)


@router.put("/booking/therapists/{entity_id}", response_model=TherapistResponse, tags=["Admin Booking"])
@router.put("/therapists/{entity_id}", response_model=TherapistResponse, include_in_schema=False)
def update_therapist(entity_id: int, payload: TherapistUpdate, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(Therapist, entity_id, "Therapist", db)
    item = update_entity(
        item,
        payload,
        db,
        specialties=join_booking_lines(payload.specialties),
        is_active=as_active_flag(payload.is_active),
    )
    return serialize_therapist(item)


@router.delete("/booking/therapists/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Booking"])
@router.delete("/therapists/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_therapist(entity_id: int, _: AdminUser = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return delete_entity(Therapist, entity_id, "Therapist", db)


@router.get("/booking/therapist-availabilities", response_model=list[TherapistAvailabilityResponse], tags=["Admin Booking"])
@router.get("/therapist-availabilities", response_model=list[TherapistAvailabilityResponse], include_in_schema=False)
def list_admin_therapist_availabilities(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = (
        db.query(TherapistAvailability)
        .order_by(TherapistAvailability.day_of_week.asc(), TherapistAvailability.start_time.asc(), TherapistAvailability.id.asc())
        .all()
    )
    return [serialize_availability(item) for item in items]


@router.get("/booking/therapist-availabilities/{entity_id}", response_model=TherapistAvailabilityResponse, tags=["Admin Booking"])
@router.get("/therapist-availabilities/{entity_id}", response_model=TherapistAvailabilityResponse, include_in_schema=False)
def get_therapist_availability(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return serialize_availability(get_entity_or_404(TherapistAvailability, entity_id, "Therapist availability", db))


@router.post("/booking/therapist-availabilities", response_model=TherapistAvailabilityResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Booking"])
@router.post("/therapist-availabilities", response_model=TherapistAvailabilityResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_therapist_availability(payload: TherapistAvailabilityCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(TherapistAvailability, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_availability(item)


@router.put("/booking/therapist-availabilities/{entity_id}", response_model=TherapistAvailabilityResponse, tags=["Admin Booking"])
@router.put("/therapist-availabilities/{entity_id}", response_model=TherapistAvailabilityResponse, include_in_schema=False)
def update_therapist_availability(entity_id: int, payload: TherapistAvailabilityUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(TherapistAvailability, entity_id, "Therapist availability", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_availability(item)


@router.delete("/booking/therapist-availabilities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Booking"])
@router.delete("/therapist-availabilities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_therapist_availability(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(TherapistAvailability, entity_id, "Therapist availability", db)


@router.get("/booking/therapist-blackouts", response_model=list[TherapistBlackoutResponse], tags=["Admin Booking"])
@router.get("/therapist-blackouts", response_model=list[TherapistBlackoutResponse], include_in_schema=False)
def list_admin_therapist_blackouts(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = (
        db.query(TherapistBlackout)
        .order_by(TherapistBlackout.blackout_date.asc(), TherapistBlackout.start_time.asc(), TherapistBlackout.id.asc())
        .all()
    )
    return [serialize_blackout(item) for item in items]


@router.get("/booking/therapist-blackouts/{entity_id}", response_model=TherapistBlackoutResponse, tags=["Admin Booking"])
@router.get("/therapist-blackouts/{entity_id}", response_model=TherapistBlackoutResponse, include_in_schema=False)
def get_therapist_blackout(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return serialize_blackout(get_entity_or_404(TherapistBlackout, entity_id, "Therapist blackout", db))


@router.post("/booking/therapist-blackouts", response_model=TherapistBlackoutResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Booking"])
@router.post("/therapist-blackouts", response_model=TherapistBlackoutResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_therapist_blackout(payload: TherapistBlackoutCreate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = create_entity(TherapistBlackout, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_blackout(item)


@router.put("/booking/therapist-blackouts/{entity_id}", response_model=TherapistBlackoutResponse, tags=["Admin Booking"])
@router.put("/therapist-blackouts/{entity_id}", response_model=TherapistBlackoutResponse, include_in_schema=False)
def update_therapist_blackout(entity_id: int, payload: TherapistBlackoutUpdate, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = get_entity_or_404(TherapistBlackout, entity_id, "Therapist blackout", db)
    item = update_entity(item, payload, db, is_active=as_active_flag(payload.is_active))
    return serialize_blackout(item)


@router.delete("/booking/therapist-blackouts/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Booking"])
@router.delete("/therapist-blackouts/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_therapist_blackout(entity_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_entity(TherapistBlackout, entity_id, "Therapist blackout", db)
