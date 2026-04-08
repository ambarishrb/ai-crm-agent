# High-Level Design: AI-First CRM HCP Module - Log Interaction Screen

## 1. Overview

An AI-first CRM module for pharmaceutical field representatives to log interactions with Healthcare Professionals (HCPs). The system provides a dual-input interface: a **structured form** and a **conversational AI chat** powered by LangGraph + Groq LLMs. The AI chat can automatically parse natural language descriptions and populate the structured form.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Redux (Vite) |
| Backend | Python + FastAPI |
| AI Agent | LangGraph + LangChain |
| LLM Provider | Groq (llama-3.1-8b-instant, llama-3.3-70b-versatile) |
| Database | PostgreSQL |
| Font | Google Inter |

---

## 2. Architecture Diagram

```
+------------------------------------------------------------------+
|                        Frontend (React + Redux)                   |
|                                                                    |
|  +---------------------------+  +------------------------------+  |
|  |   InteractionForm (Left)  |  |    ChatPanel (Right)         |  |
|  |                           |  |                              |  |
|  |  HCP Name [search]        |  |  [AI Assistant header]       |  |
|  |  Interaction Type [select] |  |                              |  |
|  |  Date / Time              |  |  +------------------------+  |  |
|  |  Attendees                |  |  | Chat messages area     |  |  |
|  |  Topics Discussed         |  |  | (scrollable)           |  |  |
|  |  [Summarize Voice Note]   |  |  |                        |  |  |
|  |  Materials Shared         |  |  +------------------------+  |  |
|  |  Samples Distributed      |  |                              |  |
|  |  Sentiment (radio)        |  |  [input] [Log button]        |  |
|  |  Outcomes                 |  +------------------------------+  |
|  |  Follow-up Actions        |          |                         |
|  |  AI Suggested Follow-ups  |          | POST /api/chat          |
|  |  [Submit]                 |          |                         |
|  +---------------------------+          v                         |
|              |                 +------------------+               |
|              | form_updates    |  Redux Store     |               |
|              |<----------------|  (single source  |               |
|              |                 |   of truth)      |               |
+--------------|-----------------+------------------+---------------+
               |                          |
               | POST /api/interactions   | POST /api/chat
               v                          v
+------------------------------------------------------------------+
|                     Backend (FastAPI)                              |
|                                                                    |
|  +----------------+  +----------------+  +---------------------+  |
|  | REST Routers   |  | Chat Router    |  | LangGraph Agent     |  |
|  |                |  |                |  |                     |  |
|  | /api/hcps      |  | /api/chat ---->|  | StateGraph (ReAct)  |  |
|  | /api/interactions| |               |  |                     |  |
|  | /api/materials  | |               |  | route_intent         |  |
|  | /api/samples   |  |                |  |   |                 |  |
|  +-------+--------+  +----------------+  |   v                 |  |
|          |                               | tool_node            |  |
|          |                               |   |                 |  |
|          |                               |   v                 |  |
|          |                               | summarize_response  |  |
|          |                               +---------------------+  |
|          |                                        |               |
|          v                                        v               |
|  +------------------------------------------------------------+  |
|  |                    SQLAlchemy ORM                            |  |
|  +------------------------------------------------------------+  |
|          |                                                        |
+----------|--------------------------------------------------------+
           v
  +------------------+
  |   PostgreSQL     |
  |                  |
  | hcps             |
  | interactions     |
  | materials        |
  | samples          |
  | interaction_*    |
  +------------------+
```

---

## 3. Database Schema

### 3.1 Entity Relationship

```
hcps 1---* interactions *---* materials
                        *---* samples
```

### 3.2 Table Definitions

#### `hcps`
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK, auto-generated |
| full_name | VARCHAR(200) | NOT NULL |
| specialty | VARCHAR(100) | e.g. "Cardiology" |
| organization | VARCHAR(200) | Hospital/clinic |
| email | VARCHAR(200) | |
| phone | VARCHAR(50) | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

