from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LearnerCreate(BaseModel):
    name: str
    dob: str      # YYYY-MM
