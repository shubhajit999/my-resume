from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Frontend HTML Page Routes
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login")


@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(os.path.join(static_dir, "pages", "login.html"))


@app.get("/register", include_in_schema=False)
def register_page():
    return FileResponse(os.path.join(static_dir, "pages", "register.html"))


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    return FileResponse(os.path.join(static_dir, "pages", "dashboard.html"))


@app.get("/builder", include_in_schema=False)
def builder_page():
    return FileResponse(os.path.join(static_dir, "pages", "builder.html"))