#### `interactions`
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK, auto-generated |
| hcp_id | UUID | FK -> hcps.id |
| interaction_type | VARCHAR(50) | "Meeting" / "Call" / "Email" / "Conference" |
| interaction_date | DATE | |
| interaction_time | TIME | |
| attendees | TEXT | |
| topics_discussed | TEXT | |
| sentiment | VARCHAR(20) | "Positive" / "Neutral" / "Negative" |
| outcomes | TEXT | |
| follow_up_actions | TEXT | |
| ai_suggested_followups | JSONB | Array of suggestion strings |
| ai_summary | TEXT | LLM-generated summary |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

#### `materials`
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK |
| name | VARCHAR(200) | NOT NULL |
| material_type | VARCHAR(100) | "Brochure" / "Study Report" / etc. |
| created_at | TIMESTAMPTZ | DEFAULT now() |

#### `interaction_materials` (join table)
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK |
| interaction_id | UUID | FK -> interactions.id |
| material_id | UUID | FK -> materials.id |

#### `samples`
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK |
| product_name | VARCHAR(200) | NOT NULL |
| dosage | VARCHAR(100) | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

#### `interaction_samples` (join table)
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK |
| interaction_id | UUID | FK -> interactions.id |
| sample_id | UUID | FK -> samples.id |
| quantity | INTEGER | DEFAULT 1 |

---

## 4. API Design

### 4.1 REST Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|-------------|----------|
| GET | `/api/hcps?search={query}` | Search HCPs by name | - | `[{id, full_name, specialty, organization}]` |
| GET | `/api/hcps/{id}` | Get HCP details | - | `{id, full_name, specialty, ...}` |
| POST | `/api/interactions` | Create interaction | Interaction payload | `{id, ...created interaction}` |
| GET | `/api/interactions?hcp_id={id}` | List interactions | - | `[{id, hcp, interaction_type, ...}]` |
| GET | `/api/interactions/{id}` | Get interaction detail | - | `{id, ...with materials & samples}` |
| PUT | `/api/interactions/{id}` | Update interaction | Partial update payload | `{id, ...updated interaction}` |
| DELETE | `/api/interactions/{id}` | Delete interaction | - | `204 No Content` |
| GET | `/api/materials?search={query}` | Search materials | - | `[{id, name, material_type}]` |
| GET | `/api/samples` | List available samples | - | `[{id, product_name, dosage}]` |

### 4.2 Chat Endpoint

**`POST /api/chat`**

```json
// Request
{
  "message": "Met Dr. Smith today, discussed Product X efficacy, positive sentiment",
  "current_form_state": {
    "hcp_name": "",
    "interaction_type": "Meeting",
    "date": "2025-04-19",
    ...
  },
  "interaction_id": null  // set if editing an existing interaction
}

// Response
{
  "reply": "I've logged your interaction with Dr. Smith. The sentiment was positive...",
  "form_updates": {
    "hcp": {"id": "uuid", "name": "Dr. Smith"},
    "topics_discussed": "Discussed Product X efficacy",
    "sentiment": "Positive",
    "ai_suggested_followups": [
      "Schedule follow-up meeting in 2 weeks",
      "Send Phase III trial results"
    ]
  },
  "tool_used": "log_interaction",
  "interaction_id": "uuid-of-saved-interaction"
}
```

---

## 5. LangGraph Agent Design

### 5.1 Agent State

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Conversation history
    form_data: dict                           # Current form state from frontend
    interaction_id: Optional[str]             # Active interaction ID
