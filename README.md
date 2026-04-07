# Hardware Hub

AI-native internal hardware management tool for managing company equipment, rentals, and inventory audits.

## Live Demo

- Frontend: `https://hardware-hub-seven.vercel.app/`
- Backend health: `https://hardware-hub-production-3e01.up.railway.app/api/health`
- Backend docs: `https://hardware-hub-production-3e01.up.railway.app/docs`

## Overview

Hardware Hub is a full-stack MVP for managing internal hardware inventory.

It includes:
- admin-only account creation
- admin-only hardware management
- authenticated inventory dashboard
- rent / return flow with backend guardrails
- deterministic inventory audit rules
- Gemini-powered audit summarization on top of deterministic findings

The project was intentionally built as a practical, interview-defensible MVP: stable core flows first, explicit trade-offs, and clear boundaries between deterministic logic and AI-assisted summarization.

## Tech Stack

### Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic Settings
- python-jose
- passlib + bcrypt
- Google GenAI SDK (`google-genai`)
- pytest

### Frontend
- Vue 3
- Vite
- TypeScript

### Hosting
- Railway (backend)
- Vercel (frontend)
- Docker

## Core Features

- Login system for admin-created users only
- Admin Command Center
  - create users
  - add hardware
  - delete hardware
  - toggle repair status
- Smart dashboard
  - list hardware
  - filter by status and brand
  - sort by multiple fields
- Rental engine
  - rent available hardware
  - return hardware assigned to the current user
  - backend guardrails for impossible states
- Inventory Auditor
  - deterministic findings for dirty / risky data
  - Gemini summary layered on top
  - graceful fallback when Gemini is unavailable

## Local Setup

### 1. Create virtual environment

From repo root:

```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\Activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

## Local Environment Variables

Create a `.env` file in the repo root:

```env
APP_NAME=Hardware Hub
APP_ENV=development
FRONTEND_URL=http://localhost:5173
DATABASE_URL=sqlite:///./hardware_hub.db

JWT_SECRET_KEY=change-me-in-local-env
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

BOOTSTRAP_ADMIN_EMAIL=admin@booksy.com
BOOTSTRAP_ADMIN_PASSWORD=Admin123!

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

Create `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If you want to test the local frontend against the deployed backend instead:

```env
VITE_API_BASE_URL=https://hardware-hub-production-3e01.up.railway.app
```

## Run Locally

### Backend

From repo root:

```bash
uvicorn backend.app.main:app --reload
```

Backend:

* `http://127.0.0.1:8000`
* `http://127.0.0.1:8000/docs`

### Frontend

From `frontend/`:

```bash
npm run dev
```

Frontend:

* `http://localhost:5173`

## Tests

From repo root:

```bash
python -m pytest backend/tests -q
```

Current automated tests cover critical backend flows:

* cannot rent safety-flagged hardware
* non-admin cannot access admin endpoints
* admin cannot delete in-use hardware
* audit detects known seed traps

## Deployment

### Backend

* deployed on Railway
* Docker-based deployment from repo root
* SQLite persisted on Railway volume mounted at `/data`
* production database URL:

  * `sqlite:////data/hardware_hub.db`

### Frontend

* deployed on Vercel from `frontend/`
* Vite project
* `frontend/vercel.json` rewrites SPA routes to `index.html`
* production frontend calls Railway backend through:

  * `VITE_API_BASE_URL=https://hardware-hub-production-3e01.up.railway.app`

## Bootstrap Admin

On startup, the backend seeds a bootstrap admin only if no admin exists.

### Local default credentials

```text
Email: admin@booksy.com
Password: Admin123!
```

This is for local convenience only.

In production, bootstrap credentials are injected through Railway environment variables.

## Project Structure

```text
backend/
  app/
    config.py
    db.py
    main.py
    dependencies/
    models/
    routes/
    schemas/
    services/
    utils/
  data/
  tests/

frontend/
  src/
    api/
    router/
    views/
  vercel.json

docs/
  ai-log.md
  prompt-trail.md
```

## ✅ Fully Implemented

### Authentication and Access Control

* JWT-based login flow
* bootstrap admin seeding
* `/api/auth/login`
* `/api/auth/me`
* protected routes
* admin-only routes for user and hardware management
* non-admin users redirected away from `/admin`

### Admin Command Center

* create standard users
* create admin users
* create hardware items
* delete hardware items
* toggle repair status
* auto-scroll to feedback banner after admin actions

### Smart Dashboard

* authenticated inventory list
* status filter
* brand filter
* sorting by id, name, brand, purchase date, and status
* visible admin link only for admins
* auto-scroll to feedback banner after rent / return actions

### Rental Engine

* rent hardware endpoint
* return hardware endpoint
* backend guards for impossible states
* return limited to the assigned user
* safety-note blocking for dangerous hardware

### Inventory Auditor

* deterministic audit endpoint
* structured findings with issue codes and severities
* Gemini summary layer on top of deterministic findings
* fallback mode when Gemini is unavailable

### Deployment

* frontend deployed on Vercel
* backend deployed on Railway
* persistent SQLite storage configured on Railway volume
* critical flows manually verified in production

## ⚡ Shortcuts and Trade-offs

### localStorage for JWT

I stored the access token in `localStorage` for the MVP.

Why this was acceptable:

* simplest implementation for a short assignment
* easy to debug
* survives refresh

Production alternative:

* HttpOnly cookies or server-managed sessions

### Raw-first data model

I preserved raw fields such as `purchase_date_raw` and `status_raw` instead of normalizing everything immediately.

Why this was acceptable:

* the seed dataset is intentionally dirty
* it made the audit layer easier to explain and verify
* it preserved source issues instead of hiding them early

Production alternative:

* separate raw ingestion from normalized operational tables

### SQLite in production for the hosted MVP

I kept SQLite for the live demo and persisted it on a Railway volume.

Why this was acceptable:

* matches the assignment’s file-based DB direction
* keeps deployment simple and reviewer-friendly

Production alternative:

* PostgreSQL with managed migrations and backups

### No refresh tokens

I implemented a short-lived JWT flow without refresh tokens.

Production alternative:

* refresh-token rotation or session-based auth

## ⚠️ Partial / Missing

* no pagination yet
* hard delete instead of soft delete / archive flow
* minimal frontend form validation
* no frontend or e2e automated tests yet
* no password reset / email verification flow
* audit history is generated on demand and not persisted

## 🔮 Next Steps

If I had one more day, my top priorities would be:

1. improve validation and UX polish
2. add pagination and better data lifecycle handling
3. harden production auth and session handling

## AI Development Notes

See:

* `docs/ai-log.md`
* `docs/prompt-trail.md`
