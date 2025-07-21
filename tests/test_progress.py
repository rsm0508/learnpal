from fastapi.testclient import TestClient
from sqlmodel import Session
from backend.app.main import app
from backend.app.models import _engine, SQLModel, Tenant, User, Learner
from backend.app.auth import hash_pw, create_token

client = TestClient(app)

def setup_module(_=None):
    SQLModel.metadata.drop_all(_engine())
    SQLModel.metadata.create_all(_engine())

    with Session(_engine()) as s:
        t = Tenant(name="T"); s.add(t); s.flush()
        u = User(tenant_id=t.id, email="p@x.com", password_hash=hash_pw("pw")); s.add(u)
        l = Learner(tenant_id=t.id, name="Kid", dob="2018-01"); s.add(l)
        s.commit()
        global jwt, learner_id
        jwt = create_token(u.id, t.id)
        learner_id = l.id

def test_progress_endpoint():
    hdr = {"Authorization": f"Bearer {jwt}"}
    for _ in range(2):
        client.post("/lesson", json={"learner_id": learner_id, "user_text": "+"}, headers=hdr)

    r = client.get(f"/progress/{learner_id}", headers=hdr)
    assert r.status_code == 200
    body = r.json()
    assert "addition within 10" in body
    assert body["addition within 10"]["attempts"] >= 2
