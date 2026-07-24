import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend path is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app

client = TestClient(app)

def test_health_and_signup():
    payload = {
        "username": "test_hero",
        "email": "hero_test@arcade.com",
        "password": "Password123!"
    }
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "test_hero"

def test_login_flow():
    login_payload = {
        "username_or_email": "hero_test@arcade.com",
        "password": "Password123!"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    token = data["access_token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "hero_test@arcade.com"
