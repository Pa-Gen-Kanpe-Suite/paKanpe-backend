from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import CounterStatus, TicketSource, TicketStatus, UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str = Field(min_length=8, max_length=30)
    bank_identifier: str | None = Field(default=None, max_length=80)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Le mot de passe doit contenir une majuscule et un chiffre")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str
    bank_identifier: str | None
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ServiceOut(BaseModel):
    id: int
    code: str
    name: str
    average_minutes: int

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    service_id: int


class PhysicalTicketCreate(BaseModel):
    service_id: int
    visitor_name: str = Field(min_length=2, max_length=160)
    visitor_phone: str | None = Field(default=None, max_length=30)


class TicketOut(BaseModel):
    id: int
    code: str
    source: TicketSource
    status: TicketStatus
    service_id: int
    service_name: str
    counter_id: int | None = None
    counter_name: str | None = None
    visitor_name: str | None = None
    position: int | None = None
    estimated_wait_minutes: int | None = None
    created_at: datetime
    called_at: datetime | None = None
    started_at: datetime | None = None
    closed_at: datetime | None = None
    comment: str | None = None


class QueuePosition(BaseModel):
    ticket: TicketOut
    current_called_code: str | None
    active_counters: int
    average_service_minutes: float


class CounterCreate(BaseModel):
    number: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=80)


class CounterStatusUpdate(BaseModel):
    status: CounterStatus


class CounterOut(BaseModel):
    id: int
    number: int
    name: str
    status: CounterStatus
    cashier_id: int | None
    current_ticket: TicketOut | None = None


class CloseTicketRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)
    auto_call_next: bool = True


class NotificationOut(BaseModel):
    id: int
    ticket_id: int
    type: str
    message: str
    is_read: bool
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatisticsOverview(BaseModel):
    date: str
    tickets_issued: int
    waiting: int
    in_service: int
    completed: int
    cancelled: int
    absent: int
    average_wait_minutes: float
    average_service_minutes: float
    active_counters: int


class DisplayTicket(BaseModel):
    code: str
    counter_name: str
    called_at: datetime


class DisplayBoard(BaseModel):
    called: list[DisplayTicket]
    waiting_count: int
    updated_at: datetime


class Message(BaseModel):
    message: str
