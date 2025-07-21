from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from .models import (
    init_db,
    Tenant,
    User,
    Learner,
    Concept,    # ← ensures Concept is in scope
    Progress,   # ← ensures Progress is in scope
    _engine,
)
from .auth import hash_pw, verify_pw, create_token, current_user
from .schemas import UserCreate, TokenOut, LearnerCreate
from .voice import router as voice_router
from .engine import tutor_reply, seed_concepts

app = FastAPI(title="LearnPal API")

# ──────────────────────────────────────────────────────────────────────────────
# CORS – allow both hosts or use ["*"] in dev                   # type: ignore
# ──────────────────────────────────────────────────────────────────────────────
app.add_middleware(  # type: ignore
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)

# run once at startup
init_db()
seed_concepts()


# ──────────────────────────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/auth/signup", response_model=TokenOut)
def signup(payload: UserCreate):
    with Session(_engine()) as session:
        tenant = Tenant(name=payload.tenant_name)
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email=payload.email,
            password_hash=hash_pw(payload.password),
        )
        session.add(user)
        session.commit()

        token = create_token(user.id, tenant.id)
        return TokenOut(access_token=token)


@app.post("/auth/token", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(_engine()) as session:
        user = session.exec(
            select(User).where(User.email == form_data.username)
        ).first()

        if user is None or not verify_pw(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="Incorrect email or password",
            )

        token = create_token(user.id, user.tenant_id)
        return TokenOut(access_token=token)


# ──────────────────────────────────────────────────────────────────────────────
# Learner CRUD
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/learners", status_code=201)
def create_learner(payload: LearnerCreate, user: User = Depends(current_user)):
    learner = Learner(
        tenant_id=user.tenant_id,
        name=payload.name,
        dob=payload.dob,
    )
    with Session(_engine()) as session:
        session.add(learner)
        session.commit()
        session.refresh(learner)
        return learner


@app.get("/learners")
def list_learners(user: User = Depends(current_user)):
    with Session(_engine()) as session:
        stmt = select(Learner).where(Learner.tenant_id == user.tenant_id)
        return session.exec(stmt).all()


# ──────────────────────────────────────────────────────────────────────────────
# Who am I
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/me")
def who_am_i(user: User = Depends(current_user)):
    return {"email": user.email, "tenant_id": user.tenant_id}


# ──────────────────────────────────────────────────────────────────────────────
# Progress endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/progress/{learner_id}")
def learner_progress(learner_id: int, user: User = Depends(current_user)):
    with Session(_engine()) as s:
        learner = s.get(Learner, learner_id)
        if not learner or learner.tenant_id != user.tenant_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        stmt = (
            select(Concept.label, Progress.correct, Progress.attempts)  # type: ignore
            .join(Progress, Concept.id == Progress.concept_id)
            .where(Progress.learner_id == learner_id)                  # type: ignore
        )
        return {
            row.label: {"correct": row.correct, "attempts": row.attempts}
            for row in s.exec(stmt)
        }


# ──────────────────────────────────────────────────────────────────────────────
# Lesson route
# ──────────────────────────────────────────────────────────────────────────────
class LessonIn(BaseModel):
    learner_id: int
    user_text: str


@app.post("/lesson")
def lesson(payload: LessonIn, user: User = Depends(current_user)):
    with Session(_engine()) as session:
        learner = session.get(Learner, payload.learner_id)
        if learner is None:
            raise HTTPException(status_code=404, detail="Learner not found")
        if learner.tenant_id != user.tenant_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    reply = tutor_reply(payload.learner_id, payload.user_text)
    return {"reply": reply}
