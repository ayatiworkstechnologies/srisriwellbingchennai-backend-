from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


InquiryStatus = Literal["new", "contacted", "closed"]
BookingStatus = Literal["pending", "confirmed", "rescheduled", "completed", "cancelled", "no_show"]


class InquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=6, max_length=50)
    email: EmailStr
    topic: str = Field(min_length=2, max_length=100)
    message: str = Field(min_length=10, max_length=5000)


class InquiryResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: EmailStr
    topic: str
    message: str
    status: InquiryStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InquiryStatusUpdate(BaseModel):
    status: InquiryStatus


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DashboardResponse(BaseModel):
    total_inquiries: int
    new_inquiries: int
    contacted_inquiries: int
    closed_inquiries: int


class ContentCategoryResponse(BaseModel):
    category: str
    item_count: int


class ServiceBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10, max_length=5000)
    image: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    pass


class ServiceResponse(ServiceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestimonialBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    review: str = Field(min_length=10, max_length=5000)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class TestimonialCreate(TestimonialBase):
    pass


class TestimonialUpdate(TestimonialBase):
    pass


class TestimonialResponse(TestimonialBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NadiCampBase(BaseModel):
    doctor: str = Field(min_length=2, max_length=255)
    camp_date: str = Field(min_length=4, max_length=50)
    location: str = Field(min_length=2, max_length=255)
    contact: str = Field(min_length=2, max_length=255)
    address: str = Field(min_length=5, max_length=5000)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class NadiCampCreate(NadiCampBase):
    pass


class NadiCampUpdate(NadiCampBase):
    pass


class NadiCampResponse(NadiCampBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RelaxationTherapyBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    duration: str = Field(min_length=2, max_length=50)
    short_description: str = Field(min_length=10, max_length=5000)
    details: str = Field(min_length=10, max_length=10000)
    benefits: list[str] = Field(min_length=1)
    image: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class RelaxationTherapyCreate(RelaxationTherapyBase):
    pass


class RelaxationTherapyUpdate(RelaxationTherapyBase):
    pass


class RelaxationTherapyResponse(RelaxationTherapyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlternativeTreatmentBase(BaseModel):
    item_id: str = Field(min_length=2, max_length=255)
    name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=255)
    short_desc: str = Field(min_length=10, max_length=5000)
    image: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class AlternativeTreatmentCreate(AlternativeTreatmentBase):
    pass


class AlternativeTreatmentUpdate(AlternativeTreatmentBase):
    pass


class AlternativeTreatmentResponse(AlternativeTreatmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PanchakarmaCoreTherapyBase(BaseModel):
    item_id: str = Field(min_length=2, max_length=255)
    name: str = Field(min_length=2, max_length=255)
    dosha: str = Field(min_length=2, max_length=255)
    dosha_color: str = Field(min_length=2, max_length=255)
    dosha_bg: str = Field(min_length=2, max_length=255)
    dosha_border: str = Field(min_length=2, max_length=255)
    short_desc: str = Field(min_length=10, max_length=5000)
    image: str = Field(min_length=1, max_length=255)
    benefits: list[str] = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class PanchakarmaCoreTherapyCreate(PanchakarmaCoreTherapyBase):
    pass


class PanchakarmaCoreTherapyUpdate(PanchakarmaCoreTherapyBase):
    pass


class PanchakarmaCoreTherapyResponse(PanchakarmaCoreTherapyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PanchakarmaOtherTreatmentBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=255)
    desc: str = Field(min_length=10, max_length=10000)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class PanchakarmaOtherTreatmentCreate(PanchakarmaOtherTreatmentBase):
    pass


class PanchakarmaOtherTreatmentUpdate(PanchakarmaOtherTreatmentBase):
    pass


class PanchakarmaOtherTreatmentResponse(PanchakarmaOtherTreatmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingSlotBase(BaseModel):
    therapy_name: str = Field(min_length=2, max_length=255)
    booking_date: date
    start_time: time
    end_time: time
    capacity: int = Field(default=1, ge=1, le=100)
    is_active: bool = True


class BookingSlotCreate(BookingSlotBase):
    pass


class BookingSlotUpdate(BookingSlotBase):
    pass


class BookingSlotResponse(BookingSlotBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicBookingSlotResponse(BookingSlotResponse):
    remaining_capacity: int


class TherapistBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=50)
    specialties: list[str] = Field(default_factory=list)
    bio: str = Field(default="", max_length=5000)
    is_active: bool = True


class TherapistCreate(TherapistBase):
    pass


class TherapistUpdate(TherapistBase):
    pass


class TherapistResponse(TherapistBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TherapistAvailabilityBase(BaseModel):
    therapist_id: int = Field(ge=1)
    therapy_name: str = Field(min_length=2, max_length=255)
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    slot_interval_minutes: int = Field(default=45, ge=15, le=240)
    max_bookings_per_slot: int = Field(default=1, ge=1, le=20)
    is_active: bool = True


class TherapistAvailabilityCreate(TherapistAvailabilityBase):
    pass


class TherapistAvailabilityUpdate(TherapistAvailabilityBase):
    pass


class TherapistAvailabilityResponse(TherapistAvailabilityBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TherapistBlackoutBase(BaseModel):
    therapist_id: int = Field(ge=1)
    blackout_date: date
    start_time: time | None = None
    end_time: time | None = None
    reason: str = Field(default="", max_length=5000)
    is_active: bool = True


class TherapistBlackoutCreate(TherapistBlackoutBase):
    pass


class TherapistBlackoutUpdate(TherapistBlackoutBase):
    pass


class TherapistBlackoutResponse(TherapistBlackoutBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicTherapyAvailabilityResponse(BaseModel):
    therapist_id: int
    therapist_name: str
    therapy_name: str
    booking_date: date
    start_time: time
    end_time: time
    remaining_capacity: int


class TherapyBookingCreate(BaseModel):
    therapy_name: str = Field(min_length=2, max_length=255)
    customer_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=6, max_length=50)
    email: EmailStr
    therapist_id: int = Field(ge=1)
    booking_date: date
    slot_id: int = Field(default=0, ge=0)
    start_time: time
    end_time: time
    notes: str | None = Field(default=None, max_length=2000)


class TherapyBookingResponse(BaseModel):
    id: int
    reference_code: str
    therapy_name: str
    customer_name: str
    phone: str
    email: EmailStr
    therapist_id: int | None = None
    therapist_name: str | None = None
    booking_date: date
    slot_id: int
    start_time: time
    end_time: time
    notes: str | None = None
    status: BookingStatus
    cancellation_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TherapyBookingStatusUpdate(BaseModel):
    status: BookingStatus | None = None
    therapist_id: int | None = Field(default=None, ge=1)
    booking_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    cancellation_reason: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)


class BookingCancelRequest(BaseModel):
    reference_code: str = Field(min_length=4, max_length=32)
    email: EmailStr
    reason: str | None = Field(default=None, max_length=2000)


class BookingCancelResponse(BaseModel):
    detail: str
    reference_code: str
    status: BookingStatus
