from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal
from ..legacy import is_active_flag
from ..models import (
    AdminUser,
    AlternativeTreatment,
    NadiCamp,
    PanchakarmaCoreTherapy,
    PanchakarmaOtherTreatment,
    RelaxationTherapy,
    Service,
    Testimonial,
)
from ..schemas import (
    AlternativeTreatmentResponse,
    NadiCampResponse,
    PanchakarmaCoreTherapyResponse,
    PanchakarmaOtherTreatmentResponse,
    RelaxationTherapyResponse,
    ServiceResponse,
    TestimonialResponse,
)
from ..security import get_password_hash

settings = get_settings()


def split_lines(value: str) -> list[str]:
    return [item.strip() for item in value.splitlines() if item.strip()]


def join_lines(items: list[str]) -> str:
    return "\n".join([item.strip() for item in items if item.strip()])


def seed_admin_user() -> None:
    db = SessionLocal()
    try:
        existing_admin = db.query(AdminUser).filter(AdminUser.email == settings.admin_email).first()
        hashed_password = get_password_hash(settings.admin_password)
        if existing_admin:
            existing_admin.full_name = "Sri Sri Wellbeing Admin"
            existing_admin.hashed_password = hashed_password
        else:
            db.add(
                AdminUser(
                    email=settings.admin_email,
                    full_name="Sri Sri Wellbeing Admin",
                    hashed_password=hashed_password,
                )
            )
        db.commit()
    finally:
        db.close()


def seed_default_content() -> None:
    db = SessionLocal()
    try:
        _seed_services(db)
        _seed_testimonials(db)
        _seed_nadi_camps(db)
        _seed_relaxation_therapies(db)
        db.commit()
    finally:
        db.close()


def _seed_services(db: Session) -> None:
    if db.query(Service).first():
        return

    db.add_all(
        [
            Service(title="Nadi Pariksha", description="A non-invasive Ayurvedic pulse diagnosis technique used by our practitioners to assess your doshas and identify imbalances, serving as the starting point for your personalized wellness journey.", image="/images/ser-1.jpg", sort_order=1),
            Service(title="Panchakarma Rituals", description="A comprehensive Ayurvedic detoxification and cleansing program designed to eliminate deep-seated toxins and effectively restore balance to the body and mind.", image="/images/ser-2.jpg", sort_order=2),
            Service(title="Marma Therapy", description="An Ayurvedic technique involving gentle stimulation of specific vital energy points on the body to improve energy flow, reduce stress, and support deep healing.", image="/images/ser-3.jpg", sort_order=3),
            Service(title="Osteopathic Therapy", description="A manual therapy focused on the body's musculoskeletal system, aiming to improve overall health by strengthening the framework of the body and managing pain.", image="/images/ser-4.jpg", sort_order=4),
        ]
    )


def _seed_testimonials(db: Session) -> None:
    if db.query(Testimonial).first():
        return

    db.add_all(
        [
            Testimonial(name="Anusha Rajan", review="A deeply soothing and authentic experience. Netra Tejas felt gentle yet remarkably effective, bringing clarity and comfort in the most natural way. A refined approach to non-invasive care that truly delivers.", sort_order=1),
            Testimonial(name="Muthukrishnan Gopal", review="An exceptional destination for authentic Ayurvedic care. The experience is thoughtfully curated, offering both depth and genuine healing in a calm, welcoming environment.", sort_order=2),
        ]
    )


def _seed_nadi_camps(db: Session) -> None:
    if db.query(NadiCamp).first():
        return

    db.add_all(
        [
            NadiCamp(doctor="Dr. K Aravindhan", camp_date="20/05/2026", location="Chennai, Tamil Nadu", contact="Manickam M (9444004975)", address="Gurukripa Agencies, No : 16, Aadhi Street, Villivakkam", sort_order=1),
            NadiCamp(doctor="Dr. Priya Narayanan", camp_date="28/05/2026", location="Coimbatore, Tamil Nadu", contact="Sathish K (9876543210)", address="No. 24, Wellness Avenue, RS Puram, Coimbatore", sort_order=2),
        ]
    )


def _seed_relaxation_therapies(db: Session) -> None:
    if db.query(RelaxationTherapy).first():
        return

    db.add_all(
        [
            RelaxationTherapy(title="Abhyanga", duration="45 mins", short_description="An Ayurvedic procedure involving warm medicated oil and gentle massage for relaxation.", details="Abhyanga is a traditional Ayurvedic full-body oil massage using warm herbal oils. It helps relax the body, improve blood circulation, nourish the skin, reduce fatigue, and calm the nervous system.", benefits=join_lines(["Relieves stress and tiredness", "Improves blood circulation", "Nourishes skin and body tissues", "Supports better sleep", "Helps relax muscles"]), image="/images/1446.jpg", sort_order=1),
            RelaxationTherapy(title="Shirodhara", duration="45 mins", short_description="A signature Ayurvedic therapy where warm oil is poured continuously over the forehead.", details="Shirodhara is a deeply calming therapy where warm medicated oil flows gently over the forehead. It is commonly used for stress relief, mental relaxation, sleep support, and emotional balance.", benefits=join_lines(["Calms the mind", "Reduces stress and anxiety", "Promotes better sleep", "Supports mental clarity", "Deep relaxation"]), image="/images/1446.jpg", sort_order=2),
        ]
    )


def as_service(item: Service) -> ServiceResponse:
    return ServiceResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        image=item.image,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_testimonial(item: Testimonial) -> TestimonialResponse:
    return TestimonialResponse(
        id=item.id,
        name=item.name,
        review=item.review,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_nadi_camp(item: NadiCamp) -> NadiCampResponse:
    return NadiCampResponse(
        id=item.id,
        doctor=item.doctor,
        camp_date=item.camp_date,
        location=item.location,
        contact=item.contact,
        address=item.address,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_relax(item: RelaxationTherapy) -> RelaxationTherapyResponse:
    return RelaxationTherapyResponse(
        id=item.id,
        title=item.title,
        duration=item.duration,
        short_description=item.short_description,
        details=item.details,
        benefits=split_lines(item.benefits),
        image=item.image,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_alt(item: AlternativeTreatment) -> AlternativeTreatmentResponse:
    return AlternativeTreatmentResponse(
        id=item.id,
        item_id=item.item_id,
        name=item.name,
        category=item.category,
        short_desc=item.short_desc,
        image=item.image,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_pk_core(item: PanchakarmaCoreTherapy) -> PanchakarmaCoreTherapyResponse:
    return PanchakarmaCoreTherapyResponse(
        id=item.id,
        item_id=item.item_id,
        name=item.name,
        dosha=item.dosha,
        dosha_color=item.dosha_color,
        dosha_bg=item.dosha_bg,
        dosha_border=item.dosha_border,
        short_desc=item.short_desc,
        image=item.image,
        benefits=split_lines(item.benefits),
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )


def as_pk_other(item: PanchakarmaOtherTreatment) -> PanchakarmaOtherTreatmentResponse:
    return PanchakarmaOtherTreatmentResponse(
        id=item.id,
        name=item.name,
        category=item.category,
        desc=item.desc,
        sort_order=item.sort_order,
        is_active=is_active_flag(item.is_active),
        created_at=item.created_at,
    )
