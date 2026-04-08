import json
import logging
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.agent.tools import create_tools
from app.config import settings

SYSTEM_PROMPT = """You are an AI assistant for a pharmaceutical CRM system. You help field representatives log and manage their interactions with Healthcare Professionals (HCPs).

KEY CONCEPTS:
- HCP Name = the DOCTOR / physician being visited (e.g., Dr. Smith, Dr. Patel). This is always a doctor.
- Attendees = other people present at the interaction (patients, other reps, nurses, colleagues). NOT the doctor.
- The field rep (user) is logging their visit to a doctor. The doctor is the HCP.

You have access to these tools:
1. log_interaction - Log a new HCP interaction from natural language description
2. edit_interaction - Edit fields of an existing interaction
3. analyze_sentiment - Analyze the sentiment of an interaction
4. suggest_followups - Generate follow-up suggestions for an interaction
5. summarize_interaction - Generate a professional summary of an interaction

TOOL ROUTING RULES:
- Use log_interaction ONLY when the user is describing a NEW interaction for the first time AND there is NO active interaction_id.
- If there IS an active interaction_id already, the user is referring to the EXISTING interaction. Use edit_interaction for ANY changes, additions, or corrections (e.g., "also shared...", "add...", "change...", "actually the doctor was...").
- Use analyze_sentiment when asked to analyze or assess sentiment.
- Use suggest_followups when asked for follow-up suggestions or next steps.
- Use summarize_interaction when asked for a summary.

For edit_interaction, analyze_sentiment, suggest_followups, and summarize_interaction, use the active interaction_id from context.

Be concise and professional in your responses."""


def build_graph(db: Session, form_data: Optional[dict] = None):
    """Build the LangGraph agent with DB session bound to tools."""

    tools = create_tools(db, form_data)
    tool_node = ToolNode(tools)

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.7,
    ).bind_tools(tools)

    def route_intent(state: AgentState) -> AgentState:
        """LLM decides which tool to call based on user message."""
        messages = state["messages"]
        interaction_id = state.get("interaction_id")

        # Inject system prompt and context
        system_msg = SystemMessage(content=SYSTEM_PROMPT)

        # Add context about current interaction if available
        context_parts = []
        if interaction_id:
            context_parts.append(f"Current active interaction_id: {interaction_id}")

        form_data = state.get("form_data")
        if form_data:
            context_parts.append(f"Current form state: {json.dumps(form_data)}")

        if context_parts:
            context_msg = SystemMessage(content="\n".join(context_parts))
            full_messages = [system_msg, context_msg] + list(messages)
        else:
            full_messages = [system_msg] + list(messages)

        response = llm.invoke(full_messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """Check if the LLM wants to call a tool or respond directly."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    def summarize_response(state: AgentState) -> AgentState:
        """After tool execution, format the final response."""
        messages = state["messages"]

        # Find the last tool message result
        tool_result = None
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                tool_result = msg
                break

        if not tool_result:
            return state

        try:
            result_data = json.loads(tool_result.content)
        except (json.JSONDecodeError, TypeError):
            return state

        # Check for errors
        if "error" in result_data:
            error_msg = AIMessage(content=f"I encountered an issue: {result_data['error']}")
            return {"messages": [error_msg]}

        # Build a friendly response using LLM
        llm_plain = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0.7,
        )

        summarize_prompt = f"""Based on this tool result, write a brief, friendly confirmation message for the user.
Tool result: {json.dumps(result_data)}
Keep it to 1-2 sentences. Be specific about what was done."""

        response = llm_plain.invoke(summarize_prompt)

        summary_msg = AIMessage(content=response.content)
        return {"messages": [summary_msg]}

    # Build the graph
    graph = StateGraph(AgentState)

    graph.add_node("route_intent", route_intent)
    graph.add_node("tools", tool_node)
    graph.add_node("summarize_response", summarize_response)

    graph.set_entry_point("route_intent")

    graph.add_conditional_edges(
        "route_intent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    graph.add_edge("tools", "summarize_response")
    graph.add_edge("summarize_response", END)

    return graph.compile()


def _extract_result(messages, interaction_id):
    """Extract reply, form_updates, tool_used, and interaction_id from graph messages."""
    reply = ""
    form_updates = None
    tool_used = None
    result_interaction_id = interaction_id

    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_used = msg.tool_calls[0]["name"]
        elif isinstance(msg, ToolMessage):
            try:
                tool_data = json.loads(msg.content)
                if "form_updates" in tool_data:
                    if form_updates is None:
                        form_updates = {}
                    form_updates.update(tool_data["form_updates"])
                if "interaction_id" in tool_data:
                    result_interaction_id = tool_data["interaction_id"]
            except (json.JSONDecodeError, TypeError):
                pass

    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not (hasattr(msg, "tool_calls") and msg.tool_calls):
            reply = msg.content
            break

    if not reply:
        reply = "I've processed your request."

    return reply, form_updates, tool_used, result_interaction_id


def invoke_agent(
    db: Session,
    user_message: str,
    form_data: Optional[dict] = None,
    interaction_id: Optional[str] = None,
) -> dict:
    """Invoke the agent and return structured response for the chat endpoint."""

    logger.info("[AGENT] Invoked | message: %s | interaction_id: %s", user_message[:100], interaction_id)

    graph = build_graph(db, form_data)

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "form_data": form_data or {},
        "interaction_id": interaction_id,
    }

    result = graph.invoke(initial_state)
    reply, form_updates, tool_used, result_interaction_id = _extract_result(
        result["messages"], interaction_id
    )

    logger.info("[AGENT] Result | tool_used: %s | interaction_id: %s", tool_used, result_interaction_id)

    # Auto-chain: after log_interaction, run analyze_sentiment + suggest_followups
    if tool_used == "log_interaction" and result_interaction_id:
        chain_parts = []
        tools = create_tools(db, form_data)
        tool_map = {t.name: t for t in tools}

        try:
            sentiment_result = tool_map["analyze_sentiment"].invoke(
                {"interaction_id": result_interaction_id}
            )
            sentiment_data = json.loads(sentiment_result)
            if form_updates is None:
                form_updates = {}
            if "form_updates" in sentiment_data:
                form_updates.update(sentiment_data["form_updates"])
            if sentiment_data.get("rationale"):
                chain_parts.append(
                    f"Sentiment: {sentiment_data.get('sentiment', 'N/A')} — {sentiment_data['rationale']}"
                )
        except Exception:
            pass

        try:
            followup_result = tool_map["suggest_followups"].invoke(
                {"interaction_id": result_interaction_id}
            )
            followup_data = json.loads(followup_result)
            if form_updates is None:
                form_updates = {}
            if "form_updates" in followup_data:
                form_updates.update(followup_data["form_updates"])
            suggestions = followup_data.get("suggestions", [])
            if suggestions:
                chain_parts.append("Suggested follow-ups:\n" + "\n".join(f"  • {s}" for s in suggestions))
        except Exception:
            pass

        if chain_parts:
            reply = reply + "\n\n" + "\n\n".join(chain_parts)

    return {
        "reply": reply,
        "form_updates": form_updates,
        "tool_used": tool_used,
        "interaction_id": result_interaction_id,
    }
