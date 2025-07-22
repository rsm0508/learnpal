"""
Core SQLModel tables for LearnPal MVP.

Sprint-6 additions:
• Feedback table (thumbs-up / thumbs-down + latency)
• Rating validator to enforce +1 / -1
"""

import os
from datetime import datetime, timezone
from typing import Optional
from pydantic import validator
from sqlmodel import Field, SQLModel, create_engine
from sqlalchemy import UniqueConstraint

class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    plan: str = "free"  # free | family | school


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    email: str
    password_hash: str
    role: str = "parent"  # parent | admin

    __table_args__ = (UniqueConstraint("email", name="uniq_user_email"),)


class Learner(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    name: str
    dob: str  # YYYY-MM
    persona_json: str = "{}"

    # ── validation ───────────────────────────────────────────────────
    @validator("dob")
    def _validate_dob(cls, v: str) -> str:  # noqa: N805
        datetime.strptime(v, "%Y-%m")
        return v


class Concept(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str
    label: str
    grade: str


class Progress(SQLModel, table=True):
    learner_id: int = Field(foreign_key="learner.id", primary_key=True)
    concept_id: int = Field(foreign_key="concept.id", primary_key=True)
    correct: int = 0
    attempts: int = 0


class Feedback(SQLModel, table=True):
    """
    Stores explicit learner feedback for each tutor response.
    `rating`  = +1 (thumbs-up) | -1 (thumbs-down)
    `latency` = GPT turnaround in ms
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    learner_id: int = Field(foreign_key="learner.id", index=True)
    latency_ms: int
    rating: int
    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # enforce +1 / -1
    @validator("rating")
    def _validate_rating(cls, v: int) -> int:  # noqa: N805
        if v not in (-1, 1):
            raise ValueError("Rating must be +1 or -1")
        return v


# ── helpers ─────────────────────────────────────────────────────────
def _engine():
    url = os.getenv("DATABASE_URL", "sqlite:///./learnpal.db")
    return create_engine(url, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(_engine())
