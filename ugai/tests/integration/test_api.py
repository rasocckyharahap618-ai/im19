from fastapi.testclient import TestClient
from api.server import app
def test_health():
 r=TestClient(app).get("/health"); assert r.status_code==200 and r.json()["status"]=="ok"
