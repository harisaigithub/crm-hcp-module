from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from typing import TypedDict, List, Annotated
import operator
import json
from datetime import datetime
from app.config import settings
from app.db.database import SessionLocal
from app.models.models import HCP, Interaction, SentimentType, InteractionType

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="gemma2-9b-it",
    temperature=0.2,
)

# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    tool_output: str

# ── Tool 1: Log Interaction ───────────────────────────────────────────────────
@tool
def log_interaction(
    hcp_id: int,
    notes: str,
    interaction_type: str = "visit",
    products_discussed: str = "",
    logged_by: str = "Field Rep",
    followup_date: str = None
) -> str:
    """Log a new interaction with an HCP. Uses LLM to generate a summary and detect sentiment."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return f"Error: HCP with id {hcp_id} not found."

        # LLM summarization + sentiment
        prompt = f"""You are a CRM assistant for life sciences. Analyze this HCP interaction note and return JSON only.
Notes: {notes}
Products discussed: {products_discussed}

Return ONLY this JSON (no markdown):
{{"summary": "2-3 sentence summary", "sentiment": "positive|neutral|negative"}}"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        try:
            result = json.loads(response.content.strip())
            summary = result.get("summary", notes[:200])
            sentiment = result.get("sentiment", "neutral")
        except:
            summary = notes[:200]
            sentiment = "neutral"

        interaction = Interaction(
            hcp_id=hcp_id,
            interaction_type=interaction_type,
            notes=notes,
            summary=summary,
            products_discussed=products_discussed,
            sentiment=SentimentType(sentiment),
            logged_by=logged_by,
            followup_date=datetime.fromisoformat(followup_date) if followup_date else None,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return f"✅ Interaction logged (ID: {interaction.id}) for {hcp.name}. Summary: {summary}. Sentiment: {sentiment}."
    finally:
        db.close()

# ── Tool 2: Edit Interaction ──────────────────────────────────────────────────
@tool
def edit_interaction(
    interaction_id: int,
    notes: str = None,
    interaction_type: str = None,
    products_discussed: str = None,
    followup_date: str = None,
    followup_notes: str = None
) -> str:
    """Edit an existing logged interaction by ID. Re-runs LLM summary if notes are updated."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return f"Error: Interaction {interaction_id} not found."

        if notes:
            interaction.notes = notes
            # Re-summarize
            prompt = f"""Summarize this updated HCP interaction note in 2-3 sentences. Notes: {notes}
Return ONLY JSON: {{"summary": "...", "sentiment": "positive|neutral|negative"}}"""
            response = llm.invoke([HumanMessage(content=prompt)])
            try:
                result = json.loads(response.content.strip())
                interaction.summary = result.get("summary", notes[:200])
                interaction.sentiment = SentimentType(result.get("sentiment", "neutral"))
            except:
                interaction.summary = notes[:200]

        if interaction_type:
            interaction.interaction_type = InteractionType(interaction_type)
        if products_discussed:
            interaction.products_discussed = products_discussed
        if followup_date:
            interaction.followup_date = datetime.fromisoformat(followup_date)
        if followup_notes:
            interaction.followup_notes = followup_notes

        db.commit()
        return f"✅ Interaction {interaction_id} updated successfully."
    finally:
        db.close()

# ── Tool 3: Get HCP Profile ───────────────────────────────────────────────────
@tool
def get_hcp_profile(hcp_id: int) -> str:
    """Fetch an HCP's profile including their full interaction history."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return f"Error: HCP {hcp_id} not found."

        interactions = db.query(Interaction).filter(Interaction.hcp_id == hcp_id).order_by(Interaction.date.desc()).limit(5).all()
        history = [
            f"- [{i.date.strftime('%Y-%m-%d')}] {i.interaction_type.value}: {i.summary or i.notes or 'No notes'} (Sentiment: {i.sentiment.value if i.sentiment else 'N/A'})"
            for i in interactions
        ]
        profile = f"""👤 HCP Profile:
Name: {hcp.name}
Specialty: {hcp.specialty or 'N/A'}
Hospital: {hcp.hospital or 'N/A'}
Territory: {hcp.territory or 'N/A'}
Phone: {hcp.phone or 'N/A'}
Email: {hcp.email or 'N/A'}

📋 Recent Interactions ({len(interactions)}):
{chr(10).join(history) if history else 'No interactions yet.'}"""
        return profile
    finally:
        db.close()

# ── Tool 4: Schedule Follow-up ────────────────────────────────────────────────
@tool
def schedule_followup(
    interaction_id: int,
    followup_date: str,
    followup_notes: str = ""
) -> str:
    """Schedule a follow-up reminder for an existing interaction."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return f"Error: Interaction {interaction_id} not found."

        interaction.followup_date = datetime.fromisoformat(followup_date)
        interaction.followup_notes = followup_notes
        db.commit()

        hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
        return f"📅 Follow-up scheduled for {hcp.name if hcp else 'HCP'} on {followup_date}. Note: {followup_notes or 'None'}"
    finally:
        db.close()

# ── Tool 5: Sentiment Analysis ────────────────────────────────────────────────
@tool
def analyze_sentiment(text: str, hcp_id: int = None) -> str:
    """Analyze the sentiment of interaction notes and optionally update the HCP's latest interaction."""
    prompt = f"""Analyze the sentiment of this HCP interaction note for a life sciences field rep.
Text: {text}

Return ONLY JSON:
{{"sentiment": "positive|neutral|negative", "confidence": "high|medium|low", "key_signals": ["signal1","signal2"], "recommendation": "brief next step"}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        result = json.loads(response.content.strip())
        sentiment = result.get("sentiment", "neutral")
        confidence = result.get("confidence", "medium")
        signals = ", ".join(result.get("key_signals", []))
        recommendation = result.get("recommendation", "")

        if hcp_id:
            db = SessionLocal()
            try:
                latest = db.query(Interaction).filter(Interaction.hcp_id == hcp_id).order_by(Interaction.date.desc()).first()
                if latest:
                    latest.sentiment = SentimentType(sentiment)
                    db.commit()
            finally:
                db.close()

        return f"🧠 Sentiment: {sentiment} (confidence: {confidence})\nKey signals: {signals}\n💡 Recommendation: {recommendation}"
    except:
        return f"Sentiment analysis completed. Result: neutral"

# ── Agent Graph ───────────────────────────────────────────────────────────────
tools = [log_interaction, edit_interaction, get_hcp_profile, schedule_followup, analyze_sentiment]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are an AI assistant for a life sciences CRM system helping field representatives manage HCP (Healthcare Professional) interactions.

You have access to these tools:
1. log_interaction - Log a new HCP interaction with AI summarization
2. edit_interaction - Edit an existing interaction
3. get_hcp_profile - Get HCP profile and interaction history
4. schedule_followup - Schedule a follow-up reminder
5. analyze_sentiment - Analyze sentiment of interaction notes

Always be professional, concise, and helpful. When logging interactions, always use the log_interaction tool."""

def agent_node(state: AgentState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def tool_node(state: AgentState):
    from langchain_core.messages import ToolMessage
    tool_map = {t.name: t for t in tools}
    last_message = state["messages"][-1]
    results = []
    for tool_call in last_message.tool_calls:
        tool_fn = tool_map.get(tool_call["name"])
        if tool_fn:
            result = tool_fn.invoke(tool_call["args"])
            results.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    return {"messages": results, "tool_output": str(results[-1].content) if results else ""}

def should_continue(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

# Build graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
agent_app = graph.compile()

def run_agent(user_message: str, history: list = []) -> str:
    messages = history + [HumanMessage(content=user_message)]
    result = agent_app.invoke({"messages": messages, "tool_output": ""})
    final = result["messages"][-1]
    return final.content if hasattr(final, "content") else str(final)
