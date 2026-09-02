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
- Node.js 18 or newer and npm
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
pip install -r requirements.txt
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
CLOUD_ENCRYPTION_KEY=replace-with-a-valid-fernet-key

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

## Database

In development, SQLAlchemy creates `backend\securevault\instance\securevault.db` automatically when the Flask app starts.

To explicitly create tables:

```powershell
cd backend\securevault
.\.venv\Scripts\Activate.ps1
python scripts\setup_db.py
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
| Health | `/health` |

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
- **Cloud credential operations fail:** set `CLOUD_ENCRYPTION_KEY` to a valid Fernet key and configure the provider credentials required by the selected cloud.
- **Gemini features are unavailable:** set `GEMINI_API_KEY`; core local development does not require it.
- **Port already in use:** run Flask with `--port 5001` and update `VITE_API_BASE_URL`, or run Vite with `--port 5174`.

## Production notes

Do not use Flask's development server in production. Set `FLASK_ENV=production`, provide strong secrets and a production database, configure Redis, and run behind a production WSGI server such as Gunicorn (or an equivalent Windows-compatible deployment server). Restrict `CORS_ORIGINS` to the deployed frontend origin and keep all cloud/API credentials in the deployment secret manager.

## License

No license file is currently included in this repository.
