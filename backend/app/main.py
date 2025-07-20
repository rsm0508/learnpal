from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from .models import init_db, Tenant, User, Learner, _engine
from .auth import hash_pw, verify_pw, create_token, current_user
from .schemas import UserCreate, TokenOut, LearnerCreate

app = FastAPI(title="LearnPal API")


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------------
# Auth endpoints
# ------------------------------------------------------------------
@app.post("/auth/signup", response_model=TokenOut)
def signup(payload: UserCreate):
    """
    Creates a new tenant and parent user. Returns a JWT access token.
    """
    init_db()
    with Session(_engine()) as session:
        # create tenant
        tenant = Tenant(name=payload.tenant_name)
        session.add(tenant)
        session.flush()  # to get tenant.id

        # create parent user
        user = User(
            tenant_id=tenant.id,
            email=payload.email,
            password_hash=hash_pw(payload.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token = create_token(user.id, tenant.id)
        return TokenOut(access_token=token)


@app.post("/auth/token", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 password flow: exchange credentials for JWT.
    """
    with Session(_engine()) as session:
        user = session.exec(
            select(User).where(User.email == form_data.username)
        ).first()

        if user is None or not verify_pw(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )

        token = create_token(user.id, user.tenant_id)
        return TokenOut(access_token=token)


# ------------------------------------------------------------------
# Learner CRUD
# ------------------------------------------------------------------
@app.post("/learners", status_code=201)
def create_learner(
    payload: LearnerCreate, user: User = Depends(current_user)
):
    """
    Parent creates a new learner profile under their tenant.
    """
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
    """
    List all learners that belong to the current parent’s tenant.
    """
    with Session(_engine()) as session:
        stmt = select(Learner).where(Learner.tenant_id == user.tenant_id)
        learners = session.exec(stmt).all()
        return learners
