import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine


@pytest.fixture(autouse=True)
def setup_database():
    """
    Ensures clean database tables for export/import test execution.
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


def test_pdf_print_view_success(client: TestClient):
    headers = get_auth_headers(client, "printuser@example.com", "Print User")
    create_res = client.post("/api/v1/resumes/", json={"title": "PDF Print Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    response = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "@page" in response.text
    assert "A4 portrait" in response.text
    assert "margin: 12mm" in response.text
    assert "break-inside: avoid" in response.text


def test_json_export_success(client: TestClient):
    headers = get_auth_headers(client, "exporter@example.com", "Exporter User")
    create_res = client.post("/api/v1/resumes/", json={"title": "Export Test Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    response = client.get(f"/api/v1/resumes/{resume_id}/export/json", headers=headers)
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "Content-Disposition" in response.headers
    assert "Export_Test_Resume_backup.json" in response.headers["Content-Disposition"]
    
    data = response.json()
    assert data["id"] == resume_id
    assert data["title"] == "Export Test Resume"


def test_json_import_success(client: TestClient):
    headers = get_auth_headers(client, "importer@example.com", "Importer User")
    
    import_payload = {
        "title": "Imported Developer Resume",
        "template_id": "classic",
        "theme_config": {"primary_color": "#16a34a"},
        "personal_info": {
            "full_name": "Imported User",
            "email": "imported@example.com",
            "summary": "Imported resume summary"
        },
        "skills": [
            {"name": "Python", "category": "Languages"}
        ]
    }

    response = client.post("/api/v1/resumes/import", json=import_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Imported Developer Resume"
    assert data["template_id"] == "classic"
    assert data["personal_info"]["full_name"] == "Imported User"
    assert len(data["skills"]) == 1


def test_authorization_isolation_export_print(client: TestClient):
    headers_a = get_auth_headers(client, "owner_a@example.com", "Owner A")
    headers_b = get_auth_headers(client, "owner_b@example.com", "Owner B")

    # User A creates a resume
    create_res = client.post("/api/v1/resumes/", json={"title": "User A Secret Resume"}, headers=headers_a)
    resume_id = create_res.json()["id"]

    # User B attempts to access print view
    print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers_b)
    assert print_res.status_code == 404

    # User B attempts to export JSON
    export_res = client.get(f"/api/v1/resumes/{resume_id}/export/json", headers=headers_b)
    assert export_res.status_code == 404