```

### 5.2 Graph Topology (ReAct Pattern)

```
         +-------+
         | START |
         +---+---+
             |
             v
     +-------+--------+
     |  route_intent   |  <-- LLM decides which tool to call
     |  (ChatGroq +    |      based on user message
     |   bound tools)  |
     +---+--------+----+
         |        |
    tool call   no tool
         |        |
         v        v
   +-----+----+  +----------+
   | tool_node|  | direct    |
   | (execute |  | response  |
   |  tool)   |  +-----+----+
   +-----+----+        |
         |              |
         v              |
   +-----+----------+  |
   | summarize_resp  |  |
   | (format reply + |  |
   |  form_updates)  |  |
   +-----+-----------+  |
         |              |
         v              v
      +--+---+     +---+--+
      | END  |     | END  |
      +------+     +------+
```

### 5.3 LangGraph Tools (5 Total)

#### Tool 1: `log_interaction` (Mandatory)
- **Purpose:** Parse natural language into structured interaction data
- **Process:**
  1. Receive user's free-text description
  2. Call LLM with extraction prompt -> JSON of structured fields
  3. Fuzzy-match HCP name against `hcps` table
  4. Insert into `interactions` table with resolved references
  5. Auto-trigger `analyze_sentiment` and `suggest_followups`
- **Returns:** `{interaction_id, extracted_fields, confirmation_message}`

#### Tool 2: `edit_interaction` (Mandatory)
- **Purpose:** Modify fields of an existing interaction
- **Process:**
  1. Receive edit instruction (e.g., "change sentiment to negative")
  2. LLM parses into `{field: new_value}` dict
  3. SQL UPDATE on the interaction record
- **Returns:** `{updated_fields, confirmation_message}`

#### Tool 3: `analyze_sentiment`
- **Purpose:** Infer HCP sentiment from interaction text
- **Process:**
  1. Take topics_discussed + outcomes text
  2. LLM classifies as Positive/Neutral/Negative with rationale
- **Returns:** `{sentiment, rationale}`

#### Tool 4: `suggest_followups`
- **Purpose:** Generate actionable follow-up suggestions
- **Process:**
  1. Take full interaction context (HCP specialty, topics, sentiment, outcomes)
  2. LLM generates 3 specific follow-up actions with timeframes
- **Returns:** `{suggestions: ["Schedule follow-up in 2 weeks", ...]}`

#### Tool 5: `summarize_interaction`
- **Purpose:** Generate a concise, structured summary of the logged interaction for call reports
- **Process:**
  1. Take the full interaction data (HCP name, topics, outcomes, sentiment, materials, samples)
  2. LLM generates a professional summary suitable for CRM records and manager review
  3. Stores the summary in the `ai_summary` field of the interaction
- **Returns:** `{summary: "Brief professional summary text...", key_points: [...]}`

### 5.4 LLM Configuration

| Setting | Value |
|---------|-------|
| Primary Model | llama-3.3-70b-versatile via Groq |
| Secondary Model | llama-3.1-8b-instant via Groq |
| Temperature (extraction) | 0.1 |
| Temperature (conversation) | 0.7 |
| Tool binding | ChatGroq.bind_tools([...]) |

---

## 6. Frontend Architecture

### 6.1 Component Hierarchy

```
App
└── LogInteraction                    # Main page, two-panel flexbox
    ├── InteractionForm               # Left panel (~60% width)
    │   ├── HcpSearch                 # Autocomplete search input
    │   ├── <select>                  # Interaction Type dropdown
    │   ├── <input type="date">       # Date picker
    │   ├── <input type="time">       # Time picker
    │   ├── <input>                   # Attendees
    │   ├── <textarea>               # Topics Discussed
    │   ├── <button>                  # Summarize from Voice Note
    │   ├── MaterialSearch            # Search + add materials as chips
    │   ├── SampleAdd                 # Dropdown + quantity + add
    │   ├── SentimentRadio            # Positive / Neutral / Negative
    │   ├── <textarea>               # Outcomes
    │   ├── <textarea>               # Follow-up Actions
    │   ├── FollowUpLinks            # AI suggestions as clickable links
    │   └── <button>                  # Submit
    │
    └── ChatPanel                     # Right panel (~40% width)
        ├── ChatHeader                # "AI Assistant" title
        ├── MessageList               # Scrollable message area
        │   └── ChatMessage           # Individual chat bubble
        └── ChatInput                 # Text input + Log button
