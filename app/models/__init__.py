"""
Modelos SQLModel — Test de Personalidad OCEAN-P
=================================================
Diseñados para ser portables entre SQLite (desarrollo local) y PostgreSQL/Neon
(producción). Decisiones clave:
- IDs como UUID v4 en string (36 chars) → URLs no predecibles (RF-4.5).
- Enums como strings (no PostgreSQL ENUM) para no requerir migraciones al
  añadir valores.
- JSON como TEXT/JSONB (SQLModel mapea a JSON portable).
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, JSON, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship


def _new_uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------------
# Tabla users (opcional en MVP — el usuario no requiere login)
# ----------------------------------------------------------------------

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=_new_uuid, primary_key=True, max_length=36)
    email: Optional[str] = Field(default=None, index=True, max_length=255)
    created_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))

    sessions: list["TestSession"] = Relationship(back_populates="user")


# ----------------------------------------------------------------------
# Tabla test_sessions
# ----------------------------------------------------------------------

SESSION_STATUSES = ("in_progress", "completed", "invalid")


class TestSession(SQLModel, table=True):
    __tablename__ = "test_sessions"

    id: str = Field(default_factory=_new_uuid, primary_key=True, max_length=36)
    user_id: Optional[str] = Field(
        default=None, foreign_key="users.id", index=True, max_length=36
    )
    started_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    status: str = Field(default="in_progress", max_length=20, index=True)
    avg_response_time_ms: Optional[int] = Field(default=None)

    user: Optional[User] = Relationship(back_populates="sessions")
    responses: list["ItemResponse"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    scores: list["Score"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    reports: list["Report"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    email_deliveries: list["EmailDelivery"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# ----------------------------------------------------------------------
# Tabla responses (ítems respondidos)
# ----------------------------------------------------------------------

class ItemResponse(SQLModel, table=True):
    __tablename__ = "responses"
    __table_args__ = (
        # Un ítem por sesión (evita duplicados al reintentar POST)
        UniqueConstraint("session_id", "item_id", name="uq_response_session_item"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="test_sessions.id", index=True, max_length=36)
    item_id: int = Field(ge=1, le=65)
    raw_value: int = Field(ge=1, le=5)
    response_time_ms: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))

    session: TestSession = Relationship(back_populates="responses")


# ----------------------------------------------------------------------
# Tabla scores (facetas, dimensiones, índices, validez)
# ----------------------------------------------------------------------

SCOPE_TYPES = ("facet", "dimension", "composite_index", "validity")


class Score(SQLModel, table=True):
    __tablename__ = "scores"
    __table_args__ = (
        # Una fila por (sesión, scope_type, scope_key)
        UniqueConstraint("session_id", "scope_type", "scope_key", name="uq_score_scope"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="test_sessions.id", index=True, max_length=36)
    scope_type: str = Field(max_length=20, index=True)
    scope_key: str = Field(max_length=64, index=True)
    raw_score: float
    percentile: Optional[float] = Field(default=None)

    session: TestSession = Relationship(back_populates="scores")


# ----------------------------------------------------------------------
# Tabla reports
# ----------------------------------------------------------------------

class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: str = Field(default_factory=_new_uuid, primary_key=True, max_length=36)
    session_id: str = Field(foreign_key="test_sessions.id", index=True, max_length=36)
    archetype_label: Optional[str] = Field(default=None, max_length=120)
    generated_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))
    pdf_token: Optional[str] = Field(default=None, index=True, max_length=36)
    pdf_url: Optional[str] = Field(default=None, max_length=512)
    pdf_expires_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))

    session: TestSession = Relationship(back_populates="reports")


# ----------------------------------------------------------------------
# Tabla email_deliveries
# ----------------------------------------------------------------------

EMAIL_STATUSES = ("sent", "failed")


class EmailDelivery(SQLModel, table=True):
    __tablename__ = "email_deliveries"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="test_sessions.id", index=True, max_length=36)
    email_hash: str = Field(max_length=64, index=True)  # SHA-256 hex
    consent: bool = Field(default=False)
    sent_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))
    status: str = Field(max_length=20)

    session: TestSession = Relationship(back_populates="email_deliveries")


# ----------------------------------------------------------------------
# Tabla norm_tables (RF-2.7 — tabla normativa versionada)
# ----------------------------------------------------------------------

class NormTable(SQLModel, table=True):
    __tablename__ = "norm_tables"

    id: Optional[int] = Field(default=None, primary_key=True)
    version: str = Field(max_length=20, index=True)
    scope_key: str = Field(max_length=64, index=True)
    raw_to_percentile_mapping: dict = Field(sa_column=Column(JSON))
    active: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))


# ----------------------------------------------------------------------
# MÓDULO DE SALUD EMOCIONAL — modelos nuevos
# ----------------------------------------------------------------------

class EmotionalAssessment(SQLModel, table=True):
    __tablename__ = "emotional_assessments"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="test_sessions.id", index=True, max_length=36)
    started_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    disclaimer_accepted: bool = False  # RS-4
    is_female: bool = True  # afecta al PHQ-15 (ítem 15 exclusivo de mujeres)
    crisis_alert: bool = False  # RS-1 — se setea en cuanto el ítem 9 > 0
    country_code: str = Field(default="ES", max_length=2)  # para crisis_resources


class EmotionalResponse(SQLModel, table=True):
    __tablename__ = "emotional_responses"

    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_id: int = Field(foreign_key="emotional_assessments.id", index=True)
    module: str = Field(max_length=32, index=True)
    item_id: int
    raw_value: int
    response_time_ms: Optional[int] = Field(default=None)
    is_scored: bool = True  # False para checklists no clínicos y contexto


class EmotionalScore(SQLModel, table=True):
    __tablename__ = "emotional_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_id: int = Field(foreign_key="emotional_assessments.id", index=True)
    module: str = Field(max_length=32, index=True)
    response_scale: str = Field(max_length=32)  # "0-3_4opciones" | "0-5_6opciones" | "0-2_3opciones"
    total_score: float
    severity_band: str = Field(max_length=32)
    is_clinically_validated: bool = True
    crisis_alert: bool = False  # RS-1, solo aplica a phq9
    professional_help_recommended: bool = False  # RS-5


class EmotionalChecklistSelection(SQLModel, table=True):
    __tablename__ = "emotional_checklist_selections"

    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_id: int = Field(foreign_key="emotional_assessments.id", index=True)
    module: str = Field(max_length=32, index=True)
    item_id: int
    selected: bool


class CrisisResource(SQLModel, table=True):
    __tablename__ = "crisis_resources"

    id: Optional[int] = Field(default=None, primary_key=True)
    country_code: str = Field(max_length=2, index=True)
    resource_name: str = Field(max_length=120)
    contact_info: str = Field(max_length=512)
    active: bool = Field(default=True, index=True)
    updated_at: datetime = Field(default_factory=_utcnow, sa_column=Column(DateTime(timezone=True)))
