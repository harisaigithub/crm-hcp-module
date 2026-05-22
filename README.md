# HCP CRM Module

A focused CRM module for Healthcare Professional (HCP) interaction logging, built for life science field representatives.

## Assignment Focus

The main screen is the **Log Interaction Screen**. It supports two everyday workflows for a field rep:

- **Structured form mode** for fast, clean interaction logging.
- **Conversational chat mode** for logging, editing, follow-ups, profile lookup, and sentiment review through a LangGraph agent.

The backend uses FastAPI, PostgreSQL, LangGraph, and Groq's `llama-3.3-70b-versatile` model. The frontend uses React, Redux Toolkit, Vite, and the Google Inter font.

## Key Features

- Dual interaction logging modes: structured form and conversational AI chat
- LangGraph-powered CRM copilot with 5 domain-specific tools
- AI-generated interaction summarization and sentiment detection
- Follow-up scheduling and interaction editing
- Redux-based frontend state management
- PostgreSQL relational persistence
- Context-aware conversational workflow

## Agent Tools

The conversational workflow is orchestrated through a LangGraph StateGraph with tool-routing and conditional execution.


The LangGraph agent exposes five sales-focused tools:

1. `log_interaction` - logs a new HCP interaction, creates a concise summary, and detects sentiment.
2. `edit_interaction` - updates an existing interaction and refreshes the summary when notes change.
3. `get_hcp_profile` - retrieves HCP details and recent interaction history.
4. `schedule_followup` - adds a follow-up date and note to an interaction.
5. `analyze_sentiment` - reviews interaction tone and recommends a next step.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Redux Toolkit, Vite, Google Inter |
| Backend | Python, FastAPI |
| Agent | LangGraph, LangChain, Groq `llama-3.3-70b-versatile` |
| Database | PostgreSQL |

## Project Structure

```text
crm-hcp-module/
|-- frontend/
|   |-- src/
|   |   |-- features/
|   |   |-- services/
|   |   |-- App.jsx
|   |   |-- main.jsx
|   |   |-- store.js
|   |   `-- styles.css
|   |-- .env.example
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- backend/
|   |-- app/
|   |   |-- agent/
|   |   |-- api/
|   |   |-- db/
|   |   `-- models/
|   |-- .env.example
|   |-- requirements.txt
|   |-- seed.py
|   `-- main.py
`-- README.md
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL
- Groq API key

## Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Update `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres@localhost:5432/crm_hcp
```

Create tables and seed sample HCPs:

```bash
cd backend
"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D ".pgdata" -l ".pgdata\server.log" start
python seed.py
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

To point the frontend at another API URL, create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/hcps` | List all HCPs |
| GET | `/api/hcps/{id}` | Get one HCP profile |
| POST | `/api/hcps` | Create an HCP |
| GET | `/api/interactions` | List interactions, optionally filtered by `hcp_id` |
| POST | `/api/interactions` | Log a new interaction |
| PATCH | `/api/interactions/{id}` | Edit an interaction |
| DELETE | `/api/interactions/{id}` | Delete an interaction |
| POST | `/api/agent/chat` | Chat with the LangGraph agent |
| DELETE | `/api/agent/chat/{session_id}` | Clear a chat session |

## Screenshots

### Log Interaction Screen

### Conversational AI Agent