```

### 6.2 Redux Store

```javascript
// store/index.js
{
  interaction: {           // interactionSlice
    hcp: { id, name },
    interactionType: "Meeting",
    date: "",
    time: "",
    attendees: "",
    topicsDiscussed: "",
    materialsShared: [],
    samplesDistributed: [],
    sentiment: "Neutral",
    outcomes: "",
    followUpActions: "",
    aiSuggestedFollowups: [],
    isSubmitting: false,
    savedInteractionId: null
  },
  chat: {                  // chatSlice
    messages: [{ role, content }],
    isLoading: false
  }
}
```

### 6.3 Key Data Flow: Chat-to-Form Bridge

```
User types in ChatPanel
        |
        v
dispatch(sendMessage(text))     // async thunk
        |
        v
POST /api/chat                  // sends message + current form state
        |
        v
LangGraph processes, calls tool
        |
        v
Response: { reply, form_updates }
        |
        +---> dispatch(addMessage(reply))           // update chat
        |
        +---> dispatch(setMultipleFields(form_updates))  // update form
                    |
                    v
              InteractionForm re-renders with AI-filled values
```

---

## 7. Project Structure (Separate Repos / Folders)

The frontend and backend live in **separate top-level folders**, each with their own dependency management. They run as independent processes on different ports.

```
hcp/
├── docs/
│   └── HLD.md
├── .gitignore
│
├── backend/                        # Standalone Python project
│   ├── .env                        # DATABASE_URL, GROQ_API_KEY
│   ├── .env.example
│   ├── requirements.txt
│   ├── database_setup.md          # Instruction for local PostgreSQL setup
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app + CORS middleware
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── hcp.py
│   │   │   ├── interaction.py
│   │   │   ├── material.py
│   │   │   └── sample.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── hcp.py
│   │   │   ├── interaction.py
│   │   │   └── chat.py
│   │   ├── crud/
│   │   │   ├── __init__.py
│   │   │   ├── hcp.py
│   │   │   └── interaction.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── hcp.py
│   │   │   ├── interaction.py
│   │   │   ├── chat.py
│   │   │   └── materials.py
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── state.py
│   │   │   ├── tools.py
│   │   │   └── graph.py
│   │   └── seed.py
│   └── tests/
│
├── frontend/                       # Standalone React project
│   ├── .env                        # VITE_API_URL=http://localhost:8000
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       ├── store/
│       │   ├── index.js
│       │   ├── interactionSlice.js
│       │   └── chatSlice.js
│       ├── components/
│       │   ├── LogInteraction.jsx
│       │   ├── InteractionForm.jsx
│       │   ├── ChatPanel.jsx
│       │   ├── ChatMessage.jsx
│       │   ├── HcpSearch.jsx
│       │   ├── MaterialSearch.jsx
│       │   ├── SampleAdd.jsx
│       │   ├── SentimentRadio.jsx
│       │   └── FollowUpLinks.jsx
│       └── services/
│           └── api.js              # Uses VITE_API_URL for base URL
```

---

## 8. Cross-Origin Communication (CORS)

Since the frontend (Vite on `:5173`) and backend (Uvicorn on `:8000`) run on **different ports**, the browser will block cross-origin requests by default. We handle this with **FastAPI's CORSMiddleware** on the backend side.

### Backend: `app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",     # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],             # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],             # Authorization, Content-Type, etc.
)
```

### Frontend: `services/api.js`

The frontend uses an environment variable for the backend URL, so it can point to different backends in dev vs production.

```javascript
// frontend/.env
VITE_API_URL=http://localhost:8000

// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});
```

### How to Run (Two Terminals)

```bash
# Terminal 1 — Backend (port 8000)
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend (port 5173)
cd frontend
npm run dev
```

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single `/api/chat` endpoint (not per-tool) | The LangGraph agent decides which tool to call based on user intent. Frontend stays simple. |
| `form_updates` in chat response | Structured data bridge between AI chat and form. Frontend doesn't need to parse AI text. |
| Factory pattern for LangGraph tools | Tools need DB access. Factory receives session per request, preventing connection leaks. |
| Synchronous graph invocation (not streaming) | Simpler to implement and demo for this scope. Streaming can be added later. |
| Redux as single source of truth | Both manual form edits and AI chat updates write to the same store, preventing conflicts. |
| `setMultipleFields` reducer | Batch-applies AI-extracted fields without clearing manually-entered ones. |
| Separate folders, CORS middleware | Frontend and backend are independently deployable. CORS on the backend allows cross-origin calls from Vite dev server. `VITE_API_URL` env var makes the backend URL configurable. |

---

## 10. Seed Data

Pre-populated data for demo purposes:

**HCPs:** Dr. Smith (Cardiology), Dr. Sharma (Oncology), Dr. Patel (Neurology), Dr. Johnson (Endocrinology), Dr. Williams (Pulmonology), Dr. Brown (Dermatology), Dr. Davis (Pediatrics), Dr. Wilson (Gastroenterology)

**Materials:** Product X Brochure, Phase III Trial Results, Dosing Guide, Patient Education Kit, Clinical Study Report, Safety Profile Sheet

**Samples:** Product X 10mg, Product X 25mg, Product Y 50mg, Product Z 100mg, Product W 5mg

---

## 11. Implementation Phases

### Phase 1: Project Scaffolding --- COMPLETED

| Task | Details | Status |
|------|---------|--------|
| Initialize git repo | `.gitignore` for Python + Node | Done |
| Backend scaffold | `backend/` folder, `requirements.txt` (fastapi, uvicorn, sqlalchemy, psycopg2-binary, alembic, pydantic-settings, langchain-groq, langgraph, langchain-core, python-dotenv), FastAPI app skeleton with CORS middleware | Done |
| Frontend scaffold | `frontend/` folder via `npm create vite@latest -- --template react`, install `@reduxjs/toolkit`, `react-redux`, `axios` | Done |
| Environment files | `backend/.env.example` (DATABASE_URL, GROQ_API_KEY), `frontend/.env` (VITE_API_URL) | Done |
| Database Setup | Local PostgreSQL configured on port 5432 | Done |

**Exit criteria:** Both servers start without errors. Frontend can make a test request to backend without CORS issues.

**Implementation notes:**
- Python 3.9 environment — uses `Optional[X]` instead of `X | None` syntax throughout
- Backend venv created at `backend/venv/` with all dependencies installed
- FastAPI health endpoint verified: `GET /api/health` returns `200 OK`
- Chat endpoint returns placeholder response (LangGraph agent wired in Phase 4)
- SQLAlchemy models, Pydantic schemas, CRUD functions, and REST routers all implemented ahead of schedule (originally Phase 2-3 scope) — pending DB connection for runtime testing
- Alembic setup deferred to Phase 2 (requires running PostgreSQL)

---

### Phase 2: Database & Models --- COMPLETED

| Task | Details | Status |
|------|---------|--------|
| SQLAlchemy models | `hcp.py`, `interaction.py`, `material.py`, `sample.py` — all 6 tables | Done (Phase 1) |
| Database config | `database.py` with engine, SessionLocal, Base | Done (Phase 1) |
| Alembic setup | `alembic init`, configure `env.py`, generate initial migration | Done |
| Run migration | `alembic upgrade head` — tables created in PostgreSQL | Done |
| Seed script | `seed.py` — populate 8 HCPs, 6 materials, 5 samples | Done |

**Exit criteria:** PostgreSQL server running locally and accessible via DATABASE_URL

**Implementation notes:**
- Alembic `env.py` reads `DATABASE_URL` from `app.config.settings` (no hardcoded URL in `alembic.ini`)
- Initial migration auto-detected all 6 tables: `hcps`, `interactions`, `materials`, `samples`, `interaction_materials`, `interaction_samples`
- Seed data verified: 8 HCPs, 6 materials, 5 samples successfully inserted

---

### Phase 3: Backend CRUD APIs --- COMPLETED

| Task | Details | Status |
|------|---------|--------|
| Pydantic schemas | Request/response models for HCP, Interaction, Material, Sample, Chat | Done (Phase 1) |
| CRUD functions | `crud/hcp.py` (search, get), `crud/interaction.py` (create, get, list, update, delete with material/sample joins) | Done (Phase 1) |
| REST routers | `GET /api/hcps`, `POST/GET/PUT/DELETE /api/interactions`, `GET /api/materials`, `GET /api/samples` | Done (Phase 1) |
| Wire routers | Register all routers in `main.py` | Done (Phase 1) |

**Exit criteria:** All endpoints testable via FastAPI Swagger UI (`http://localhost:8000/docs`). CRUD operations work with seed data.

