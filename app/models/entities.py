from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserRole(StrEnum):
    CLIENT = "CLIENT"
    AGENT = "AGENT"
    CASHIER = "CASHIER"
    ADMIN = "ADMIN"


class TicketStatus(StrEnum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    ABSENT = "ABSENT"
    CANCELLED = "CANCELLED"


class TicketSource(StrEnum):
    DIGITAL = "DIGITAL"
    PHYSICAL = "PHYSICAL"


class CounterStatus(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    PAUSED = "PAUSED"


class NotificationType(StrEnum):
    CREATED = "CREATED"
    UPCOMING = "UPCOMING"
    CALLED = "CALLED"
    CANCELLED = "CANCELLED"
    ABSENT = "ABSENT"
    COMPLETED = "COMPLETED"


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    branch_name: Mapped[str] = mapped_column(String(120), default="Agence principale")
    address: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int | None] = mapped_column(
        ForeignKey("banks.id", ondelete="SET NULL")
    )
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), unique=True)
    bank_identifier: Mapped[str | None] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.CLIENT.value, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="client")

    __table_args__ = (
        CheckConstraint(
            "role IN ('CLIENT','AGENT','CASHIER','ADMIN')", name="ck_users_role"
        ),
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    average_minutes: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("average_minutes > 0", name="ck_service_duration"),
    )


class Counter(Base):
    __tablename__ = "counters"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default=CounterStatus.CLOSED.value)
    cashier_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="counter")

    __table_args__ = (
        CheckConstraint("number > 0", name="ck_counter_number"),
        CheckConstraint(
            "status IN ('CLOSED','OPEN','PAUSED')", name="ck_counter_status"
        ),
        Index("uq_counter_bank_number", "bank_id", "number", unique=True),
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(30), unique=True, index=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id", ondelete="RESTRICT"))
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT")
    )
    counter_id: Mapped[int | None] = mapped_column(
        ForeignKey("counters.id", ondelete="SET NULL")
    )
    source: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(
        String(20), default=TicketStatus.WAITING.value, index=True
    )
    visitor_name: Mapped[str | None] = mapped_column(String(160))
    visitor_phone: Mapped[str | None] = mapped_column(String(30))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[User | None] = relationship(back_populates="tickets")
    service: Mapped[Service] = relationship()
    counter: Mapped[Counter | None] = relationship(back_populates="tickets")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('WAITING','CALLED','IN_PROGRESS','CLOSED','ABSENT','CANCELLED')",
            name="ck_ticket_status",
        ),
        CheckConstraint("source IN ('DIGITAL','PHYSICAL')", name="ck_ticket_source"),
        Index(
            "uq_ticket_active_client",
            "client_id",
            unique=True,
            postgresql_where=text(
                "client_id IS NOT NULL AND status IN ('WAITING','CALLED','IN_PROGRESS')"
            ),
            sqlite_where=text(
                "client_id IS NOT NULL AND status IN ('WAITING','CALLED','IN_PROGRESS')"
            ),
        ),
        Index(
            "uq_ticket_active_counter",
            "counter_id",
            unique=True,
            postgresql_where=text(
                "counter_id IS NOT NULL AND status IN ('CALLED','IN_PROGRESS')"
            ),
            sqlite_where=text(
                "counter_id IS NOT NULL AND status IN ('CALLED','IN_PROGRESS')"
            ),
        ),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    type: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    ticket: Mapped[Ticket] = relationship(back_populates="notifications")

    __table_args__ = (
        CheckConstraint(
            "type IN ('CREATED','UPCOMING','CALLED','CANCELLED','ABSENT','COMPLETED')",
            name="ck_notification_type",
        ),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(50))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
