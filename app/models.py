from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Sri Sri Wellbeing Admin")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="super_admin", index=True)
    therapist_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    service_interest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_path: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Testimonial(Base):
    __tablename__ = "testimonials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    review: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NadiCamp(Base):
    __tablename__ = "nadi_camps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor: Mapped[str] = mapped_column(String(255), nullable=False)
    camp_date: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RelaxationTherapy(Base):
    __tablename__ = "relaxation_therapies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[str] = mapped_column(String(50), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    benefits: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class AlternativeTreatment(Base):
    __tablename__ = "alternative_treatments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    short_desc: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class PanchakarmaCoreTherapy(Base):
    __tablename__ = "panchakarma_core_therapies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosha: Mapped[str] = mapped_column(String(255), nullable=False)
    dosha_color: Mapped[str] = mapped_column(String(255), nullable=False)
    dosha_bg: Mapped[str] = mapped_column(String(255), nullable=False)
    dosha_border: Mapped[str] = mapped_column(String(255), nullable=False)
    short_desc: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=False)
    benefits: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class PanchakarmaOtherTreatment(Base):
    __tablename__ = "panchakarma_other_treatments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    desc: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class BookingSlot(Base):
    __tablename__ = "booking_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    therapy_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Therapist(Base):
    __tablename__ = "therapists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    specialties: Mapped[str] = mapped_column(Text, nullable=False, default="")
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class TherapistAvailability(Base):
    __tablename__ = "therapist_availabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    therapist_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    therapy_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    max_bookings_per_slot: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class TherapistBlackout(Base):
    __tablename__ = "therapist_blackouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    therapist_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    blackout_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class TherapyBooking(Base):
    __tablename__ = "therapy_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    cancel_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    therapy_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    therapist_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    therapist_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    slot_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