**Implementation notes:**
- All 14 endpoint tests passed against live PostgreSQL with seed data
- Full CRUD lifecycle verified: create interaction with materials/samples, read, update, delete
- HCP search (ilike), material search, sample listing all functional
- Chat endpoint returns placeholder (LangGraph agent wired in Phase 4)

---

### Phase 4: LangGraph Agent (Critical Path) --- COMPLETED

| Task | Details | Status |
|------|---------|--------|
| Agent state | `agent/state.py` — `AgentState` TypedDict with messages, form_data, interaction_id | Done |
| Tool 1: `log_interaction` | Parse natural language -> extract structured fields -> fuzzy-match HCP -> insert interaction -> return form_updates | Done |
| Tool 2: `edit_interaction` | Parse edit instruction -> identify fields to update -> SQL UPDATE -> return updated fields | Done |
| Tool 3: `analyze_sentiment` | Take interaction text -> LLM classifies Positive/Neutral/Negative with rationale | Done |
| Tool 4: `suggest_followups` | Take interaction context -> LLM generates 3 actionable follow-ups with timeframes | Done |
| Tool 5: `summarize_interaction` | Take full interaction data -> LLM generates professional summary for call reports -> store in ai_summary | Done |
| Graph definition | `agent/graph.py` — StateGraph with ReAct pattern (route_intent -> tool_node -> summarize_response) | Done |
| Chat endpoint | `POST /api/chat` — instantiate graph, invoke with user message + form state, return `{reply, form_updates, tool_used}` | Done |

**Exit criteria:** Each tool triggers correctly via `/api/chat`. Test messages:
- `"Met Dr. Smith today about Product X, positive sentiment"` -> log_interaction
- `"Change sentiment to negative"` -> edit_interaction
- `"Analyze the sentiment of this interaction"` -> analyze_sentiment
- `"Suggest follow-ups"` -> suggest_followups
- `"Summarize this interaction"` -> summarize_interaction

**Implementation notes:**
- Tools are initialized with a database session to perform CRUD operations
- Primary model: `llama-3.3-70b-versatile` for intent routing (with tool binding), `llama-3.1-8b-instant` for extraction/summarization
- Fuzzy HCP matching: case-insensitive partial match with "Dr." prefix stripping
- Graph topology: `route_intent` -> conditional edge (tool call vs direct response) -> `tools` (ToolNode) -> `summarize_response` -> END
- All 5 tools tested and verified via `/api/chat` with correct form_updates returned

---

### Phase 5: Frontend — Redux Store & API Layer --- COMPLETED

