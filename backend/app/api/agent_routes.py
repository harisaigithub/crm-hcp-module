from fastapi import APIRouter, HTTPException
from groq import BadRequestError, AuthenticationError, PermissionDeniedError, RateLimitError
from app.models.schemas import ChatMessage
from app.agent.agent import run_agent
from langchain_core.messages import HumanMessage, AIMessage as AssistantMessage

router = APIRouter()

chat_sessions: dict = {}


@router.post("/agent/chat")
def chat_with_agent(payload: ChatMessage):
    session_id = payload.session_id or "default"
    history = chat_sessions.get(session_id, [])

    try:
        response = run_agent(
            payload.message,
            history,
            payload.selected_hcp_id
        )

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="Groq API key is invalid or missing."
        ) from exc

    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=403,
            detail="Groq project does not have access to the selected model."
        ) from exc

    except RateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="Groq rate limit reached. Please retry after a short break."
        ) from exc

    except BadRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc

    chat_sessions[session_id] = history + [
        HumanMessage(content=payload.message),
        AssistantMessage(content=response)
    ]

    return {
        "response": response,
        "session_id": session_id
    }


@router.delete("/agent/chat/{session_id}")
def clear_session(session_id: str):
    chat_sessions.pop(session_id, None)

    return {
        "message": f"Session {session_id} cleared"
    }