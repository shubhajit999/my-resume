import uuid
import pytest
from fastapi.testclient import TestClient


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


def test_all_10_templates_selection_and_print(client: TestClient):
    headers = get_auth_headers(client, "templates_user@example.com", "Templates User")
    
    # Create resume
    create_res = client.post("/api/v1/resumes/", json={"title": "Multi Template Resume"}, headers=headers)
    assert create_res.status_code == 201
    resume_id = create_res.json()["id"]

    templates = [
        "modern",
        "professional",
        "minimal",
        "ats",
        "creative",
        "corporate",
        "executive",
        "student",
        "two_column",
        "elegant",
    ]

    for t in templates:
        # Update template_id via PUT
        update_res = client.put(
            f"/api/v1/resumes/{resume_id}",
            json={"title": f"Resume ({t})", "template_id": t, "theme_config": {"primary_color": "#2563eb", "template_id": t}},
            headers=headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["template_id"] == t

        # Verify print endpoint renders HTML with template class
        print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers)
        assert print_res.status_code == 200
        assert "text/html" in print_res.headers["content-type"]
        normalized_t = t.lower().replace("-", "_")
        assert f"template-{normalized_t}" in print_res.text


def test_work_experience_date_mapping_persistence(client: TestClient):
    headers = get_auth_headers(client, "dates_tester@example.com", "Dates Tester")
    create_res = client.post("/api/v1/resumes/", json={"title": "Work Dates Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    update_payload = {
        "title": "Work Dates Resume",
        "work_experiences": [
            {
                "company": "Acme Inc",
                "position": "Senior Engineer",
                "location": "Boston, MA",
                "start_date": "2025-01-01",
                "end_date": "2026-01-01",
                "is_current": False,
                "description": "Full stack development.",
                "display_order": 0,
            }
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "B.S.",
                "field_of_study": "EECS",
                "start_date": "2020-09-01",
                "end_date": "2024-05-31",
                "display_order": 0,
            }
        ],
        "certifications": [
            {
                "name": "Cloud Architect",
                "issuing_organization": "GCP",
                "issue_date": "2024-06-15",
                "display_order": 0,
            }
        ],
    }

    update_res = client.put(f"/api/v1/resumes/{resume_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    res_data = update_res.json()
    assert res_data["work_experiences"][0]["start_date"] == "2025-01-01"
    assert res_data["work_experiences"][0]["end_date"] == "2026-01-01"
    assert res_data["education"][0]["start_date"] == "2020-09-01"
    assert res_data["education"][0]["end_date"] == "2024-05-31"
    assert res_data["certifications"][0]["issue_date"] == "2024-06-15"

    get_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["work_experiences"][0]["start_date"] == "2025-01-01"
    assert fetched["work_experiences"][0]["end_date"] == "2026-01-01"
    assert fetched["education"][0]["start_date"] == "2020-09-01"
    assert fetched["education"][0]["end_date"] == "2024-05-31"
    assert fetched["certifications"][0]["issue_date"] == "2024-06-15"


def test_print_view_css_and_layout_rules(client: TestClient):
    headers = get_auth_headers(client, "print_rules_user@example.com", "Print Rules User")
    create_res = client.post("/api/v1/resumes/", json={"title": "Print Rules Resume", "template_id": "executive"}, headers=headers)
    resume_id = create_res.json()["id"]

    print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers)
    assert print_res.status_code == 200
    assert "text/html" in print_res.headers["content-type"]
    text = print_res.text

    # Assert A4 & margin rules
    assert "size: A4 portrait;" in text
    assert "margin: 12mm;" in text

    # Assert print resets
    assert "html, body" in text
    assert "margin: 0 !important;" in text
    assert "padding: 0 !important;" in text

    # Assert Executive header override in @media print
    assert ".template-executive .preview-header" in text
    assert "margin: 0 0 16px 0 !important;" in text

    # Assert explicit user print button exists
    assert 'onclick="window.print()"' in text


VALID_JPEG_PHOTO = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
VALID_PNG_PHOTO = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
VALID_WEBP_PHOTO = "data:image/webp;base64,UklGRh4AAABXRUJQVlA4TBEAAAAvAAAAAAfQ//73v/+BiOh/AAA="


