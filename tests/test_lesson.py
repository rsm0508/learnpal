from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.app.main import app
from backend.app.models import _engine, SQLModel, Tenant, User, Learner
from backend.app.auth import hash_pw, create_token

client = TestClient(app)


def setup_module(_=None):
    # fresh in-memory tables
    SQLModel.metadata.drop_all(_engine())
    SQLModel.metadata.create_all(_engine())

    with Session(_engine()) as s:
        # tenant + parent user
        tenant = Tenant(name="test")
        s.add(tenant)
        s.flush()
        parent = User(
            tenant_id=tenant.id,
            email="x@y.com",
            password_hash=hash_pw("pw"),
        )
        s.add(parent)

        # learner
        learner = Learner(tenant_id=tenant.id, name="Kid", dob="2018-01")
        s.add(learner)
        s.commit()

        global jwt, learner_id
        jwt = create_token(parent.id, tenant.id)
        learner_id = learner.id


def test_lesson_route():
    resp = client.post(
        "/lesson",
        json={"learner_id": learner_id, "user_text": "Hi"},
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert resp.status_code == 200
    assert "reply" in resp.json()
