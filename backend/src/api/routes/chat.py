"""Chat endpoint: SSE streaming Q&A."""

from __future__ import annotations

import json
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_engine
from src.api.models import ChatRequest, UserContext
from src.auth.dependencies import get_current_user
from src.core.gate import require_feature
from src.db.models.user import User

router = APIRouter(tags=["chat"])


@router.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: Annotated[User, Depends(require_feature("chat"))],
):
    engine = get_engine()

    # Build user context from authenticated user
    request.user_context = UserContext(
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        departments=current_user.departments or ["all"],
        access_levels=current_user.access_levels or ["public"],
        role=current_user.role,
    )

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
