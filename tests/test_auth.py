from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import _engine, SQLModel

client = TestClient(app)


def setup_module(_=None):
    # fresh in-memory DB for each test run
    SQLModel.metadata.drop_all(_engine())
    SQLModel.metadata.create_all(_engine())


def test_signup_and_token():
    signup = {
        "email": "parent@example.com",
        "password": "secret123",
        "tenant_name": "Family Smith",
    }
    r = client.post("/auth/signup", json=signup)
    assert r.status_code == 200
    jwt = r.json()["access_token"]
    # token should let us hit /learners (empty list)
    hdrs = {"Authorization": "Bearer " + jwt}
    r2 = client.get("/learners", headers=hdrs)
    assert r2.status_code == 200
    assert r2.json() == []
