"""
main.py – adds JSON-friendly login while keeping OAuth2PasswordRequestForm
for Swagger / programmatic clients.
"""

from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .auth import create_token, current_user, hash_pw, verify_pw
from .engine import seed_concepts, tutor_reply
from .models import (
    Concept,
    Feedback,
    Learner,
    Progress,
    Tenant,
    User,
    _engine,
    init_db,
)
from .schemas import LearnerCreate, TokenOut, UserCreate
from .voice import router as voice_router

app = FastAPI(title="LearnPal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)
init_db()
seed_concepts()

# ─────────────────────────────────────────── Health
@app.get("/health")
def health():
    return {"status": "ok"}

# ─────────────────────────────────────────── Auth
class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/auth/signup", response_model=TokenOut)
def signup(payload: UserCreate):
    with Session(_engine()) as s:
        tenant = Tenant(name=payload.tenant_name)
        s.add(tenant)
        s.flush()

        user = User(
            tenant_id=tenant.id,
            email=payload.email,
            password_hash=hash_pw(payload.password),
        )
        s.add(user)
        s.commit()
        return TokenOut(access_token=create_token(user.id, tenant.id))


@app.post("/auth/token", response_model=TokenOut)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Accept both:
    • application/x-www-form-urlencoded (Swagger, CLI)
    • application/json            (our React login form)
    """
    if request.headers.get("content-type", "").startswith("application/json"):
        body = await request.json()
        creds = LoginIn(**body)
        email, pwd = creds.email, creds.password
    else:
        email, pwd = form_data.username, form_data.password

    with Session(_engine()) as s:
        user = s.exec(select(User).where(User.email == email)).first()
        if not user or not verify_pw(pwd, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        return TokenOut(access_token=create_token(user.id, user.tenant_id))

# ────────────────────────── Learner CRUD
@app.post("/learners", status_code=201)
def create_learner(payload: LearnerCreate, user: User = Depends(current_user)):
    learner = Learner(tenant_id=user.tenant_id, name=payload.name, dob=payload.dob)
    with Session(_engine()) as s:
        s.add(learner)
        s.commit()
        s.refresh(learner)
        return learner


@app.get("/learners")
def list_learners(user: User = Depends(current_user)):
    with Session(_engine()) as s:
        return s.exec(select(Learner).where(Learner.tenant_id == user.tenant_id)).all()

# ────────────────────────── Who-am-I
@app.get("/me")
def who_am_i(user: User = Depends(current_user)):
    return {"email": user.email, "tenant_id": user.tenant_id}

# ────────────────────────── Progress
@app.get("/progress/{learner_id}")
def learner_progress(learner_id: int, user: User = Depends(current_user)):
    with Session(_engine()) as s:
        learner = s.get(Learner, learner_id)
        if not learner or learner.tenant_id != user.tenant_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        rows = (
            s.exec(
                select(Concept.label, Progress.correct, Progress.attempts)
                .join(Progress, Concept.id == Progress.concept_id)
                .where(Progress.learner_id == learner_id)
            )
            .all()
        )
        return {
            r.label: {"correct": r.correct, "attempts": r.attempts}
            for r in rows
        }

# ────────────────────────── Lesson
class LessonIn(BaseModel):
    learner_id: int
    user_text: str


@app.post("/lesson")
def lesson(payload: LessonIn, user: User = Depends(current_user)):
    with Session(_engine()) as s:
        learner = s.get(Learner, payload.learner_id)
        if not learner or learner.tenant_id != user.tenant_id:
            raise HTTPException(status_code=403)
    data = tutor_reply(payload.learner_id, payload.user_text)
    return {**data, "reply": data["content"]}  # legacy key for tests

# ────────────────────────── Feedback
class FeedbackIn(BaseModel):
    learner_id: int
    latency_ms: int = Field(ge=0)
    rating: int = Field(..., description="+1 for 👍  or -1 for 👎")


@app.post("/feedback", status_code=201)
def feedback(payload: FeedbackIn, user: User = Depends(current_user)):
    with Session(_engine()) as s:
        learner = s.get(Learner, payload.learner_id)
        if not learner or learner.tenant_id != user.tenant_id:
            raise HTTPException(status_code=403)

        fb = Feedback(
            learner_id=payload.learner_id,
            latency_ms=payload.latency_ms,
            rating=payload.rating,
            created=datetime.now(timezone.utc),
        )
        s.add(fb)
        s.commit()
        return {"status": "ok"}
