# CloudOpt / SecureVault

CloudOpt is a multi-cloud cost optimization and security platform. It provides a React dashboard backed by a Flask API for:

- AWS, Azure, and GCP cloud account management
- Cloud cost and usage analysis
- Optimization recommendations
- Repository security and dependency scanning
- JWT-based authentication with role-based admin endpoints
- Background scan processing with Celery and Redis
- JSON and PDF scan reports

## Project structure

```text
cloudProject/
├── frontend/                 # React 19 + Vite + Tailwind UI
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Application screens
│   │   ├── services/         # API clients
│   │   ├── store/            # Zustand state stores
│   │   └── hooks/            # React Query and app hooks
│   └── package.json
├── backend/
│   └── securevault/
│       ├── app/
│       │   ├── api/          # Flask blueprints and API routes
│       │   ├── core/         # App factory and extensions
│       │   ├── models/       # SQLAlchemy models
│       │   ├── services/     # Cloud, scanner, and optimizer services
│       │   └── tasks/        # Celery tasks
│       ├── tests/
│       ├── config/
│       ├── wsgi.py
│       └── requirements.txt
└── .gitignore
```

## Prerequisites

- Windows, macOS, or Linux
- Python 3.10 or newer
- Node.js 20.19 or newer (or 22.12+) and npm
- Redis 6 or newer for Celery workers and distributed rate limiting
- PostgreSQL is optional; development defaults to SQLite

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/AnirudhSGopal/Multi-cloudcostoptimizer.git
cd Multi-cloudcostoptimizer
```

### 2. Configure the backend

Open PowerShell in `backend\securevault`:

```powershell
cd backend\securevault
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

The application can start with its development defaults. For a useful local setup, set these values in `backend\securevault\.env`:

```dotenv
FLASK_ENV=development
SECRET_KEY=replace-with-a-long-random-value
JWT_SECRET_KEY=replace-with-another-long-random-value
DATABASE_URL=sqlite:///instance/securevault.db
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173
CLONE_BASE_DIR=C:/temp/securevault_repos
MAX_REPO_SIZE_MB=500

# Required for encrypted cloud credentials
ENCRYPTION_KEY=replace-with-a-valid-fernet-key

# Required for Gemini-powered recommendations and diagnostics
GEMINI_API_KEY=your-gemini-api-key
```

Never commit `.env`, API keys, cloud credentials, or private keys. Generate a Fernet encryption key with:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Install the frontend

Open a second terminal in `frontend`:

```powershell
cd frontend
npm install
```

If the API is not running on the default address, create or update `frontend\.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:5000
```

## Running locally

Start Redis first if you want background scans or production-like rate-limit storage.

### Start the backend

From `backend\securevault` with the virtual environment activated:

```powershell
flask --app wsgi:app run --debug
```

The API runs at `http://127.0.0.1:5000`. A health check is available at:

```text
http://127.0.0.1:5000/health
```

The included Windows helper can also be used:

```powershell
.\scripts\start_flask.bat
```

### Start the Celery worker

In another backend terminal:

```powershell
cd backend\securevault
.\.venv\Scripts\Activate.ps1
celery -A wsgi.celery worker --loglevel=info --pool=solo
```

Or run `.\scripts\start_worker.bat` from the backend directory.

### Start the frontend

From `frontend`:

