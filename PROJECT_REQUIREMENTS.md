# Project Requirements: ResumeForge

## 1. Executive Summary & Vision

**ResumeForge** is a production-style web application that enables users to create, customize, manage, and export professional resumes. Built with a clean client-server architecture, it serves as an educational yet robust application using modern web standards.

### Target Audience
- Job seekers needing structured, modern resume templates.
- Students and early-career developers looking for a clean tool to showcase their projects, skills, and background.

### Core Goals
- **Simplicity**: Clean UI with real-time editing and live preview.
- **Data Integrity**: Safe storage of multi-section user resume data using a relational database.
- **Portability**: Export options for PDF and structured JSON backups, with seamless JSON re-import.
- **Security**: Secure authentication with industry-standard password hashing, JWT token management, and row-level authorization.

---

## 2. Tech Stack Overview

| Layer | Technology | Rationale / Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla ES6+) | Lightweight, zero build-step overhead, direct mastery of web fundamentals. |
| **Backend** | Python 3.11+, FastAPI | High performance, automatic OpenAPI docs, native async support, robust type hints via Pydantic. |
| **ORM** | SQLAlchemy 2.0 (Synchronous) | Standard Python ORM providing type-safe relational mapping, synchronous sessions with `psycopg2-binary`, and SQL injection prevention. |
| **Database** | PostgreSQL | Enterprise-ready relational database with JSONB payload support and strict relational constraints. |
| **Database Migrations** | Alembic | Safe database schema versioning and automated migration scripts executed via Docker entrypoint. |
| **Authentication** | JWT (JSON Web Tokens) & Passlib (Bcrypt) | Stateless authentication header pattern (`Bearer <token>`) with secure salted password hashing. |
| **Containerization** | Docker & Docker Compose | Consistent local and production container environments for API and Postgres services. |
| **Testing** | pytest & HTTPX | Automated unit testing and asynchronous API endpoint verification using an isolated test database. |

---

## 3. Functional Requirements

### 3.1 User Management & Authentication
- **User Registration**: New users can register with an email, full name, and password (minimum 8 characters).
- **User Login**: Secure authentication issuing short-lived JWT access tokens. Rate-limited to prevent brute-force attacks.
- **Session Persistence**: Stored token state for authenticated API interactions.
- **Profile & Password Management**: Retrieve/update profile details and update account password.

### 3.2 Resume Management
- **Create Resume**: Create a new resume draft with a custom title and template selection.
- **List Resumes**: View a dashboard list of all resumes created by the logged-in user.
- **Read/Edit Resume**: Fetch and modify details of any existing resume using a full JSON payload update strategy.
- **Duplicate Resume**: Clone an existing resume as a template for a new application.
- **Delete Resume**: Safely remove a resume with cascade deletion of child sections.

### 3.3 Resume Content Sections
Each resume supports structured data management across standard and custom sections:
1. **Personal / Contact Information**: Full Name, Professional Title, Email, Phone, Location, Portfolio, GitHub, LinkedIn, Summary statement.
2. **Work Experience**: Company, Position, Location, Start Date, End Date, Is Current, Bullet Point Descriptions, Display Order.
3. **Education**: Institution, Degree, Field of Study, Location, Start Date, End Date, GPA/Honors, Display Order.
4. **Skills**: Skill Name, Category (e.g., Frontend, Languages), Proficiency Level (e.g., Beginner, Advanced), Display Order.
5. **Projects**: Title, Description, Tech Stack used, Live/Repo URL, Start Date, End Date, Display Order.
6. **Certifications**: Name, Issuing Organization, Issue Date, Credential URL/ID, Display Order.
7. **Custom Sections**: Custom Title (e.g., Languages, Volunteer Work), Description / Bullet Points, Display Order.

### 3.4 Customization & Live Preview
- **Template Selection**: Toggle between visually distinct layout templates (e.g., Modern, Classic, Minimalist).
- **Theme Configuration**: Customize primary accent colors, font pairs, margins, and section-level ordering (`section_order`).
- **Live Preview**: Real-time side-by-side preview update as the user types or reorganizes items.

### 3.5 Export & Data Portability Requirements
- **PDF Export & Print Layout**:
  - Browser print dialog (`window.print()`) supported by dedicated clean print view endpoint (`GET /api/v1/resumes/{id}/print`).
  - `@media print` rules hiding UI controls, headers, and sidebars.
  - Print CSS rules specifying page boundaries (`@page { size: A4 portrait; margin: 12mm; }`) and avoiding line-break splitting across sections (`break-inside: avoid`).
- **JSON Export**: Download complete resume structure as a standardized JSON backup file.
- **JSON Import**: Upload a JSON backup file to create or restore a resume document via `POST /api/v1/resumes/import`.

---

## 4. Non-Functional Requirements

### 4.1 Performance
- **API Response Time**: Endpoints must return responses under 200ms for standard CRUD operations.
- **Client-Side Rendering**: Instant input reactivity in the live preview window without triggering full page reloads.

### 4.2 Security & Authorization
- **Password Hashing**: Passwords stored using `bcrypt` salted hash algorithm; plain text never persisted.
- **Authentication**: JWT token validation on protected API routes via HTTP `Authorization: Bearer <token>` header.
- **Row-Level Authorization**: Users strictly view, edit, duplicate, or delete only their own resumes (`WHERE resume.user_id == current_user.id`).
- **Input Validation**: Pydantic v2 schemas enforce field constraints, email formatting, and character limits.
- **Rate Limiting**: Auth endpoints (`/auth/login`, `/auth/register`) rate-limited to 5 attempts per minute per IP.
- **Configuration Security**: Environment variables managed via Pydantic `BaseSettings` reading from `.env` files; secrets strictly excluded from source control.

### 4.3 Data Integrity & Reliability
- **Relational Integrity**: Foreign key constraints with explicit CASCADE rules to prevent orphan records.
- **Validation Rules**: Mandatory field constraints (e.g., valid email formats, non-empty resume titles).

### 4.4 Code Quality & Maintainability
- **Clean Architecture**: Separation of concerns between API routes, service logic, data models, and schemas.
- **Modular Codebase**: Single-purpose modules easy to read, test, and debug.
- **Minimal Dependencies**: Minimal external library footprint to ensure beginner clarity.

### 4.5 Testing Requirements
- **Unit Tests**: Coverage for password hashing, JWT encoding/decoding, and Pydantic validation rules.
- **Integration Tests**: API route verification using `pytest` and `httpx.AsyncClient` connected to a dedicated test database (`TEST_DATABASE_URL`).
- **Database Isolation**: Tests execute against an isolated PostgreSQL test database or transaction-rollback setup.

---

## 5. Deployment & System Constraints
- **Browser Compatibility**: Modern evergreen browsers (Chrome, Firefox, Edge, Safari).
- **Docker Production Strategy**: Multi-container Docker Compose setup (`backend` and `db`).
- **Container Entrypoint**: Docker startup script executes database migrations (`alembic upgrade head`) before starting the Uvicorn web server.
