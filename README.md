# HCP CRM Module

AI-first CRM module for pharmaceutical field reps to log interactions with Healthcare Professionals (HCPs). Dual-input: structured form + conversational AI chat powered by LangGraph + Groq.

## Project Structure

```
hcp/
├── backend/          # Python FastAPI + LangGraph agent
│   ├── app/
│   │   ├── main.py         # FastAPI app entry, CORS middleware
│   │   ├── config.py       # Settings (DATABASE_URL, GROQ_API_KEY)
│   │   ├── database.py     # SQLAlchemy engine, SessionLocal, Base
│   │   ├── models/         # ORM models (HCP, Interaction, Material, Sample)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── crud/           # Database operations (CRUD logic)
│   │   ├── routers/        # API route handlers
│   │   ├── agent/          # LangGraph agent (state, tools, graph)
│   │   └── seed.py         # Demo data seeder
│   ├── venv/               # Python virtual environment
│   ├── requirements.txt
│   └── .env / .env.example
│
├── frontend/         # React + Redux (Vite)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── ...             # Components, store, services
│   ├── .env                # VITE_API_URL=http://localhost:8000
│   └── package.json
│
└── docs/
    └── HLD.md              # High-level design documentation
```

## Tech Stack

- **Backend:** Python 3.9, FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Alembic
- **AI Agent:** LangGraph + LangChain + Groq (llama-3.3-70b-versatile)
- **Frontend:** React 19, Redux Toolkit, Axios, Vite 8
- **Font:** Google Inter

## Running the Project

```bash

# Start backend (port 8000)
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Start frontend (port 5173)
cd frontend && npm run dev
```

## Key Commands

```bash
# Backend
cd backend && source venv/bin/activate
pip install -r requirements.txt              # Install deps
python -m app.seed                           # Seed demo data
alembic upgrade head                         # Run migrations
alembic revision --autogenerate -m "msg"     # Create migration

# Frontend
cd frontend
npm install                                  # Install deps
npm run dev                                  # Dev server
npm run build                                # Production build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/hcps?search=` | Search HCPs by name |
| GET | `/api/hcps/{id}` | Get HCP detail |
| POST | `/api/interactions` | Create interaction |
| GET | `/api/interactions?hcp_id=` | List interactions |
| GET | `/api/interactions/{id}` | Get interaction detail |
| PUT | `/api/interactions/{id}` | Update interaction |
| DELETE | `/api/interactions/{id}` | Delete interaction |
| GET | `/api/materials?search=` | Search materials |
| GET | `/api/samples` | List samples |
| POST | `/api/chat` | AI chat endpoint |

## Important Constraints

- **Python 3.9** — use `Optional[X]` and `List[X]` from `typing`, not `X | None` or `list[X]`
- **CORS** — backend allows origins `localhost:5173` and `127.0.0.1:5173`
- **Database** — PostgreSQL on port 5432, creds: `hcp_user` / `hcp_pass` / `hcp_db`
- **No streaming** — chat endpoint uses synchronous LangGraph invocation

## Implementation Phases

1. **Project Scaffolding** — COMPLETED
2. **Database & Models** — Alembic setup, migrations, seed data
3. **Backend CRUD APIs** — Models/schemas/CRUD done early; needs Alembic + runtime testing
4. **LangGraph Agent** — 5 tools: log_interaction, edit_interaction, analyze_sentiment, suggest_followups, summarize_interaction
5. **Frontend Redux & API** — Store config, slices, API service layer
6. **Frontend UI** — Two-panel layout, form components, chat panel
7. **Integration & Polish** — Chat-to-form bridge, error handling, loading states
