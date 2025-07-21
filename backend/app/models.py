"""
Core SQLModel tables for multi-tenant MVP.
Only Tenant, User and Learner are needed in Sprint-0.
"""

import os
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine

###############################################################################
# Tables
###############################################################################


class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    plan: str = "free"  # free / family / school


class User(SQLModel, table=True):
    """Parent or admin login – NOT a learner."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    email: str
    password_hash: str
    role: str = "parent"  # parent | admin


class Learner(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    name: str
    dob: str  # store as YYYY-MM, no exact day for privacy
    persona_json: str = "{}"  # tone, voice, reading_level …


class Concept(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str        # "math" | "reading"
    label: str         # "addition within 10"
    grade: str         # "K" | "1" | "6" etc.


class Progress(SQLModel, table=True):
    learner_id: int = Field(foreign_key="learner.id", primary_key=True)
    concept_id: int = Field(foreign_key="concept.id", primary_key=True)
    correct: int = 0
    attempts: int = 0

###############################################################################
# Helpers
###############################################################################


def _engine():
    url = os.getenv("DATABASE_URL", "sqlite:///./learnpal.db")
    return create_engine(url, echo=False, connect_args={"check_same_thread": False})


def init_db():
    """Call once at startup (we’ll wire it in later)."""
    SQLModel.metadata.create_all(_engine())