```powershell
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

### Repository scan and Gemini review

Repository scans automatically request a secondary Gemini review when an API key,
Redis-backed quota, and the Gemini service are available. The review sends Google
up to 12 bounded source excerpts (at most 24,000 characters total) after common
secret-like values and email addresses are redacted. Redaction is best-effort, not
a guarantee; do not scan repositories whose source you are not authorized to share.
Gemini results are advisory and may be incomplete. If the budget service or model
is unavailable, the scan reports that status and still returns enabled rule-based
results. Uploaded-folder scans do not send source to Gemini.

### Run the backend stack with Docker Compose

Copy `backend\securevault\.env.example` to `backend\securevault\.env`, replace the secret placeholders (especially `ENCRYPTION_KEY`), then start the local API, worker, and Redis:

```powershell
docker compose up --build -d
docker compose exec backend flask --app wsgi:app db upgrade
```

The local Compose file uses SQLite and Redis in named volumes. The production Compose file uses Supabase PostgreSQL instead.

## Database

Development defaults to SQLite at `backend\securevault\instance\securevault.db`. The app does not create tables on startup; use Flask-Migrate to create or update the schema:

```powershell
cd backend\securevault
.\.venv\Scripts\Activate.ps1
flask --app wsgi:app db upgrade
```

For PostgreSQL, set `DATABASE_URL` to a SQLAlchemy PostgreSQL URL before starting the backend, for example:

```dotenv
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/securevault_db
```

## API overview

All authenticated routes use the `/api/v1` prefix:

| Area | Main endpoints |
| --- | --- |
| Authentication | `/api/v1/auth/register`, `/login`, `/refresh`, `/me`, `/logout` |
| Scanning | `/api/v1/scan/start`, `/api/v1/scan/<job_id>` |
| Cloud accounts | `/api/v1/cloud/accounts`, `/api/v1/cloud/test` |
| Reports | `/api/v1/reports/<job_id>/json`, `/api/v1/reports/<job_id>/pdf` |
| Administration | `/api/v1/admin/users`, `/cloud-accounts`, `/scans`, `/stats`, `/system-health` |
| Simple audit | `/api/audit` |
| Liveness / readiness | `/health`, `/ready` |

After login, send the returned access token as:

```text
Authorization: Bearer <access-token>
```

## Creating an administrator

Set optional admin values in `.env`, then run:

```powershell
cd backend\securevault
.\.venv\Scripts\Activate.ps1
python scripts\create_admin.py
```

The script defaults to `admin@cloudopt.ai`, username `admin`, and a development password if values are not supplied. Change these values before using the application outside local development.

## Testing and quality checks

### Backend tests

```powershell
cd backend\securevault
.\.venv\Scripts\Activate.ps1
pytest
```

### Frontend lint and production build

```powershell
cd frontend
npm run lint
npm run build
```

## Common issues

- **Frontend cannot reach the API:** confirm Flask is running on port 5000 and `VITE_API_BASE_URL` points to that address.
- **Background scans remain pending:** start Redis and a Celery worker.
- **Cloud credential operations fail:** set `ENCRYPTION_KEY` to a valid Fernet key and configure the provider credentials required by the selected cloud.
- **Gemini features are unavailable:** set `GEMINI_API_KEY`; core local development does not require it.
- **Port already in use:** run Flask with `--port 5001` and update `VITE_API_BASE_URL`, or run Vite with `--port 5174`.

## Production deployment

Do not use Flask's development server in production. Run the backend container behind the host's TLS-terminating proxy/load balancer, deploy the frontend separately to Vercel or Netlify, and keep secrets in the platform's secret manager (never in a frontend `VITE_*` variable).

### Required backend environment

Set these on both the backend and Celery worker:

| Variable | Purpose |
| --- | --- |
| `FLASK_ENV=production` | Selects production config; debug and exception propagation remain disabled. |
| `SECRET_KEY` | Strong, random Flask signing secret. |
| `JWT_SECRET_KEY` | Independent, strong JWT signing secret. |
| `ENCRYPTION_KEY` | Fernet key for encrypted cloud-provider credentials. |
| `DATABASE_URL` | Supabase PostgreSQL connection URL. |
| `CORS_ORIGINS` | Comma-separated exact frontend origins including scheme; never `*`. |
| `REDIS_URL` | Redis broker/result backend and rate-limit storage. |

Generate the encryption key locally with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Generate distinct random values for `SECRET_KEY` and `JWT_SECRET_KEY`; do not reuse the encryption key.

Optional controls include `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, and `DB_POOL_TIMEOUT` (defaults sized for a small pool); `GUNICORN_WORKERS`; `GEMINI_API_KEY`, `GEMINI_DAILY_USER_QUOTA`, and `GEMINI_DAILY_GLOBAL_CAP`; `GITHUB_TOKEN`; and `SENTRY_DSN`. Provider credentials should normally be entered through the application and are encrypted at rest. `SENTRY_DSN` is optional and enables Sentry only when configured.

### Supabase and migrations

