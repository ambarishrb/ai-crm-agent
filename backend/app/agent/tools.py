import json
import logging
from typing import Optional
from datetime import date, datetime

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy.orm import Session

from app.models.hcp import HCP
from app.models.interaction import Interaction
from app.config import settings

logger = logging.getLogger(__name__)


def _get_llm(temperature: float = 0.1) -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
    )


def _fuzzy_match_hcp(db: Session, name: str) -> Optional[HCP]:
    """Find the best matching HCP by name (case-insensitive partial match)."""
    # Try exact match first
    hcp = db.query(HCP).filter(HCP.full_name.ilike(name)).first()
    if hcp:
        return hcp

    # Try partial match
    # Strip common prefixes for matching
    search_name = name.replace("Dr.", "").replace("Dr", "").strip()
    hcp = db.query(HCP).filter(HCP.full_name.ilike(f"%{search_name}%")).first()
    return hcp


def create_tools(db: Session, form_data: Optional[dict] = None):
    """Factory function — creates tools with a DB session and form state bound via closure."""
    _form_data = form_data or {}

    @tool
    def log_interaction(user_message: str) -> str:
        """Parse a natural language description of an HCP interaction and log it.
        Use this when the user describes a meeting, call, email, or conference with a doctor/HCP.
        The user_message contains the free-text description of the interaction."""

        logger.info("[TOOL] log_interaction called | message: %s", user_message[:100])
        llm = _get_llm(temperature=0.1)
        extraction_prompt = f"""Extract structured interaction data from this message.

IMPORTANT RULES:
- "hcp_name" is the DOCTOR's name (the Healthcare Professional). This is the physician/doctor being visited (e.g., Dr. Smith, Dr. Patel). It is NOT a patient.
- "attendees" is everyone ELSE present at the interaction — patients, other reps, nurses, colleagues, etc. Do NOT put the doctor's name here.
- "materials_shared" is a list of brochures, documents, study reports, guides etc. shared during the interaction.
- "samples_distributed" is a list of product samples given out (e.g., "Product X 10mg x2").

Return ONLY a valid JSON object with these fields (use null for missing fields):
{{
    "hcp_name": "string - the DOCTOR/physician name only (e.g., Dr. Smith)",
    "interaction_type": "Meeting|Call|Email|Conference",
    "interaction_date": "YYYY-MM-DD or null",
    "interaction_time": "HH:MM:SS or null",
    "attendees": "string - comma-separated names of OTHER people present (patients, reps, nurses), NOT the doctor. null if none mentioned",
    "topics_discussed": "string - key discussion points, or null",
    "sentiment": "Positive|Neutral|Negative or null",
    "outcomes": "string - key outcomes or agreements, or null",
    "follow_up_actions": "string - next steps or tasks, or null",
    "materials_shared": ["list of material/document names as strings, or empty array"],
    "samples_distributed": ["list of sample descriptions as strings e.g. 'Product X 10mg x2', or empty array"]
}}

Message: {user_message}

Today's date is {date.today().isoformat()}. If the user says "today", use today's date.
Return ONLY the JSON, no other text."""

        response = llm.invoke(extraction_prompt)
        try:
            extracted = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                extracted = json.loads(content[start:end])
            else:
                return json.dumps({"error": "Could not parse interaction data from message"})

        hcp_name = extracted.get("hcp_name") or "Unknown"

        # Parse date/time
        interaction_date = None
        if extracted.get("interaction_date"):
            try:
                interaction_date = date.fromisoformat(extracted["interaction_date"])
            except ValueError:
                interaction_date = date.today()

        interaction_time = None
        if extracted.get("interaction_time"):
            try:
                interaction_time = datetime.strptime(extracted["interaction_time"], "%H:%M:%S").time()
            except ValueError:
                pass

        # Create interaction (hcp_name stored as attendees context, no FK needed)
        interaction = Interaction(
            interaction_type=extracted.get("interaction_type", "Meeting"),
            interaction_date=interaction_date or date.today(),
            interaction_time=interaction_time,
            attendees=extracted.get("attendees"),
            topics_discussed=extracted.get("topics_discussed"),
            sentiment=extracted.get("sentiment", "Neutral"),
            outcomes=extracted.get("outcomes"),
            follow_up_actions=extracted.get("follow_up_actions"),
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        # Materials and samples as simple text chips
        materials_list = [str(m) for m in (extracted.get("materials_shared") or [])]
        samples_list = [str(s) for s in (extracted.get("samples_distributed") or [])]

        form_updates = {
            "hcp": {"id": str(interaction.id), "name": hcp_name},
            "interactionType": interaction.interaction_type,
            "date": interaction.interaction_date.isoformat() if interaction.interaction_date else "",
            "time": interaction.interaction_time.isoformat() if interaction.interaction_time else "",
            "attendees": interaction.attendees or "",
            "topicsDiscussed": interaction.topics_discussed or "",
            "sentiment": interaction.sentiment or "Neutral",
            "outcomes": interaction.outcomes or "",
            "followUpActions": interaction.follow_up_actions or "",
            "materialsShared": materials_list,
            "samplesDistributed": samples_list,
        }

        return json.dumps({
            "interaction_id": str(interaction.id),
            "form_updates": form_updates,
            "confirmation": f"Logged {interaction.interaction_type} with {hcp_name} on {interaction.interaction_date}.",
        })

    @tool
    def edit_interaction(edit_instruction: str, interaction_id: str) -> str:
        """Edit an existing interaction based on a natural language instruction.
        Use this when the user wants to change or update fields of an already logged interaction.
        edit_instruction is what the user wants to change. interaction_id is the UUID of the interaction to edit."""

        logger.info("[TOOL] edit_interaction called | instruction: %s | id: %s", edit_instruction[:100], interaction_id)
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"Interaction {interaction_id} not found"})

        # Build current field values from form state (frontend) + DB
        current_fields = {
            "hcp_name": _form_data.get("hcp_name") or ((_form_data.get("hcp") or {}).get("name")) or "",
            "interaction_type": _form_data.get("interaction_type") or interaction.interaction_type,
            "interaction_date": _form_data.get("date") or (str(interaction.interaction_date) if interaction.interaction_date else None),
            "interaction_time": _form_data.get("time") or (str(interaction.interaction_time) if interaction.interaction_time else None),
            "attendees": _form_data.get("attendees") or interaction.attendees or "",
            "topics_discussed": _form_data.get("topics_discussed") or interaction.topics_discussed or "",
            "sentiment": _form_data.get("sentiment") or interaction.sentiment,
            "outcomes": _form_data.get("outcomes") or interaction.outcomes or "",
            "follow_up_actions": _form_data.get("follow_up_actions") or interaction.follow_up_actions or "",
            "materials_shared": _form_data.get("materials_shared") or [],
            "samples_distributed": _form_data.get("samples_distributed") or [],
        }

        llm = _get_llm(temperature=0.1)
        parse_prompt = f"""The user wants to edit an interaction. Parse their instruction into field updates.

CURRENT VALUES of the interaction (these are the EXISTING values — you must preserve them when appending):
- hcp_name: {current_fields.get('hcp_name') or 'empty'}
- interaction_type: {current_fields.get('interaction_type') or 'empty'}
- interaction_date: {current_fields.get('interaction_date') or 'empty'}
- interaction_time: {current_fields.get('interaction_time') or 'empty'}
- attendees: {current_fields.get('attendees') or 'empty'}
- topics_discussed: {current_fields.get('topics_discussed') or 'empty'}
- sentiment: {current_fields.get('sentiment') or 'empty'}
- outcomes: {current_fields.get('outcomes') or 'empty'}
- follow_up_actions: {current_fields.get('follow_up_actions') or 'empty'}
- materials_shared: {json.dumps(current_fields.get('materials_shared') or [])}
- samples_distributed: {json.dumps(current_fields.get('samples_distributed') or [])}

CRITICAL RULES:
- "hcp_name" = DOCTOR name. "attendees" = everyone ELSE (not the doctor).
- When the user says "also", "add", "additionally", "too", or similar → you MUST KEEP all existing values AND add the new ones.
  Example: materials_shared is currently ["Product X Brochure"]. User says "also shared Dosing Guide" → result MUST be ["Product X Brochure", "Dosing Guide"].
  Example: attendees is currently "Alice, Bob". User says "Jayanthi was also attendee" → result MUST be "Alice, Bob, Jayanthi".
- Only REPLACE a field entirely if the user explicitly says to change/replace/set it to something new.

Return ONLY a valid JSON object with ONLY the fields that should change (omit unchanged fields):
{{
    "hcp_name": "new doctor name or null",
    "interaction_type": "Meeting|Call|Email|Conference or null",
    "interaction_date": "YYYY-MM-DD or null",
    "interaction_time": "HH:MM:SS or null",
    "attendees": "COMPLETE attendee string (existing + new if appending) or null",
    "topics_discussed": "COMPLETE topics (existing + new if appending) or null",
    "sentiment": "Positive|Neutral|Negative or null",
    "outcomes": "COMPLETE outcomes (existing + new if appending) or null",
    "follow_up_actions": "COMPLETE actions (existing + new if appending) or null",
    "materials_shared": ["COMPLETE list (existing + new if appending)"] or null,
    "samples_distributed": ["COMPLETE list (existing + new if appending)"] or null
}}

User instruction: {edit_instruction}

Today's date is {date.today().isoformat()}.
Return ONLY the JSON, no other text."""

        response = llm.invoke(parse_prompt)
        try:
            updates = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                updates = json.loads(content[start:end])
            else:
                return json.dumps({"error": "Could not parse edit instruction"})

        form_updates = {}

        # Handle HCP name change (free text, no DB lookup)
        hcp_name = updates.pop("hcp_name", None)
        if hcp_name:
            form_updates["hcp"] = {"id": str(interaction.id), "name": hcp_name}

        # Handle materials change (plain text chips)
        materials_shared = updates.pop("materials_shared", None)
        if materials_shared is not None:
            form_updates["materialsShared"] = [str(m) for m in materials_shared]

        # Handle samples change (plain text chips)
        samples_distributed = updates.pop("samples_distributed", None)
        if samples_distributed is not None:
            form_updates["samplesDistributed"] = [str(s) for s in samples_distributed]

        # Handle simple field updates
        field_map = {
            "interaction_type": "interactionType",
            "interaction_date": "date",
            "interaction_time": "time",
            "attendees": "attendees",
            "topics_discussed": "topicsDiscussed",
            "sentiment": "sentiment",
            "outcomes": "outcomes",
            "follow_up_actions": "followUpActions",
        }

        for field, value in updates.items():
            if field in field_map and value is not None:
                setattr(interaction, field, value)
                form_updates[field_map[field]] = value

        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "interaction_id": str(interaction.id),
            "form_updates": form_updates,
            "confirmation": f"Updated fields: {', '.join(form_updates.keys())}",
        })

    @tool
    def analyze_sentiment(interaction_id: str) -> str:
        """Analyze the sentiment of an interaction based on its content.
        Use this when the user asks to analyze or assess the sentiment of an interaction.
        interaction_id is the UUID of the interaction to analyze."""

        logger.info("[TOOL] analyze_sentiment called | id: %s", interaction_id)
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"Interaction {interaction_id} not found"})

        hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
        context_text = f"""Topics discussed: {interaction.topics_discussed or 'N/A'}
Outcomes: {interaction.outcomes or 'N/A'}
Follow-up actions: {interaction.follow_up_actions or 'N/A'}"""

        llm = _get_llm(temperature=0.1)
        sentiment_prompt = f"""Analyze the sentiment of this HCP interaction and classify it.

HCP: {hcp.full_name if hcp else 'Unknown'} ({hcp.specialty if hcp else 'Unknown'})
{context_text}

Return ONLY a valid JSON object:
{{
    "sentiment": "Positive|Neutral|Negative",
    "rationale": "Brief explanation of why this sentiment was chosen"
}}"""

        response = llm.invoke(sentiment_prompt)
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {"sentiment": "Neutral", "rationale": "Could not analyze"}

        # Update interaction sentiment
        interaction.sentiment = result["sentiment"]
        db.commit()

        return json.dumps({
            "interaction_id": str(interaction.id),
            "form_updates": {"sentiment": result["sentiment"]},
            "sentiment": result["sentiment"],
            "rationale": result.get("rationale", ""),
        })

    @tool
    def suggest_followups(interaction_id: str) -> str:
        """Generate actionable follow-up suggestions for an interaction.
        Use this when the user asks for follow-up suggestions or next steps.
        interaction_id is the UUID of the interaction."""

        logger.info("[TOOL] suggest_followups called | id: %s", interaction_id)
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"Interaction {interaction_id} not found"})

        hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()

        llm = _get_llm(temperature=0.7)
        followup_prompt = f"""Based on this HCP interaction, suggest 3 specific, actionable follow-up actions with timeframes.

HCP: {hcp.full_name if hcp else 'Unknown'} (Specialty: {hcp.specialty if hcp else 'Unknown'})
Interaction Type: {interaction.interaction_type}
Topics Discussed: {interaction.topics_discussed or 'N/A'}
Sentiment: {interaction.sentiment or 'N/A'}
Outcomes: {interaction.outcomes or 'N/A'}

Return ONLY a valid JSON object:
{{
    "suggestions": [
        "Follow-up action 1 with timeframe",
        "Follow-up action 2 with timeframe",
        "Follow-up action 3 with timeframe"
    ]
}}"""

        response = llm.invoke(followup_prompt)
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {"suggestions": ["Schedule a follow-up meeting within 2 weeks"]}

        suggestions = result.get("suggestions", [])

        # Store suggestions in the interaction
        interaction.ai_suggested_followups = suggestions
        db.commit()

        return json.dumps({
            "interaction_id": str(interaction.id),
            "form_updates": {"aiSuggestedFollowups": suggestions},
            "suggestions": suggestions,
        })

    @tool
    def summarize_interaction(interaction_id: str) -> str:
        """Generate a professional summary of an interaction for call reports.
        Use this when the user asks to summarize an interaction.
        interaction_id is the UUID of the interaction."""

        logger.info("[TOOL] summarize_interaction called | id: %s", interaction_id)
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"Interaction {interaction_id} not found"})

        # Resolve HCP name: prefer form_data, then DB
        hcp_name_from_form = (_form_data.get("hcp") or {}).get("name") or _form_data.get("hcp_name")
        hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
        hcp_display_name = hcp_name_from_form or (hcp.full_name if hcp else "Unknown")
        hcp_specialty = hcp.specialty if hcp else "Unknown"
        hcp_org = hcp.organization if hcp else "Unknown"

        # Prefer form_data for all editable fields (may not be persisted to DB yet)
        interaction_type = _form_data.get("interactionType") or interaction.interaction_type
        interaction_date = _form_data.get("date") or str(interaction.interaction_date) if interaction.interaction_date else "Unknown"
        topics = _form_data.get("topicsDiscussed") or interaction.topics_discussed or "N/A"
        sentiment = _form_data.get("sentiment") or interaction.sentiment or "N/A"
        outcomes = _form_data.get("outcomes") or interaction.outcomes or "N/A"
        follow_up = _form_data.get("followUpActions") or interaction.follow_up_actions or "N/A"

        # Materials and samples from form_data (free text chips)
        mat_names = _form_data.get("materialsShared") or _form_data.get("materials_shared") or []
        sample_names = _form_data.get("samplesDistributed") or _form_data.get("samples_distributed") or []

        llm = _get_llm(temperature=0.3)
        summary_prompt = f"""Generate a concise, professional summary of this HCP interaction suitable for CRM records and manager review.

HCP: {hcp_display_name} ({hcp_specialty}, {hcp_org})
Type: {interaction_type}
Date: {interaction_date}
Topics: {topics}
Sentiment: {sentiment}
Outcomes: {outcomes}
Follow-up Actions: {follow_up}
Materials Shared: {', '.join(mat_names) if mat_names else 'None'}
Samples Distributed: {', '.join(sample_names) if sample_names else 'None'}

Return ONLY a valid JSON object:
{{
    "summary": "Professional summary paragraph",
    "key_points": ["key point 1", "key point 2", "key point 3"]
}}"""

        response = llm.invoke(summary_prompt)
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(content[start:end])
            else:
                result = {"summary": "Summary could not be generated.", "key_points": []}

        # Store summary
        interaction.ai_summary = result.get("summary", "")
        db.commit()

        return json.dumps({
            "interaction_id": str(interaction.id),
            "form_updates": {"aiSummary": result.get("summary", "")},
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
        })

    return [log_interaction, edit_interaction, analyze_sentiment, suggest_followups, summarize_interaction]
