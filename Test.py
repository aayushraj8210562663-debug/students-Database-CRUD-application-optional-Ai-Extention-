import os, tempfile
os.environ["STUDENTS_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
 
from fastapi.testclient import TestClient
from main import app
 
STUDENT = {"name": "Asha Singh", "date_of_birth": "2003-05-14",
           "email": "asha@example.com", "phone": "9876543210", "course": "CSE"}
 
 
def test_crud_flow():
    with TestClient(app) as c:
        r = c.post("/students", json=STUDENT)
        assert r.status_code == 201
        sid = r.json()["id"]
 
        assert c.post("/students", json=STUDENT).status_code == 409          # duplicate email
        assert c.post("/students", json={"name": "X", "date_of_birth": "2000-01-01"}).status_code == 422
 
        assert c.get(f"/students/{sid}").json()["name"] == "Asha Singh"
        assert len(c.get("/students", params={"course": "cse"}).json()) == 1
        assert c.get("/students", params={"name": "zzz"}).json() == []
 
        r = c.patch(f"/students/{sid}", json={"course": "ECE"})
        assert r.json()["course"] == "ECE"
 
        assert c.delete(f"/students/{sid}").status_code == 204
        assert c.get(f"/students/{sid}").status_code == 404
 