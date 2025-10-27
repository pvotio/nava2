# Nava2 - Asynchronous Reporting Platform

Nava2 is a **modern, asynchronous reporting platform** built with [FastAPI](https://fastapi.tiangolo.com/), [Celery](https://docs.celeryq.dev/), and [PostgreSQL](https://www.postgresql.org/).  
It enables dynamic report generation based on **external data sources** (such as MSSQL) and customizable **Python-driven templates**, producing downloadable **PDF reports** through a headless [Puppeteer](https://pptr.dev/) service.

---

## Overview

### Key Features
- **Async report generation** with Celery and Redis  
- **Templated reports** defined in a remote GitHub repository  
- **Dynamic Python logic** and validation for each report  
- **Multi-database support** (MSSQL, PostgreSQL, MySQL, MariaDB — extensible)  
- **Automated PDF rendering** using a Node.js Puppeteer microservice  
- **Admin endpoints** for monitoring, syncing, and auditing reports  
- **Secure authentication** via JWT with role-based access (User, Admin)

---

## ⚙️ Environment Configuration

### Example `.env`

```bash
# Core
SECRET_KEY=change-me
BASE_URL=http://localhost:8000
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Storage
MEDIA_DIR=/data/media
MEDIA_URL=/files

# Databases
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/nava2
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# MSSQL connection (for report data)
MSSQL_DSN=Driver={ODBC Driver 18 for SQL Server};Server=your-server,1433;Database=yourdb;UID=user;PWD=pass;Encrypt=yes;TrustServerCertificate=yes;
```

Also copy `db.env.example` → `db.env` for PostgreSQL container credentials.

---

## Quick Start (Docker Compose)

Nava2 ships with a ready-to-run **Docker Compose** setup for local development.

```bash
# Build and start all services
docker compose up --build
```

### Services

| Service | Description | Port |
|----------|--------------|------|
| **web** | FastAPI application (REST API + docs) | 8000 |
| **worker** | Celery worker processing report tasks | — |
| **beat** | Celery beat scheduler (periodic jobs) | — |
| **generator** | Puppeteer PDF renderer | 3000 (internal) |
| **postgres** | PostgreSQL database | 5432 |
| **redis** | Redis (broker & cache) | 6379 |

---

## Concepts

### 1. Templates Repository
Each report template lives in a GitHub repo and defines:
- **`map.json`** — registry of available templates, arguments, and metadata
- **`logic.py`** — main script generating placeholders for rendering
- **`test.py`** — optional pre-check or data validation logic
- **`template.html`** — Jinja2-compatible HTML file for rendering

Templates are fetched and cached in Redis. The system periodically syncs the index via Celery beat.

---

### 2. Report Lifecycle

| Stage | Description |
|--------|-------------|
| **Pending (P)** | Report request created |
| **Fetched (F)** | Template and arguments validated |
| **Generated (G)** | PDF successfully rendered |
| **Failed (F)** | Exception occurred during processing |
| **Deleted (D)** | Cleaned up or expired |

---

## Authentication

JWT-based authentication.

- `POST /api/auth/login` → get token  
- Use the token in `Authorization: Bearer <token>` header for all protected endpoints  
- Admin endpoints require `is_admin=True` flag on the user

Public endpoints (e.g., `GET /api/reports/{hash_id}`) allow unauthenticated access to finalized reports.

---

## Endpoints (Highlights)

| Method | Endpoint | Description | Auth |
|--------|-----------|-------------|------|
| **POST** | `/api/reports` | Submit new report request | ✅ Required |
| **GET** | `/api/reports/{hash_id}` | Publicly retrieve report and PDF link | ❌ Optional |
| **POST** | `/api/admin/templates/sync` | Force sync templates index and assets | ✅ Admin |
| **GET** | `/api/admin/reports` | List and audit reports | ✅ Admin |

Explore the full OpenAPI documentation at:  
**[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## Media Files

Generated PDFs are stored inside a shared Docker volume (`media`) and served directly by the FastAPI application.

- Directory inside containers: `/files`
- URL prefix: `/files`
- Example URL:  
  ```
  http://localhost:8000/files/report_hello_simple_1234abcd.pdf
  ```

---

## Development & Tooling

### Run migrations
```bash
docker compose exec web alembic upgrade head
```

### Create or update a user
```bash
docker compose exec web python -m app.cli create-user -e user@example.com -p secret
```

### Logs (for debugging)
```bash
docker compose logs -f web
docker compose logs -f worker
```

### Static checks
```bash
ruff check . --fix
```

---

## Contributing

We welcome contributions!  
Please ensure PRs follow the existing code style and include tests when applicable.

1. Fork this repository  
2. Create a new branch (`feature/my-feature`)  
3. Submit a pull request once tested
