"""
Chat Router
============
Streaming chat endpoint for the live player analyst.

Uses the same direct LLM streaming pattern as the demo chat — proven to work
across all 7 LLM providers. Player context and dataset stats are injected into
the system prompt so the LLM can answer questions without tool calls.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    """
    player_context: full response from GET /api/v1/players/{platform}/{id}.
    Pass this when the user is viewing a player — gives the LLM real data.

    conversation_history: previous messages for multi-turn context.
    Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    message: str
    player_context: dict | None = None
    conversation_history: list[dict] = []


@router.post("")
async def chat(request: ChatRequest):
    """Stream the analyst's response token by token."""
    from api.agents.churn_analyst import get_agent, build_system_prompt

    system_prompt = build_system_prompt(request.player_context)
    llm = get_agent()

    async def stream():
        messages = [{"role": "system", "content": system_prompt}]
        for msg in request.conversation_history[-6:]:  # last 3 turns
            messages.append(msg)
        messages.append({"role": "user", "content": request.message})

        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content

    return StreamingResponse(stream(), media_type="text/plain")
