# MyResume

**MyResume** is a production-style, full-stack Resume Builder web application built with a clean client-server architecture using Python FastAPI, SQLAlchemy 2.0, PostgreSQL, JWT Authentication, and modern web standards.

---

## 🌟 Features

- **User Authentication**: Secure signup, login, JWT token management, and profile management with salted `bcrypt` password hashing.
- **Interactive Resume Editor**: Form controls for Personal Information, Work Experience, Education, Skills, Projects, Certifications, and Custom Sections.
- **Real-Time Live Preview**: Instantly updates preview sheet as user types without triggering page reloads.
- **Data Persistence**: Full resume state synchronized atomically within a single database transaction.
- **Autosave**: 1.5-second debounced background autosave with real-time visual status indicator.
- **Row-Level Authorization**: Server-side user resource isolation (`WHERE user_id == current_user.id`).
- **PDF Export**: Dedicated print view (`GET /api/v1/resumes/{id}/print`) with A4 portrait styling, 12mm page margins, and page-break rules (`break-inside: avoid`).
- **JSON Backup & Import**: Download structured JSON backups and upload JSON files to restore or create resumes.
- **Multi-Container Dockerization**: Orchestrated FastAPI and PostgreSQL services with automated startup database migrations (`alembic upgrade head`).

---

## 🏗️ Architecture & Tech Stack

```
ResumeForge Application
├── Frontend (Browser)
│   ├── Vanilla HTML5 / CSS3 (Flexbox & Grid)
│   ├── Vanilla JavaScript (ES6+ API Client & Live Preview Engine)
│   └── Dedicated Print View (@media print)
├── Backend Service (FastAPI)
│   ├── API Routers (/api/v1/auth, /api/v1/resumes, /api/v1/health)
│   ├── Security Layer (Bcrypt, JWT HS256, Authorization Dependencies)
│   ├── Pydantic v2 Input/Output Schemas
│   └── SQLAlchemy 2.0 Synchronous ORM
└── Database Layer
    ├── PostgreSQL (Relational tables + JSONB theme configuration)
    └── Alembic Migration Manager
```

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+) |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, pydantic-settings |
| **ORM & Database** | SQLAlchemy 2.0 (Synchronous), PostgreSQL, Alembic |
| **Security & Auth** | JWT (`python-jose`), `bcrypt` password hashing |
| **Testing** | `pytest`, `httpx` |
| **Containerization** | Docker, Docker Compose |

---

## 🚀 Local Development Setup

### 1. Prerequisites
- **Python 3.11+**
- **Git**
- **Docker & Docker Compose** *(Optional for local database)*

### 2. Environment Configuration
Clone the repository and create a Python virtual environment:

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

#### Environment Variables Reference
| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `PROJECT_NAME` | Name of the application | `ResumeForge` |
| `API_V1_STR` | API version prefix | `/api/v1` |
| `ENVIRONMENT` | Environment mode (`development` / `production`) | `development` |
| `DEBUG` | Enable debug logs | `true` |
| `SECRET_KEY` | JWT signature secret key | *Random secure string in production* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration time in minutes | `1440` (24 Hours) |
| `DATABASE_URL` | Main database connection string | `postgresql://user:pass@localhost:5432/resumeforge_db` |
| `TEST_DATABASE_URL` | Isolated test database string | `sqlite:///./resumeforge_test.db` |

---

## 🗄️ Database Setup & Migrations

### Run Database Migrations
Apply Alembic migrations to synchronize database tables:

```bash
alembic upgrade head
```

### Create New Migrations
When modifying SQLAlchemy models in `app/models/`, generate a new migration script:

```bash
alembic revision --autogenerate -m "Describe schema changes"
```

---

## ⚡ Running the Application

### Option A: Local Python Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Option B: Docker Compose Multi-Container Setup

Start PostgreSQL and FastAPI containerized services:

```bash
docker compose up --build
```

The container entrypoint will automatically wait for PostgreSQL to become healthy, run `alembic upgrade head`, and start the web server.

---

## 📍 Interactive API Documentation

Once the server is running, access interactive OpenAPI documentation:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 🧪 Running Automated Tests

Execute the complete test suite (unit, integration, authentication, CRUD, PDF, JSON import/export, and E2E user journey tests):

```bash
pytest
```

---

## ☁️ Production Deployment Prerequisites Guidelines

When preparing to deploy **ResumeForge** to production environments (e.g. Render, Railway, AWS EC2, GCP):

1. **Environment Variables**:
   - Set `ENVIRONMENT="production"` and `DEBUG=false`.
   - Provide a strong, cryptographically generated `SECRET_KEY`.
   - Configure managed PostgreSQL connection string in `DATABASE_URL`.
2. **Database Security**:
   - Ensure SSL connection mode is enabled (`sslmode=require`) for remote PostgreSQL databases.
   - Run `alembic upgrade head` via release command or Docker startup entrypoint.
3. **CORS Configuration**:
   - Restrict `allow_origins` in `app/main.py` to production domain origin.
