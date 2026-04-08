# AI CRM Agent

An AI-powered CRM system designed for pharmaceutical field representatives to manage Healthcare Professionals (HCPs), log interactions, and automate workflows using conversational AI.

---

## Why This Project?

Traditional CRM systems rely heavily on manual data entry.

This system introduces a dual-input approach:
- Structured forms for precise data entry
- Conversational AI for faster, natural interaction logging

This improves efficiency, reduces friction, and demonstrates how AI agents can enhance real-world business workflows.

---

## Tech Stack

### Backend
- Python 3.9
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL

### AI Agent
- LangGraph
- LangChain
- Groq (llama-3.3-70b-versatile)

### Frontend
- React (Vite)
- Redux Toolkit
- Axios

---

## Core Features

- AI-powered chat interface for CRM interaction logging
- HCP (Healthcare Professional) management
- Interaction tracking with sentiment analysis
- Dual input system (form + chat)
- Modular agent architecture with tool-based execution

---

## Architecture Overview

The system follows a modular full-stack architecture:

- Backend: FastAPI with layered architecture (routers, schemas, models, CRUD)
- Agent Layer: LangGraph-based workflow with tool execution
- Database: PostgreSQL with Alembic migrations
- Frontend: React with Redux state management

For detailed design:
See docs/HLD.md

---

## Project Structure

hcp/
├── backend/
├── frontend/
└── docs/

---

## Running the Project

### Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

### Frontend
cd frontend
npm run dev

---

## API Highlights

- POST /api/chat → AI interaction
- POST /api/interactions → Log interaction
- GET /api/hcps → Search HCPs

---

## What This Project Demonstrates

- Full-stack system design
- Clean backend architecture
- API design and modularity
- AI agent integration in real applications
- Real-world CRM workflow implementation