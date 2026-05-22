# HCP CRM Process and Data Flow Guide

## 1. What The System Does

This module helps a life science field representative manage interactions with Healthcare Professionals (HCPs).

The rep can:

- Register a new HCP.
- Select an existing HCP.
- Log an interaction using a structured form.
- Use chat to ask the LangGraph agent to log, edit, summarize, schedule follow-ups, or review sentiment.
- See recent interaction history for the selected HCP.

## 2. Main User Flow

### Step 1: Open The App

The frontend runs at:

```text
http://localhost:5173
```

or another Vite port such as:

```text
http://localhost:5174
```

The frontend calls the FastAPI backend at:

```text
http://127.0.0.1:8000/api
```

### Step 2: Load HCP List

When the app opens, it calls:

```text
GET /api/hcps
```

The backend reads the `hcps` table and returns all doctors. The frontend stores them in Redux.

If there is at least one HCP, the first HCP is selected automatically. This is intentional so the screen is useful immediately during a demo.

### Step 3: Register A New HCP

Click **Register HCP** in the sidebar.

Fill:

- Name
- Specialty
- Hospital
- Email
- Phone
- Territory

When saved, the frontend calls:

```text
POST /api/hcps
```

The backend inserts the HCP into the `hcps` table. The frontend then selects the new HCP automatically and clears the interaction history panel.

### Step 4: Log Interaction By Form

With an HCP selected, the rep fills:

- Interaction type
- Products discussed
- Notes
- Follow-up date
- Logged by
- Follow-up note

When saved, the frontend calls:

```text
POST /api/interactions
```

The backend stores the interaction in the `interactions` table with the selected `hcp_id`.

### Step 5: View Recent History

Whenever an HCP is selected, the frontend calls:

```text
GET /api/interactions?hcp_id={selectedHcpId}
```

The backend returns interactions for that HCP only. The frontend shows them in the Recent History panel.

### Step 6: Use Chat Agent

In chat mode, the frontend calls:

```text
POST /api/agent/chat
```

The backend sends the message to the LangGraph agent. The agent can decide whether to call one of the tools:

- `log_interaction`
- `edit_interaction`
- `get_hcp_profile`
- `schedule_followup`
- `analyze_sentiment`

The selected Groq model is configured in `.env`:

```env
GROQ_MODEL=llama-3.3-70b-versatile
```

## 3. Data Flow

```text
React UI
  -> Redux action
  -> API service fetch()
  -> FastAPI route
  -> SQLAlchemy session
  -> PostgreSQL table
  -> FastAPI JSON response
  -> Redux state update
  -> UI refresh
```

For chat:

```text
React chat input
  -> POST /api/agent/chat
  -> LangGraph agent
  -> Groq model
  -> Tool call if needed
  -> Database read/write
  -> Final assistant response
  -> Chat UI
```

## 4. Database Tables

### `hcps`

Stores doctor profile information:

- `id`
- `name`
- `specialty`
- `hospital`
- `email`
- `phone`
- `territory`
- `created_at`

### `interactions`

Stores each field interaction:

- `id`
- `hcp_id`
- `interaction_type`
- `date`
- `notes`
- `summary`
- `products_discussed`
- `sentiment`
- `followup_date`
- `followup_notes`
- `logged_by`
- `created_at`
- `updated_at`

## 5. Demo Flow

Use this order in the video:

1. Show the HCP list.
2. Collapse and expand the sidebar.
3. Register a new HCP.
4. Select that HCP.
5. Log an interaction using the structured form.
6. Show the Recent History update.
7. Switch to chat mode.
8. Ask the agent to get the HCP profile.
9. Ask the agent to analyze sentiment.
10. Ask the agent to schedule a follow-up.

## 6. Important Notes

- The first HCP is selected automatically only for convenience.
- New HCP registration is handled from the sidebar.
- Structured form logging works without calling Groq.
- Chat mode requires a valid Groq API key.
- If Groq changes models again, update `GROQ_MODEL` in `backend/.env`.
