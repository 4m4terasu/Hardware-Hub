# Hardware Hub

AI-native internal hardware management tool for managing company equipment, rentals, and inventory audits.

## Overview

Hardware Hub is a full-stack MVP for managing internal hardware inventory. It includes:

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

## Features

- Simple login system for admin-created users only
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
  - deterministic findings for risky / dirty data
  - Gemini summary layered on top of deterministic findings
  - graceful fallback when Gemini is unavailable

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Git

## Environment Variables

Create a local `.env` file in the repo root.

### Required for local app
```env
JWT_SECRET_KEY=change-me-in-local-env
```

### Required for Gemini-powered audit summaries
```env
GEMINI_API_KEY=your_real_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### Example `.env.example`
```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

## Default Bootstrap Admin

On startup, the backend seeds a default admin account if it does not already exist.

### Default credentials
```text
Email: admin@booksy.com
Password: Admin123!
```

This is intentionally convenient for local review only. In a real environment, bootstrap credentials should be injected securely and rotated immediately.

## Backend Setup

From the repo root:

```bash
python -m venv .venv
```

Activate the virtual environment:

**Windows (PowerShell)**
```powershell
.\.venv\Scripts\Activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

## Run Backend

From the repo root with the virtual environment active:

```bash
uvicorn backend.app.main:app --reload
```

Backend will run at:
```text
http://127.0.0.1:8000
```

Swagger docs:
```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

From the `frontend` directory:

```bash
npm install
```

## Run Frontend

From the `frontend` directory:

```bash
npm run dev
```

Frontend will run at:
```text
http://localhost:5173
```

## Run Tests

From the repo root with the virtual environment active:

```bash
python -m pytest backend/tests -q
```

Current test coverage focuses on critical backend flows:

- cannot rent safety-flagged hardware
- non-admin cannot access admin endpoints
- admin cannot delete in-use hardware
- audit detects known seed traps

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

docs/
  ai-log.md
  prompt-trail.md
```

## ✅ Fully Implemented

### Authentication and Access Control
- JWT-based login flow
- bootstrap admin seeding
- `/api/auth/login`
- `/api/auth/me`
- protected hardware routes
- admin-only routes for user and hardware management
- frontend route guards for authenticated pages
- non-admin users redirected away from `/admin`

### Admin Command Center
- create standard users
- create admin users
- create hardware items
- delete hardware items
- toggle repair status
- backend enforcement for invalid admin actions
- functional admin UI for all core admin actions

### Smart Dashboard
- authenticated inventory list
- status filter
- brand filter
- sorting by: id, name, brand, purchase date, status
- visible admin link only for admins
- logout flow

### Rental Engine
- rent hardware endpoint
- return hardware endpoint
- backend guards for impossible states
- rent / return actions available from the dashboard UI
- return action limited in UI to hardware assigned to the current user
- safety-note blocking for dangerous hardware such as the Dell XPS example
- consistent success / error feedback on rent and return actions

### Inventory Auditor
- deterministic audit endpoint
- structured findings with issue codes and severities
- rules for: future purchase date, malformed purchase date, missing purchase date, invalid status, missing brand, suspicious brand typo, safety-blocking notes, damage-related history, duplicate seed ID detected during import
- Gemini-based summary layer on top of deterministic findings
- fallback mode when Gemini is unavailable

### Testing
- 4 critical backend tests are implemented and passing

### Documentation
- README
- AI development log
- prompt trail

## ⚡ Shortcuts and Hacks

### localStorage for JWT

I stored the access token in `localStorage` for the MVP.

**Why this was acceptable for the MVP**
- simplest approach for a short assignment
- easy to debug manually
- survives page refresh
- reduced auth implementation overhead so I could focus on the required business logic

**Production alternative**
- HttpOnly secure cookies or a server-managed session

**Trade-off**
- `localStorage` is more exposed to XSS risk than HttpOnly cookies

### Raw-first data model instead of a fully normalized schema

I intentionally preserved raw seed fields such as `purchase_date_raw` and `status_raw` instead of normalizing everything immediately.

**Why this was acceptable for the MVP**
- the provided dataset is intentionally dirty
- preserving source truth first made the audit layer easier to explain and validate
- it avoided premature cleanup logic that might hide source problems

**Production alternative**
- separate raw ingestion from normalized operational tables
- structured validation pipeline with clean canonical columns

### No refresh tokens

I implemented a simple short-lived JWT flow without refresh tokens.

**Why this was acceptable for the MVP**
- reduced auth complexity
- enough for local demo and reviewer testing

**Production alternative**
- refresh-token rotation or session-based auth

### No pagination

Inventory lists are currently loaded in a single response.

**Why this was acceptable for the MVP**
- small dataset
- faster implementation
- cleaner demo flow

**Production alternative**
- paginated backend queries and UI pagination controls

### Brand filter built from loaded items

The brand filter options are derived from the currently loaded hardware list in the frontend.

**Why this was acceptable for the MVP**
- simple implementation
- no extra metadata endpoint required

**Production alternative**
- backend-provided distinct filter values or faceted search metadata

### AI-assisted development process

I used AI heavily, but not passively.

**How I used it**
- ChatGPT was my primary planning and implementation partner
- Claude was used for cross-verification on technical decisions and edge cases
- Gemini was used inside the product for the Inventory Auditor summarization layer

**How I controlled quality**
- I did not blindly accept output
- I verified flows manually in Swagger, PowerShell, and the browser
- I cross-checked important architectural or scope decisions
- when AI produced a weaker solution, I corrected it before moving forward

## ⚠️ Partial / Missing

- no pagination yet
- no email validation beyond basic form/input handling on user creation
- hard delete instead of soft delete / archive flow
- minimal frontend form validation
- no live deployment yet

## 🔮 Next Steps (24h Roadmap)

If I had one more day, my top three priorities would be:

1. **Deploy the app** — backend + frontend live demo, production environment variables, simple reviewer-friendly hosted version
2. **Harden validation and UX** — stronger frontend validation, clearer empty/error states, better audit presentation and actionability
3. **Improve data lifecycle and production safety** — soft delete / archive flow, better auth/session handling, more robust input validation and admin safeguards

## AI Development Notes

See:
- `docs/ai-log.md`
- `docs/prompt-trail.md`

## Submission Notes

This project was intentionally built as a strong MVP rather than a broad feature dump. I prioritized:

- clear core business logic
- explainable architecture
- explicit handling of dirty input data
- deterministic validation before AI summarization
- honest documentation of shortcuts and missing pieces