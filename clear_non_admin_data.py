from sqlalchemy import text

from app.database import SessionLocal
from app.models import (
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


MODELS_TO_CLEAR = [
    Inquiry,
    TherapyBooking,
    BookingSlot,
    TherapistAvailability,
    TherapistBlackout,
    Therapist,
    Service,
    Testimonial,
    NadiCamp,
    RelaxationTherapy,
    AlternativeTreatment,
    PanchakarmaCoreTherapy,
    PanchakarmaOtherTreatment,
]


def main() -> None:
    db = SessionLocal()
    try:
        cleared = {}

        # Keep login credentials, but detach them from therapist rows that are being cleared.
        db.query(AdminUser).update({AdminUser.therapist_id: None}, synchronize_session=False)

        for model in MODELS_TO_CLEAR:
            cleared[model.__tablename__] = db.query(model).delete(synchronize_session=False)

        db.commit()

        for model in MODELS_TO_CLEAR:
            db.execute(text(f"ALTER TABLE {model.__tablename__} AUTO_INCREMENT = 1"))

        db.commit()

        print("Database cleanup complete.")
        print("Preserved table: admin_users")
        for table_name, count in cleared.items():
            print(f"{table_name}: deleted {count}")
        print("Auto-increment counters reset for cleared tables.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
