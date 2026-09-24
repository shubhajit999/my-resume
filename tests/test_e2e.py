import uuid
import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine


@pytest.fixture(autouse=True)
def setup_e2e_database():
    """
    Ensures clean database tables for end-to-end user journey test execution.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_complete_e2e_user_journey(client: TestClient):
    """
    Tests the complete end-to-end user lifecycle:
    Registration -> Login -> Profile -> Create -> Update -> Print -> Export -> Import -> Duplicate -> Delete -> Security Checks.
    """
    # 1. Registration
    reg_payload = {
        "email": "e2euser@example.com",
        "full_name": "E2E Tester",
        "password": "e2epassword123",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "e2euser@example.com"
    assert "hashed_password" not in user_data

    # 2. Login
    login_payload = {
        "email": "e2euser@example.com",
        "password": "e2epassword123",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Current User Profile
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "E2E Tester"

    # 4. List Resumes (Initially empty)
    list_res = client.get("/api/v1/resumes/", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0

    # 5. Create Resume
    create_payload = {
        "title": "Master Engineer Resume",
        "template_id": "modern",
        "theme_config": {"primary_color": "#4f46e5"},
    }
    create_res = client.post("/api/v1/resumes/", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    resume_id = create_res.json()["id"]

    # 6. Fetch Single Resume Detail
    get_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Master Engineer Resume"

    # 7. Update Resume (Full Payload Sync)
    update_payload = {
        "title": "Senior Principal Engineer",
        "template_id": "classic",
        "theme_config": {"primary_color": "#16a34a"},
        "personal_info": {
            "full_name": "E2E Tester",
            "email": "e2euser@example.com",
            "phone": "+1 555-0199",
            "location": "New York, NY",
            "summary": "Accomplished Principal Systems Architect with 10+ years of experience.",
        },
        "work_experiences": [
            {
                "company": "Cloud Corp",
                "position": "Lead Architect",
                "location": "New York",
                "is_current": True,
                "description": "Led distributed backend architecture.",
                "display_order": 0,
            }
        ],
        "education": [
            {
                "institution": "Columbia University",
                "degree": "M.S.",
                "field_of_study": "Computer Science",
                "gpa": "3.9",
                "display_order": 0,
            }
        ],
        "skills": [
            {"name": "Python", "category": "Languages", "display_order": 0},
            {"name": "FastAPI", "category": "Frameworks", "display_order": 1},
        ],
        "projects": [
            {
                "title": "ResumeForge App",
                "tech_stack": "Python, FastAPI, PostgreSQL",
                "description": "Production resume builder web app.",
                "display_order": 0,
            }
        ],
        "certifications": [
            {
                "name": "AWS Solutions Architect",
                "issuing_organization": "Amazon Web Services",
                "display_order": 0,
            }
        ],
        "custom_sections": [
            {
                "section_title": "Languages Spoken",
                "content": "English (Native), French (Fluent)",
                "display_order": 0,
            }
        ],
    }

    update_res = client.put(f"/api/v1/resumes/{resume_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "Senior Principal Engineer"
    assert updated_data["personal_info"]["summary"].startswith("Accomplished Principal")
    assert len(updated_data["work_experiences"]) == 1
    assert len(updated_data["education"]) == 1
    assert len(updated_data["skills"]) == 2

    # 8. Dedicated PDF Print View
    print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers)
    assert print_res.status_code == 200
    assert "A4 portrait" in print_res.text
    assert "Senior Principal Engineer" in print_res.text

    # 9. Export JSON Backup
    export_res = client.get(f"/api/v1/resumes/{resume_id}/export/json", headers=headers)
    assert export_res.status_code == 200
    exported_json = export_res.json()
    assert exported_json["title"] == "Senior Principal Engineer"

    # 10. Import JSON Backup as New Resume
    import_res = client.post("/api/v1/resumes/import", json=exported_json, headers=headers)
    assert import_res.status_code == 201
    imported_data = import_res.json()
    imported_id = imported_data["id"]
    assert imported_id != resume_id
    assert imported_data["title"] == "Senior Principal Engineer"

    # 11. Duplicate Resume
    dup_res = client.post(f"/api/v1/resumes/{resume_id}/duplicate", headers=headers)
    assert dup_res.status_code == 201
    assert "Copy" in dup_res.json()["title"]

    # 12. Delete Resumes
    del1 = client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert del1.status_code == 204
    del2 = client.delete(f"/api/v1/resumes/{imported_id}", headers=headers)
    assert del2.status_code == 204

    # 13. Security Checks & User Isolation
    # Register User B
    client.post("/api/v1/auth/register", json={"email": "userb_e2e@example.com", "full_name": "User B", "password": "password123"})
    login_b = client.post("/api/v1/auth/login", json={"email": "userb_e2e@example.com", "password": "password123"})
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # User B attempts to access User A's remaining duplicate resume
    user_a_resumes = client.get("/api/v1/resumes/", headers=headers).json()
    assert len(user_a_resumes) == 1
    dup_id = user_a_resumes[0]["id"]

    assert client.get(f"/api/v1/resumes/{dup_id}", headers=headers_b).status_code == 404
    assert client.put(f"/api/v1/resumes/{dup_id}", json={"title": "Hacked"}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/resumes/{dup_id}", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/resumes/{dup_id}/print", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/resumes/{dup_id}/export/json", headers=headers_b).status_code == 404
