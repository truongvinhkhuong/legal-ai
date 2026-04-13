"""Chat endpoint: SSE streaming Q&A."""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_engine
from src.api.models import ChatRequest

router = APIRouter(tags=["chat"])


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    engine = get_engine()

    async def event_generator() -> AsyncGenerator[dict, None]:
        async for event in engine.query(request):
            event_type = event.get("type", "chunk")
            data = event.get("data", "")

            if event_type == "done":
                yield {"event": "done", "data": json.dumps(data, ensure_ascii=False)}
            elif event_type == "error":
                yield {"event": "error", "data": json.dumps({"error": data}, ensure_ascii=False)}
            else:
                yield {"data": json.dumps({"type": "chunk", "data": data}, ensure_ascii=False)}

    return EventSourceResponse(event_generator())
