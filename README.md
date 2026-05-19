# AI-First CRM – HCP Module

An AI-powered CRM system for Healthcare Professionals (HCPs), built for life science field representatives.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Redux + Google Inter |
| Backend | Python + FastAPI |
| AI Agent | LangGraph + Groq (gemma2-9b-it) |
| Database | PostgreSQL |

## Features

- **Log Interaction Screen** — Dual-mode: Structured Form OR Conversational Chat
- **LangGraph Agent** with 5 sales tools:
  1. `log_interaction` — Captures & summarizes HCP interactions via LLM
  2. `edit_interaction` — Modifies existing interaction records
  3. `get_hcp_profile` — Fetches HCP history and details
  4. `schedule_followup` — Creates follow-up reminders
  5. `sentiment_analysis` — Analyzes tone of interaction notes

## Project Structure

```
crm-hcp-module/
├── frontend/         # React + Redux app
│   ├── src/
│   │   ├── components/
│   │   ├── store/
│   │   └── pages/
│   └── package.json
├── backend/          # FastAPI + LangGraph
│   ├── app/
│   │   ├── api/
│   │   ├── agent/
│   │   ├── models/
│   │   └── db/
│   ├── requirements.txt
│   └── main.py
└── README.md
```

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL
- Groq API Key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your GROQ_API_KEY and DATABASE_URL

uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Environment Variables

**backend/.env**
```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/crm_hcp
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hcps` | List all HCPs |
| GET | `/api/hcps/{id}` | Get HCP profile |
| POST | `/api/interactions` | Log new interaction |
| PATCH | `/api/interactions/{id}` | Edit interaction |
| POST | `/api/agent/chat` | Chat with LangGraph agent |

## License
MIT
