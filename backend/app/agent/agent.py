import json
import operator
from datetime import datetime
from typing import Annotated, List, TypedDict
import dateparser

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.config import settings
from app.db.database import SessionLocal
from app.models.models import HCP, Interaction, InteractionType, SentimentType


# Groq model used by the LangGraph tools.
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.2,
)


class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    tool_output: str
    selected_hcp_id: int


@tool
def log_interaction(
    hcp_id: int,
    notes: str,
    interaction_type: str = "visit",
    products_discussed: str = "",
    logged_by: str = "Field Rep",
    followup_date: str = None,
) -> str:
    """Log a new HCP interaction, summarize the note, and detect sentiment."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return f"Error: HCP with id {hcp_id} not found."

        prompt = f"""You are a CRM copilot for life sciences. Analyze this HCP interaction note and return JSON only.
Notes: {notes}
Products discussed: {products_discussed}

Return ONLY this JSON without markdown:
{{"summary": "2-3 sentence summary", "sentiment": "positive|neutral|negative"}}"""

        response = llm.invoke([HumanMessage(content=prompt)])
        try:
            result = json.loads(response.content.strip())
            summary = result.get("summary", notes[:200])
            sentiment = result.get("sentiment", "neutral")
        except (json.JSONDecodeError, TypeError, AttributeError):
            summary = notes[:200]
            sentiment = "neutral"

        parsed_followup = (
            dateparser.parse(followup_date)
            if followup_date
            else None
        )

        interaction = Interaction(
            hcp_id=hcp_id,
            interaction_type=InteractionType(interaction_type),
            notes=notes,
            summary=summary,
            products_discussed=products_discussed,
            sentiment=SentimentType(sentiment),
            logged_by=logged_by,
            followup_date=parsed_followup,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return (
            f"Interaction logged (ID: {interaction.id}) for {hcp.name}. "
            f"Summary: {summary}. Sentiment: {sentiment}."
        )
    finally:
        db.close()


@tool
def edit_interaction(
    interaction_id: int,
    notes: str = None,
    interaction_type: str = None,
    products_discussed: str = None,
    followup_date: str = None,
    followup_notes: str = None,
) -> str:
    """Edit an existing interaction and refresh the summary when notes change."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return f"Error: Interaction {interaction_id} not found."

        if notes:
            interaction.notes = notes
            prompt = f"""Summarize this updated HCP interaction note in 2-3 sentences.
Notes: {notes}

Return ONLY JSON:
{{"summary": "...", "sentiment": "positive|neutral|negative"}}"""
            response = llm.invoke([HumanMessage(content=prompt)])
            try:
                result = json.loads(response.content.strip())
                interaction.summary = result.get("summary", notes[:200])
                interaction.sentiment = SentimentType(result.get("sentiment", "neutral"))
            except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
                interaction.summary = notes[:200]

        if interaction_type:
            interaction.interaction_type = InteractionType(interaction_type)
        if products_discussed:
            interaction.products_discussed = products_discussed
        if followup_date:
            interaction.followup_date = dateparser.parse(followup_date)
        if followup_notes:
            interaction.followup_notes = followup_notes

        db.commit()
        return f"Interaction {interaction_id} updated successfully."
    finally:
        db.close()


@tool
def get_hcp_profile(hcp_id: int) -> str:
    """Fetch an HCP profile with the most recent interaction history."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return f"Error: HCP {hcp_id} not found."

        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp_id)
            .order_by(Interaction.date.desc())
            .limit(5)
            .all()
        )
        history = [
            (
                f"- [{item.date.strftime('%Y-%m-%d')}] {item.interaction_type.value}: "
                f"{item.summary or item.notes or 'No notes'} "
                f"(Sentiment: {item.sentiment.value if item.sentiment else 'N/A'})"
            )
            for item in interactions
        ]

        return f"""HCP Profile
Name: {hcp.name}
Specialty: {hcp.specialty or 'N/A'}
Hospital: {hcp.hospital or 'N/A'}
Territory: {hcp.territory or 'N/A'}
Phone: {hcp.phone or 'N/A'}
Email: {hcp.email or 'N/A'}

Recent Interactions ({len(interactions)}):
{chr(10).join(history) if history else 'No interactions yet.'}"""
    finally:
        db.close()


@tool
def schedule_followup(
    interaction_id: int,
    followup_date: str,
    followup_notes: str = "",
) -> str:
    """Schedule a follow-up reminder for an existing interaction."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return f"Error: Interaction {interaction_id} not found."

        interaction.followup_date = dateparser.parse(followup_date)
        interaction.followup_notes = followup_notes
        db.commit()

        hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
        name = hcp.name if hcp else "HCP"
        return f"Follow-up scheduled for {name} on {followup_date}. Note: {followup_notes or 'None'}"
    finally:
        db.close()


@tool
def analyze_sentiment(text: str, hcp_id: int = None) -> str:
    """Analyze sentiment in interaction notes and optionally update the latest HCP interaction."""
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
                latest = (
                    db.query(Interaction)
                    .filter(Interaction.hcp_id == hcp_id)
                    .order_by(Interaction.date.desc())
                    .first()
                )
                if latest:
                    latest.sentiment = SentimentType(sentiment)
                    db.commit()
            finally:
                db.close()

        return (
            f"Sentiment: {sentiment} (confidence: {confidence})\n"
            f"Key signals: {signals}\n"
            f"Recommendation: {recommendation}"
        )
    except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
        return "Sentiment analysis completed. Result: neutral"


tools = [log_interaction, edit_interaction, get_hcp_profile, schedule_followup, analyze_sentiment]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a CRM copilot for life sciences field representatives managing HCP (Healthcare Professional) interactions.

You have access to these tools:
1. log_interaction - Log a new HCP interaction with model-generated summarization
2. edit_interaction - Edit an existing interaction
3. get_hcp_profile - Get HCP profile and interaction history
4. schedule_followup - Schedule a follow-up reminder
5. analyze_sentiment - Analyze sentiment of interaction notes

Always be professional, concise, and helpful.

Tool safety rules:
- Use read-only tools for read-only requests.
- Do not call log_interaction unless the user explicitly asks to log or save an interaction.
- Do not call edit_interaction unless the user explicitly asks to change an existing interaction.
- Do not call schedule_followup unless the user explicitly asks to schedule, add, or update a follow-up.
- Do not modify database records while answering a profile lookup or general question.
- If required IDs or dates are missing, ask a short clarification instead of guessing."""


def agent_node(state: AgentState):

    selected_context = ""

    if state.get("selected_hcp_id"):
        selected_context = f"""
Currently selected HCP ID: {state['selected_hcp_id']}

IMPORTANT:
- Always prioritize this HCP unless user explicitly specifies another HCP.
- Never guess interaction IDs.
- If interaction ID is missing for edit/schedule operations, ask for clarification.
"""

    system_prompt = SYSTEM_PROMPT + "\n" + selected_context

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def tool_node(state: AgentState):
    from langchain_core.messages import ToolMessage

    tool_map = {item.name: item for item in tools}
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


# The graph loops through tools when needed, then returns to the model for the final response.
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
agent_app = graph.compile()


def run_agent(
    user_message: str,
    history: list = None,
    selected_hcp_id: int = None
) -> str:
    messages = (history or []) + [HumanMessage(content=user_message)]
    result = agent_app.invoke({
    "messages": messages,
    "tool_output": "",
    "selected_hcp_id": selected_hcp_id
})
    final = result["messages"][-1]
    return final.content if hasattr(final, "content") else str(final)
