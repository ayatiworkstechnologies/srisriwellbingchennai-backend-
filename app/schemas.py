from datetime import date, datetime, time
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


InquiryStatus = Literal["new", "contacted", "closed"]
BookingStatus = Literal["pending", "confirmed", "rescheduled", "completed", "cancelled", "no_show"]
UserRole = Literal["super_admin", "doctor", "therapist"]


class InquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=6, max_length=50)
    email: EmailStr
    topic: str = Field(min_length=2, max_length=100)
    message: str = Field(min_length=10, max_length=5000)
    source: str | None = Field(default=None, min_length=2, max_length=100)
    service_interest: str | None = Field(default=None, min_length=2, max_length=255)
    page_path: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("source", "service_interest", "page_path", mode="before")
    @classmethod
    def normalize_optional_text(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class LeadInquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=6, max_length=50)
    email: EmailStr
    topic: str | None = Field(default=None, min_length=2, max_length=100)
    service_interest: str | None = Field(default=None, min_length=2, max_length=255)
    message: str | None = Field(default=None, min_length=2, max_length=5000)
    source: str | None = Field(default=None, min_length=2, max_length=100)
    page_path: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("topic", "service_interest", "message", "source", "page_path", mode="before")
    @classmethod
    def normalize_nullable_text(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def require_some_context(self):
        if self.topic or self.service_interest or self.message:
            return self
        raise ValueError("At least one of topic, service_interest, or message is required")


class InquiryResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: EmailStr
    topic: str
    message: str
    source: str | None = None
    service_interest: str | None = None
    page_path: str | None = None
    status: InquiryStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InquiryStatusUpdate(BaseModel):
    status: InquiryStatus


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    detail: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=2000)
    password: str = Field(min_length=6, max_length=128)


class ResetPasswordResponse(BaseModel):
    detail: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole = "super_admin"
    full_name: str | None = None
    therapist_id: int | None = None


class HealthResponse(BaseModel):
    status: str


class DashboardResponse(BaseModel):
    total_inquiries: int
    new_inquiries: int
    contacted_inquiries: int
    closed_inquiries: int


class AdminBootstrapResponse(BaseModel):
    services: list["ServiceResponse"]
    relaxation_therapies: list["RelaxationTherapyResponse"]
    therapists: list["TherapistResponse"]
    bookings: list["TherapyBookingResponse"]


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = "doctor"
    therapist_id: int | None = Field(default=None, ge=1)
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    role: UserRole = "doctor"
    therapist_id: int | None = Field(default=None, ge=1)
    is_active: bool = True


class AdminUserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    therapist_id: int | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentCategoryResponse(BaseModel):
    category: str
    item_count: int


class ServiceBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=2, max_length=255)
    short_description: str | None = Field(
        default=None,
        max_length=5000,
        validation_alias=AliasChoices("short_description", "shortDescription"),
    )
    description: str | None = Field(default=None, max_length=5000)
    benefits: list[str] = Field(min_length=1)
    image: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("title", "short_description", "description", "image", mode="before")
    @classmethod
    def strip_service_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("benefits", mode="before")
    @classmethod
    def normalize_service_benefits(cls, value):
        if isinstance(value, str):
            value = value.splitlines()
        if isinstance(value, list):
            cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            return cleaned
        return value

    @model_validator(mode="after")
    def ensure_service_descriptions(self):
        if not self.short_description and not self.description:
            raise ValueError("Either short description or public description is required")
        if not self.short_description and self.description:
            self.short_description = self.description
        if not self.description and self.short_description:
            self.description = self.short_description
        return self


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
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=2, max_length=255)
    duration: str = Field(min_length=2, max_length=50)
    short_description: str | None = Field(
        default=None,
        max_length=5000,
        validation_alias=AliasChoices("short_description", "shortDescription"),
    )
    details: str | None = Field(default=None, max_length=10000)
    benefits: list[str] = Field(min_length=1)
    image: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("title", "duration", "short_description", "details", "image", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("benefits", mode="before")
    @classmethod
    def normalize_benefits(cls, value):
        if isinstance(value, str):
            value = value.splitlines()
        if isinstance(value, list):
            cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            return cleaned
        return value

    @model_validator(mode="after")
    def ensure_relaxation_descriptions(self):
        if not self.short_description and not self.details:
            raise ValueError("Either short description or deep details is required")
        if not self.short_description and self.details:
            self.short_description = self.details
        if not self.details and self.short_description:
            self.details = self.short_description
        return self


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
    role_label: str = Field(default="Therapist", min_length=2, max_length=100)
    qualification: str = Field(default="", max_length=255)
    experience_years: int = Field(default=0, ge=0, le=80)
    languages: list[str] = Field(default_factory=list)
    image: str = Field(default="/images/doctor-placeholder.png", min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=50)
    specialties: list[str] = Field(default_factory=list)
    bio: str = Field(default="", max_length=5000)
    is_active: bool = True

    @field_validator("full_name", "role_label", "qualification", "image", "phone", "bio", mode="before")
    @classmethod
    def normalize_therapist_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("languages", "specialties", mode="before")
    @classmethod
    def normalize_therapist_lists(cls, value):
        if isinstance(value, str):
            value = value.splitlines()
        if isinstance(value, list):
            return [item.strip() for item in value if isinstance(item, str) and item.strip()]
        return value


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
    therapist_id: int = Field(default=0, ge=0)
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


class BookingEmailLogResponse(BaseModel):
    id: int
    booking_id: int
    audience: str
    event_key: str
    recipient_email: EmailStr
    subject: str
    delivery_status: str
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TherapyBookingStatusUpdate(BaseModel):
    status: BookingStatus | None = None
    therapist_id: int | None = Field(default=None, ge=1)
    booking_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    cancellation_reason: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)
    send_email: bool = False
    email_message: str | None = Field(default=None, max_length=5000)


class BookingClientEmailRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=5, max_length=5000)


class BookingClientEmailResponse(BaseModel):
    detail: str
    recipient: EmailStr
    subject: str


class BookingCancelRequest(BaseModel):
    reference_code: str = Field(min_length=4, max_length=32)
    email: EmailStr
    reason: str | None = Field(default=None, max_length=2000)


class BookingCancelResponse(BaseModel):
    detail: str
    reference_code: str
    status: BookingStatus
