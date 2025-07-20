from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import _engine, SQLModel, Tenant, User, Learner
from backend.app.auth import hash_pw, create_token

client = TestClient(app)

def setup_module(_=None):
    SQLModel.metadata.drop_all(_engine())
    SQLModel.metadata.create_all(_engine())
    # seed minimal data
    with SQLModel.session(_engine()) as s:
        t = Tenant(name="test")
        s.add(t)
        s.flush()
        u = User(tenant_id=t.id, email="x@y.com", password_hash=hash_pw("pw"))
        s.add(u)
        l = Learner(tenant_id=t.id, name="Kid", dob="2018-01")
        s.add(l)
        s.commit()
        global jwt, learner_id
        jwt = create_token(u.id, t.id)
        learner_id = l.id

def test_lesson_route():
    r = client.post(
        "/lesson",
        json={"learner_id": learner_id, "user_text": "Hi"},
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert r.status_code == 200
    assert "reply" in r.json()