Create a Supabase project and allow network access from both the migration runner and backend host. Use the direct or session-pooler connection for schema migrations. Use the Supabase pooler connection appropriate to the backend host (typically transaction mode) for the running app, and keep the connection URL in the secret manager. The backend normalizes `postgres://` to `postgresql://` and requires TLS (`sslmode=require`) for non-local PostgreSQL hosts.

Back up the database before applying migrations. With the production environment loaded, run this as a deliberate release step (or dispatch the manual **Production migration** GitHub Actions job):

```powershell
cd backend\securevault
flask --app wsgi:app db upgrade
flask --app wsgi:app db current
```

Do not run migrations automatically on every application start or every push.

### Backend and frontend deployment

Build and publish a versioned backend image; do not deploy a floating `latest` tag:

```powershell
docker build -t ghcr.io/your-org/cloudopt-backend:release-tag backend\securevault
docker push ghcr.io/your-org/cloudopt-backend:release-tag
```

Set `BACKEND_IMAGE` and the production variables in a host-side environment file (for example `.env.production`, excluded from Git). Review `docker-compose.prod.yml`, then deploy:

```powershell
docker compose -f docker-compose.prod.yml --env-file .env.production pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

The production compose example uses an external Supabase database and a private Redis service. Prefer managed Redis with authentication and TLS where supported by the hosting environment. Restrict direct public access to the container port when a reverse proxy is available.

Deploy `frontend` from its own directory to Vercel or Netlify. Set the build-time variable `VITE_API_BASE_URL` to the public HTTPS API origin (for example `https://api.example.com`) and set backend `CORS_ORIGINS` to the exact deployed frontend origin. `VITE_*` variables are public and must never contain credentials. The API client reads its base URL from `import.meta.env.VITE_API_BASE_URL`.

### Rollback and backups

Before release, record the currently deployed image tag and output of `flask db current`, and take/verify a Supabase backup or point-in-time recovery checkpoint. To roll back application code, set `BACKEND_IMAGE` to the previous known-good tag and redeploy with Compose. Only downgrade the schema when the migration is known to be reversible and compatible with the previous image:

```powershell
flask --app wsgi:app db downgrade <previous-revision>
```

For a first-schema deployment, the pre-migration revision is `base`. A downgrade can remove data; restore from the verified backup instead when required. Confirm Supabase backup/PITR retention and perform a restore drill appropriate to the service's recovery objectives.

### Short operational runbook

- **API is up but traffic fails:** check `/health` for liveness and `/ready` for database/Redis availability; inspect host networking, Supabase TLS/allow-list settings, and `REDIS_URL`.
- **Browser reports CORS errors:** make `CORS_ORIGINS` exactly match the deployed frontend origin (scheme and host, no wildcard), then restart the backend.
- **Background jobs stay pending:** confirm Redis is healthy and the Celery worker uses the same image/configuration as the API.
- **Gemini results fall back to heuristics:** check the API key and spend caps; repeated upstream failures intentionally open the circuit breaker temporarily.
- **Release fails after a schema change:** compare the deployed image and `flask db current` with the release record; roll back to the previous image and downgrade only after assessing compatibility and backup status.
- **Investigating errors:** use redacted structured logs and readiness status; never paste secrets, credentials, or full user emails into logs or issue reports.

### Privacy and stored data

The service stores account usernames and email addresses, password hashes (not plaintext passwords), encrypted cloud-provider credentials, repository URLs and branches submitted for scanning, scan findings/results, and cloud cost/usage metrics and optimization records. Operational metadata is also stored for authentication, ownership, and background-job processing. Restrict database and log access, configure a retention/deletion policy for scan and metric data, and disclose the applicable retention and processing practices to users before launch.

Repository scans report findings and per-check coverage; they do not calculate an overall security score. Unsupported or unavailable checks are surfaced as partial or unavailable coverage rather than being described as clean. Dependency checks use manifest metadata, including exact Maven/Gradle versions where supported; they do not execute repository build scripts. Gemini source review is off unless a user explicitly opts in for that scan. When enabled, bounded, commonly secret-like redacted source excerpts are sent to Google Gemini and any returned issues are advisory; redaction is heuristic and cannot guarantee removal of every secret.

## License

No license file is currently included in this repository.