| Task | Details | Status |
|------|---------|--------|
| Store config | `store/index.js` with `configureStore` | Done |
| Interaction slice | `interactionSlice.js` — all form fields, `setField`, `setMultipleFields`, `resetForm`, `addMaterial`, `removeMaterial`, `addSample`, `removeSample` reducers + `submitInteraction` async thunk | Done |
| Chat slice | `chatSlice.js` — messages array, `isLoading`, `sendMessage` async thunk with chat-to-form bridge | Done |
| API service | `services/api.js` — axios instance with `VITE_API_URL`, functions for `searchHcps()`, `createInteraction()`, `searchMaterials()`, `getSamples()`, `sendChatMessage()` | Done |

**Exit criteria:** Redux DevTools shows correct state shape. `sendMessage` thunk successfully calls backend and updates both slices.

**Implementation notes:**
- Chat-to-form bridge built into `sendMessage` thunk: dispatches `setMultipleFields(response.form_updates)` automatically
- `savedInteractionId` tracked in interaction slice and passed to chat endpoint for edit/analyze/suggest/summarize tools
- Frontend builds clean with 82 modules, no errors

---

### Phase 6: Frontend — UI Components --- COMPLETED

| Task | Details | Status |
|------|---------|--------|
| Global styles | `index.css` — Google Inter font import, CSS variables (blue `#1a73e8`, red for Log button, grey borders) | Done |
| LogInteraction | Main two-panel layout (flexbox, left 60% / right 40%) | Done |
| InteractionForm | Left panel — all form fields bound to `interactionSlice`, Submit button calls `createInteraction()` | Done |
| HcpSearch | Debounced autocomplete input, calls `GET /api/hcps?search=`, dropdown results | Done |
| MaterialSearch | Search input + chips for added materials with remove | Done |
| SampleAdd | Dropdown of products + quantity input + Add button, list of added samples | Done |
| SentimentRadio | Three radio buttons (Positive / Neutral / Negative) with emoji icons | Done |
| FollowUpLinks | Renders `aiSuggestedFollowups` as blue `+` prefixed clickable links | Done |
| ChatPanel | Right panel — message area (scrollable), input bar with text field + red "Log" button | Done |
| ChatMessage | Single message bubble — left-aligned grey (assistant), right-aligned blue (user) | Done |

**Exit criteria:** UI matches the mockup. All form fields render and are editable. Chat panel sends/receives messages.

**Implementation notes:**
- 10 components total matching the HLD component hierarchy
- Chat-to-form bridge fully wired: AI responses auto-populate form fields
- Loading animation (bouncing dots) shows while AI processes
- Welcome message in chat panel matches mockup text
- Build clean: 88 modules, no errors

---

### Phase 7: Integration & Polish --- COMPLETED

| Task | Details | Status |
|------|---------|--------|
| Chat-to-form bridge | `sendMessage` thunk dispatches `setMultipleFields(response.form_updates)` after receiving AI response | Done (Phase 5) |
| Auto-chaining | After `log_interaction`, automatically trigger `analyze_sentiment` + `suggest_followups` in the graph | Done |
| Error handling | Try/catch on chat router, user-friendly error messages, frontend error states | Done |
| Loading states | Bouncing dots in chat while AI processes, disable Submit while saving | Done (Phase 6) |
| Draggable chat panel | Resizable divider between form and chat panels (25%-60% range) | Done |
| End-to-end test | Full walkthrough: log via chat -> auto sentiment + followups -> edit -> summarize -> direct conversation | Done |

**Exit criteria:** All 5 LangGraph tools demo correctly through the chat UI. Form and chat stay in sync. Ready for video recording.

**Implementation notes:**
- Auto-chaining: `invoke_agent` directly calls `analyze_sentiment` and `suggest_followups` tools after `log_interaction`, merging all `form_updates` into a single response
- Error handling: chat router wraps agent invocation in try/except, returns user-friendly error with exception type
- Draggable panel: mouse-drag divider between form and chat, clamped to 25%-60% chat width
- E2E verified: log (with auto-chain) -> edit -> summarize -> direct conversation all work correctly