def test_photo_valid_jpeg(client: TestClient):
    headers = get_auth_headers(client, "photo_jpeg@example.com", "Photo JPEG")
    create_res = client.post("/api/v1/resumes/", json={"title": "JPEG Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    payload = {"theme_config": {"photo_url": VALID_JPEG_PHOTO, "primary_color": "#2563eb"}}
    res = client.put(f"/api/v1/resumes/{resume_id}", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["theme_config"]["photo_url"] == VALID_JPEG_PHOTO


def test_photo_valid_png(client: TestClient):
    headers = get_auth_headers(client, "photo_png@example.com", "Photo PNG")
    create_res = client.post("/api/v1/resumes/", json={"title": "PNG Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    payload = {"theme_config": {"photo_url": VALID_PNG_PHOTO}}
    res = client.put(f"/api/v1/resumes/{resume_id}", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["theme_config"]["photo_url"] == VALID_PNG_PHOTO


def test_photo_valid_webp(client: TestClient):
    headers = get_auth_headers(client, "photo_webp@example.com", "Photo WebP")
    create_res = client.post("/api/v1/resumes/", json={"title": "WebP Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    payload = {"theme_config": {"photo_url": VALID_WEBP_PHOTO}}
    res = client.put(f"/api/v1/resumes/{resume_id}", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["theme_config"]["photo_url"] == VALID_WEBP_PHOTO


def test_photo_unsupported_file_type_rejection(client: TestClient):
    headers = get_auth_headers(client, "photo_svg@example.com", "Photo SVG")
    create_res = client.post("/api/v1/resumes/", json={"title": "SVG Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    # Reject SVG
    svg_payload = {"theme_config": {"photo_url": "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="}}
    res = client.put(f"/api/v1/resumes/{resume_id}", json=svg_payload, headers=headers)
    assert res.status_code == 422

    # Reject HTML / javascript:
    js_payload = {"theme_config": {"photo_url": "javascript:alert(1)"}}
    res2 = client.put(f"/api/v1/resumes/{resume_id}", json=js_payload, headers=headers)
    assert res2.status_code == 422

    # Reject external URL
    ext_payload = {"theme_config": {"photo_url": "https://example.com/photo.jpg"}}
    res3 = client.put(f"/api/v1/resumes/{resume_id}", json=ext_payload, headers=headers)
    assert res3.status_code == 422


def test_photo_excessively_large_payload_rejection(client: TestClient):
    headers = get_auth_headers(client, "photo_large@example.com", "Photo Large")
    create_res = client.post("/api/v1/resumes/", json={"title": "Large Photo Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    huge_b64 = "A" * 600000
    payload = {"theme_config": {"photo_url": f"data:image/jpeg;base64,{huge_b64}"}}
    res = client.put(f"/api/v1/resumes/{resume_id}", json=payload, headers=headers)
    assert res.status_code == 422


def test_photo_save_and_reload(client: TestClient):
    headers = get_auth_headers(client, "photo_saveload@example.com", "Photo Save Load")
    create_res = client.post("/api/v1/resumes/", json={"title": "Save Load Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    # Save photo
    client.put(f"/api/v1/resumes/{resume_id}", json={"theme_config": {"photo_url": VALID_JPEG_PHOTO}}, headers=headers)

    # Reload resume
    get_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["theme_config"]["photo_url"] == VALID_JPEG_PHOTO


def test_photo_removal(client: TestClient):
    headers = get_auth_headers(client, "photo_remove@example.com", "Photo Remove")
    create_res = client.post("/api/v1/resumes/", json={"title": "Remove Photo Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    # Save photo
    client.put(f"/api/v1/resumes/{resume_id}", json={"theme_config": {"photo_url": VALID_JPEG_PHOTO}}, headers=headers)

    # Remove photo
    remove_res = client.put(f"/api/v1/resumes/{resume_id}", json={"theme_config": {"photo_url": None}}, headers=headers)
    assert remove_res.status_code == 200
    assert remove_res.json()["theme_config"].get("photo_url") is None

    # Reload
    get_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert get_res.json()["theme_config"].get("photo_url") is None


def test_photo_template_switching(client: TestClient):
    headers = get_auth_headers(client, "photo_templates@example.com", "Photo Templates")
    create_res = client.post("/api/v1/resumes/", json={"title": "Template Switch Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    # Set photo
    client.put(f"/api/v1/resumes/{resume_id}", json={"theme_config": {"photo_url": VALID_JPEG_PHOTO}}, headers=headers)

    # Switch to executive template
    switch_res = client.put(f"/api/v1/resumes/{resume_id}", json={"template_id": "executive", "theme_config": {"photo_url": VALID_JPEG_PHOTO, "template_id": "executive"}}, headers=headers)
    assert switch_res.status_code == 200
    assert switch_res.json()["template_id"] == "executive"
    assert switch_res.json()["theme_config"]["photo_url"] == VALID_JPEG_PHOTO


def test_photo_json_export_and_import(client: TestClient):
    headers = get_auth_headers(client, "photo_export@example.com", "Photo Export")
    create_res = client.post("/api/v1/resumes/", json={"title": "Export Photo Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    client.put(f"/api/v1/resumes/{resume_id}", json={"theme_config": {"photo_url": VALID_JPEG_PHOTO}}, headers=headers)

    # Export JSON
    export_res = client.get(f"/api/v1/resumes/{resume_id}/export/json", headers=headers)
    assert export_res.status_code == 200
    exported_data = export_res.json()
    assert exported_data["theme_config"]["photo_url"] == VALID_JPEG_PHOTO

    # Import JSON into new resume
    import_res = client.post("/api/v1/resumes/import", json=exported_data, headers=headers)
    assert import_res.status_code == 201
    imported_data = import_res.json()
    assert imported_data["id"] != resume_id
    assert imported_data["theme_config"]["photo_url"] == VALID_JPEG_PHOTO


def test_photo_print_view(client: TestClient):
    headers = get_auth_headers(client, "photo_print@example.com", "Photo Print")
    create_res = client.post("/api/v1/resumes/", json={"title": "Print Photo Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    client.put(f"/api/v1/resumes/{resume_id}", json={"theme_config": {"photo_url": VALID_JPEG_PHOTO}}, headers=headers)

    print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers)
    assert print_res.status_code == 200
    assert 'class="preview-avatar"' in print_res.text


def test_photo_resume_duplication(client: TestClient):
    headers = get_auth_headers(client, "photo_dup@example.com", "Photo Dup")
    create_res = client.post("/api/v1/resumes/", json={"title": "Dup Photo Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    client.put(f"/api/v1/resumes/{resume_id}", json={"theme_config": {"photo_url": VALID_JPEG_PHOTO}}, headers=headers)

    dup_res = client.post(f"/api/v1/resumes/{resume_id}/duplicate", headers=headers)
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["id"] != resume_id
    assert dup_data["theme_config"]["photo_url"] == VALID_JPEG_PHOTO


def test_photo_no_photo_resume(client: TestClient):
    headers = get_auth_headers(client, "nophoto@example.com", "No Photo")
    create_res = client.post("/api/v1/resumes/", json={"title": "Plain Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    # Print view should not contain preview-avatar
    print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers)
    assert print_res.status_code == 200
    assert 'class="preview-avatar"' not in print_res.text


def test_user_isolation_print_and_export(client: TestClient):
    headers_a = get_auth_headers(client, "usera_iso@example.com", "User A Iso")
    headers_b = get_auth_headers(client, "userb_iso@example.com", "User B Iso")

    create_res = client.post("/api/v1/resumes/", json={"title": "Private Resume A"}, headers=headers_a)
    resume_id = create_res.json()["id"]

    # User B print attempt -> 404
    print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers_b)
    assert print_res.status_code == 404

    # User B export attempt -> 404
    export_res = client.get(f"/api/v1/resumes/{resume_id}/export/json", headers=headers_b)
    assert export_res.status_code == 404

    # User B duplicate attempt -> 404
    dup_res = client.post(f"/api/v1/resumes/{resume_id}/duplicate", headers=headers_b)
    assert dup_res.status_code == 404


def test_print_view_html_escaping(client: TestClient):
    headers = get_auth_headers(client, "xss_test@example.com", "XSS Tester")
    create_res = client.post("/api/v1/resumes/", json={"title": "<script>alert('xss')</script> Title"}, headers=headers)
    resume_id = create_res.json()["id"]

    update_payload = {
        "title": "<script>alert('xss')</script> Title",
        "personal_info": {
            "full_name": "<b onclick=alert(1)>John</b> & Jane",
            "summary": "Summary with <script>tags</script>",
        },
    }
    client.put(f"/api/v1/resumes/{resume_id}", json=update_payload, headers=headers)

    print_res = client.get(f"/api/v1/resumes/{resume_id}/print", headers=headers)
    assert print_res.status_code == 200
    text = print_res.text

    # Assert raw script tags were escaped
    assert "<script>alert('xss')</script>" not in text
    assert "&lt;script&gt;alert(" in text
    assert "&lt;b onclick=alert(1)&gt;John&lt;/b&gt;" in text


def test_primary_color_css_injection_rejection(client: TestClient):
    headers = get_auth_headers(client, "color_inject@example.com", "Color Injector")
    create_res = client.post("/api/v1/resumes/", json={"title": "Color Test Resume"}, headers=headers)
    resume_id = create_res.json()["id"]

    # Reject CSS injection payload
    bad_color_payload = {
        "theme_config": {"primary_color": "#2563eb; } body { display:none }"}
    }
    res = client.put(f"/api/v1/resumes/{resume_id}", json=bad_color_payload, headers=headers)
    assert res.status_code == 422





