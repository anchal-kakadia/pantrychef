
# PantryChef 🥦

A smart pantry management and recipe recommendation web app that helps you
stop wasting food and answer the daily question of *"what should I cook tonight?"*

---

## What it does

- **Track your pantry** — add grocery items manually; items without an expiry
  date get an AI-estimated shelf life automatically via GPT-4o.
- **Colour-coded urgency** — your pantry is sorted by how soon things expire.
- **Get alerted before things expire** — daily email listing items expiring
  within 3 days, sent via AWS SES.
- **Recipes built around your pantry** — GPT-4o generates personalised recipe
  suggestions from what you actually have, streamed token-by-token as they
  generate. Respects your dietary preferences, allergies, spice tolerance, and
  protein goals.
- **Preference-aware** — set high-protein goals, spice level (1–5), allergens,
  and cuisine preference once; every recipe suggestion respects them.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) + TailwindCSS |
| Backend | Python 3.12 + FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy 2.0 + Alembic |
| AI | OpenAI GPT-4o (shelf-life inference + streaming recipes) |
| Background Jobs | Celery + Redis |
| Email Alerts | AWS SES |
| Deployment | AWS (Elastic Beanstalk/ECS, RDS, S3, CloudFront) |

---

## Project Structure

```
pantrychef/
├── app/
│   ├── main.py            # FastAPI app factory, CORS, lifespan
│   ├── config.py          # Pydantic Settings — all env vars validated at startup
│   ├── database.py        # Async SQLAlchemy engine + session factory
│   ├── models/            # SQLAlchemy ORM models (User, PantryItem, etc.)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routers/           # FastAPI route handlers
│   ├── services/          # Business logic (auth, pantry, LLM, email)
│   └── workers/           # Celery tasks
├── alembic/               # Database migrations
├── tests/                 # pytest integration tests
├── docs/                  # Requirements and architecture documents
├── docker-compose.yml     # Local Postgres + Redis
├── pyproject.toml         # Dependencies and tooling config
├── Makefile               # Dev shortcuts (make dev, make test, make migrate)
└── .env.example           # Required environment variables
```

---

## Local Setup

### Prerequisites
- Python 3.12
- Docker Desktop (for local Postgres + Redis)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/pantrychef.git
cd pantrychef

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Set up environment variables
cp .env.example .env
# Fill in SECRET_KEY, DATABASE_URL, REDIS_URL at minimum

# 5. Start Postgres + Redis
make db-up

# 6. Run database migrations
make migrate

# 7. Start the API
make dev
```

API runs at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## Environment Variables

See `.env.example` for the full list. Required to run locally:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | Postgres connection string (asyncpg) |
| `REDIS_URL` | Redis connection string |
| `OPENAI_API_KEY` | For shelf-life inference and recipe generation |
| `AWS_ACCESS_KEY_ID` | For SES email alerts |
| `AWS_SECRET_ACCESS_KEY` | For SES email alerts |
| `SES_SENDER_EMAIL` | Verified sending address in AWS SES |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account, returns JWT |
| `POST` | `/auth/token` | Login, returns JWT |
| `GET` | `/users/me` | Get current user profile |
| `PATCH` | `/users/me/preferences` | Update dietary preferences |
| `GET` | `/pantry/items` | List all active pantry items |
| `POST` | `/pantry/items` | Add item (triggers AI shelf-life if no expiry) |
| `GET` | `/pantry/items/{id}` | Get single item |
| `PATCH` | `/pantry/items/{id}` | Update item |
| `DELETE` | `/pantry/items/{id}` | Soft delete item |
| `GET` | `/pantry/items/expiring-soon` | Items expiring within N days |
| `GET` | `/recipes/suggest` | Stream AI recipe suggestions (SSE) |

---

## Running Tests

```bash
make test
```

Tests use a separate `pantrychef_test` database and never touch your dev data.
Each test runs with a fresh database state.

---

## Documentation

- [Software Requirements Document](docs/requirements.md)
- [System Design Document](docs/PantryChef_Design_Document.docx)

---

## Build Status

| Phase | Status |
|---|---|
| Phase 1 — Project scaffold | ✅ Done |
| Phase 2 — Backend (auth + pantry CRUD) | ✅ Done |
| Phase 3 — AI layer (shelf-life + recipes) | 🚧 In progress |
| Phase 4 — Background jobs + email alerts | ⏳ Upcoming |
| Phase 5 — React frontend | ⏳ Upcoming |
```
