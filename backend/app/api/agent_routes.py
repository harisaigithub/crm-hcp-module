from fastapi import APIRouter
from app.models.schemas import ChatMessage
from app.agent.agent import run_agent

router = APIRouter()

chat_sessions: dict = {}

@router.post("/agent/chat")
def chat_with_agent(payload: ChatMessage):
    session_id = payload.session_id or "default"
    history = chat_sessions.get(session_id, [])
    
    response = run_agent(payload.message, history)
    
    from langchain_core.messages import HumanMessage, AIMessage
    chat_sessions[session_id] = history + [
        HumanMessage(content=payload.message),
        AIMessage(content=response)
    ]
    
    return {"response": response, "session_id": session_id}

@router.delete("/agent/chat/{session_id}")
def clear_session(session_id: str):
    chat_sessions.pop(session_id, None)
    return {"message": f"Session {session_id} cleared"}
