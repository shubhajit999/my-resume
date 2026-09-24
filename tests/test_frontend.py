from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_redirect_to_login():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/login"


def test_login_page_route():
    response = client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>Login - ResumeForge</title>" in response.text


def test_register_page_route():
    response = client.get("/register")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>Sign Up - ResumeForge</title>" in response.text


def test_dashboard_page_route():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>Dashboard - ResumeForge</title>" in response.text


def test_builder_page_route():
    response = client.get("/builder")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>Resume Builder - ResumeForge</title>" in response.text


def test_static_css_routes():
    res1 = client.get("/static/css/main.css")
    assert res1.status_code == 200
    assert "ResumeForge Modern Stylesheet" in res1.text

    res2 = client.get("/static/css/builder.css")
    assert res2.status_code == 200
    assert "resume-paper" in res2.text


def test_static_js_routes():
    res1 = client.get("/static/js/api.js")
    assert res1.status_code == 200
    assert "class APIClient" in res1.text

    res2 = client.get("/static/js/auth.js")
    assert res2.status_code == 200
    assert "function requireAuth" in res2.text

    res3 = client.get("/static/js/builder.js")
    assert res3.status_code == 200
    assert "function updateLivePreview" in res3.text
