# Mini CRM with Async Summarization (FastAPI)

Small REST API with authentication, role-based access (Admin/Agent), SQL storage, and an asynchronous summarization worker. Dockerized and deployable to Koyeb. Includes Swagger docs and tests.

## Features
- Auth: email/password signup & login, JWT, roles `ADMIN`/`AGENT` (RBAC)
- Notes: `raw_text`, `summary`, `status` (`queued|processing|done|failed`), timestamps
- Async summarize: background worker polls DB and fills summaries
- SQL + migrations: SQLAlchemy 2.x + Alembic
- Docker & Compose: web + worker + Postgres
- Docs & tests: OpenAPI/Swagger at `/docs`, pytest suite

## Tech Stack
- FastAPI + Uvicorn
- SQLAlchemy 2.x + Alembic
- Pydantic v2, python-jose (JWT), passlib[bcrypt]
- Postgres or SQLite for dev

## Quickstart (Windows PowerShell)

```pwsh
# 1) Create virtual env
python -m venv .venv
. .venv/Scripts/Activate.ps1

# 2) Install deps
pip install -e .[dev]

# 3) Configure env
Copy-Item .env.example .env
# (edit values if needed)

# 4) Run DB migrations
alembic upgrade head

# 5) Start API server
uvicorn app.main:app --reload --port 8000

# 6) Start worker (new terminal)
. .venv/Scripts/Activate.ps1
python -m app.worker
```

## Configuration
See `.env.example` for defaults. Important vars:
- `DATABASE_URL` (e.g., `sqlite+aiosqlite:///./app.db` or `postgresql+psycopg://user:pass@host:5432/db`)
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

## Using the API
Open Swagger UI at `/docs`.

### Auth
- Signup: `POST /auth/signup`
	- JSON: `{ "email": "user@example.com", "password": "Secret123!", "role": "AGENT" }`
- Login (JSON): `POST /auth/login`
	- JSON: `{ "email": "user@example.com", "password": "Secret123!" }`
- Login (Swagger Authorize via OAuth2 Password):
	- Token URL: `/auth/token`
	- username: your email (e.g., `admin@example.com`)
	- password: your password
	- client_id / client_secret: leave blank
	- If you see 422, refresh `/docs` and try again.

### Notes
- Create: `POST /notes`
	- JSON: `{ "raw_text": "Call Alice about Q3 renewal..." }`
- Get one: `GET /notes/{id}` → shows `status` and `summary` when ready
- List: `GET /notes?limit=20&offset=0&status=queued|processing|done|failed&q=search`
	- Role-based visibility: Agents see only their own notes; Admins see all

## Docker
```pwsh
# Build
docker build -t mini-crm-ai:latest .

# Run with SQLite (dev only)
docker run --env-file .env -p 8000:8000 mini-crm-ai:latest
```
For Postgres, set `DATABASE_URL` accordingly.

### Docker Compose (web + worker + Postgres)
1) Set DB URL in `.env`:
	 - `DATABASE_URL=postgresql+psycopg://app:app@db:5432/app`
2) Start services:
```pwsh
docker compose up --build
```
3) Run migrations once (inside `web`):
```pwsh
docker compose exec web alembic upgrade head
```
4) Visit `http://localhost:8000/docs`.

## Deploy to Koyeb (free tier)
1) Push repo to GitHub.
2) Create service `web` from Dockerfile:
	 - Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3) Create service `worker` from same repo:
	 - Command: `python -m app.worker`
4) Configure env vars: `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`.
5) Run one-off migration: `alembic upgrade head` with the same env.
6) Use the public URL and open `/docs`.

## Tests
```pwsh
pytest -q
```

## Troubleshooting
- 401/403: Ensure correct Bearer token and role.
- DB errors: Check `DATABASE_URL`; run migrations.
- Worker idle: Confirm note is `queued` and check worker logs; polling interval applies.
- CORS (with frontend): configure allowed origins in settings.
- JWT validity: check system clock and token expiry settings.
