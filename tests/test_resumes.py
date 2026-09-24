import uuid
import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine


@pytest.fixture(autouse=True)
def setup_database():
    """
    Ensures clean database tables for resume CRUD test execution.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_auth_headers(client: TestClient, email: str, name: str) -> dict:
    reg_payload = {"email": email, "full_name": name, "password": "password123"}
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_resume_authenticated(client: TestClient):
    headers = get_auth_headers(client, "resumemaker@example.com", "Resume Maker")
    payload = {
        "title": "Software Engineer Resume",
        "template_id": "modern",
        "theme_config": {"primary_color": "#007bff"},
    }
    response = client.post("/api/v1/resumes/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Software Engineer Resume"
    assert data["template_id"] == "modern"
    assert "id" in data


def test_create_resume_unauthenticated(client: TestClient):
    payload = {"title": "Unauthenticated Resume"}
    response = client.post("/api/v1/resumes/", json=payload)
    assert response.status_code == 401


def test_get_user_resumes_list(client: TestClient):
    headers = get_auth_headers(client, "lister@example.com", "Lister User")
    
    # Create 2 resumes
    client.post("/api/v1/resumes/", json={"title": "Resume 1"}, headers=headers)
    client.post("/api/v1/resumes/", json={"title": "Resume 2"}, headers=headers)

    response = client.get("/api/v1/resumes/", headers=headers)
    assert response.status_code == 200
    resumes = response.json()
    assert len(resumes) == 2
    titles = [r["title"] for r in resumes]
    assert "Resume 1" in titles
    assert "Resume 2" in titles


def test_get_single_resume(client: TestClient):
    headers = get_auth_headers(client, "singlefetch@example.com", "Single Fetch")
    create_res = client.post("/api/v1/resumes/", json={"title": "Target Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == resume_id
    assert data["title"] == "Target Resume"


def test_update_resume_full_payload(client: TestClient):
    headers = get_auth_headers(client, "updater@example.com", "Updater User")
    create_res = client.post("/api/v1/resumes/", json={"title": "Initial Title"}, headers=headers)
    resume_id = create_res.json()["id"]

    # Full update payload
    update_payload = {
        "title": "Updated Engineer Resume",
        "template_id": "classic",
        "theme_config": {"primary_color": "#28a745"},
        "personal_info": {
            "full_name": "Jane Developer",
            "email": "jane@example.com",
            "summary": "Full Stack Engineer",
        },
        "work_experiences": [
            {
                "company": "Tech Innovations",
                "position": "Lead Developer",
                "is_current": True,
                "display_order": 0,
            }
        ],
        "skills": [
            {"name": "Python", "category": "Backend", "display_order": 0},
            {"name": "FastAPI", "category": "Backend", "display_order": 1},
        ],
        "custom_sections": [
            {"section_title": "Languages", "content": "English, Spanish", "display_order": 0}
        ],
    }

    response = client.put(f"/api/v1/resumes/{resume_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Engineer Resume"
    assert data["template_id"] == "classic"
    assert data["personal_info"]["full_name"] == "Jane Developer"
    assert len(data["work_experiences"]) == 1
    assert data["work_experiences"][0]["company"] == "Tech Innovations"
    assert len(data["skills"]) == 2
    assert len(data["custom_sections"]) == 1
    assert data["custom_sections"][0]["section_title"] == "Languages"


def test_delete_resume(client: TestClient):
    headers = get_auth_headers(client, "deleter@example.com", "Deleter User")
    create_res = client.post("/api/v1/resumes/", json={"title": "Delete Me"}, headers=headers)
    resume_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert get_res.status_code == 404


def test_user_isolation_read(client: TestClient):
    headers_a = get_auth_headers(client, "usera@example.com", "User A")
    headers_b = get_auth_headers(client, "userb@example.com", "User B")

    # User A creates a resume
    create_res = client.post("/api/v1/resumes/", json={"title": "User A Private Resume"}, headers=headers_a)
    resume_id = create_res.json()["id"]

    # User B attempts to read User A's resume
    response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers_b)
    assert response.status_code == 404


def test_user_isolation_update(client: TestClient):
    headers_a = get_auth_headers(client, "usera2@example.com", "User A2")
    headers_b = get_auth_headers(client, "userb2@example.com", "User B2")

    create_res = client.post("/api/v1/resumes/", json={"title": "User A Resume"}, headers=headers_a)
    resume_id = create_res.json()["id"]

    # User B attempts to update User A's resume
    update_payload = {"title": "Hacked Title"}
    response = client.put(f"/api/v1/resumes/{resume_id}", json=update_payload, headers=headers_b)
    assert response.status_code == 404


def test_user_isolation_delete(client: TestClient):
    headers_a = get_auth_headers(client, "usera3@example.com", "User A3")
    headers_b = get_auth_headers(client, "userb3@example.com", "User B3")

    create_res = client.post("/api/v1/resumes/", json={"title": "User A Resume"}, headers=headers_a)
    resume_id = create_res.json()["id"]

    # User B attempts to delete User A's resume
    response = client.delete(f"/api/v1/resumes/{resume_id}", headers=headers_b)
    assert response.status_code == 404


def test_invalid_resume_creation_payload(client: TestClient):
    headers = get_auth_headers(client, "invalid@example.com", "Invalid User")
    payload = {"title": ""}  # Min length is 1
    response = client.post("/api/v1/resumes/", json=payload, headers=headers)
    assert response.status_code == 422


def test_non_existent_resume_id(client: TestClient):
    headers = get_auth_headers(client, "nonexistent@example.com", "Non Existent User")
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/resumes/{fake_id}", headers=headers)
    assert response.status_code == 404


def test_duplicate_resume(client: TestClient):
    headers = get_auth_headers(client, "duplicator@example.com", "Duplicator User")
    create_res = client.post("/api/v1/resumes/", json={"title": "Original Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    dup_res = client.post(f"/api/v1/resumes/{resume_id}/duplicate", headers=headers)
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["title"] == "Original Resume (Copy)"
    assert dup_data["id"] != resume_id
