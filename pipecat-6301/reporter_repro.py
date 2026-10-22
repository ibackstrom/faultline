"""GeminiLiveLLMService re-sends settled tool results after a resumed reconnect.

Offline: the Live session is an AsyncMock and _connect is stubbed, so only Pipecat's own
bookkeeping runs. Tested on pipecat-ai 1.13.0 (gemini_live/llm.py is identical on main).
"""

import asyncio
from unittest.mock import AsyncMock

from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService


def tool_turn(call_id: str) -> list[dict]:
    return [
        {"role": "assistant", "tool_calls": [{"id": call_id, "type": "function",
                                              "function": {"name": "list_items", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": call_id, "content": '{"items": []}'},
    ]


def sent(session: AsyncMock) -> list[tuple[str, str]]:
    return [(r.id, r.name) for call in session.send_tool_response.await_args_list
            for r in [call.kwargs["function_responses"]]]


async def main() -> None:
    llm = GeminiLiveLLMService(api_key="test")  # default model: models/gemini-3.8-live
    llm.register_function("list_items", AsyncMock(), cancellable_by_llm=False)

    # Connection 1: a tool call completes and its result is sent, as the assistant
    # aggregator's upstream context push makes it happen.
    first = AsyncMock()
    llm._session = first
    llm._tool_call_id_to_name["call-1"] = "list_items"
    context = LLMContext(messages=[{"role": "user", "content": "list them"}, *tool_turn("call-1")])
    llm._context = context
    await llm._handle_context(context, FrameDirection.UPSTREAM)
    print("connection 1 sent:", sent(first))  # [('call-1', 'list_items')]  correct

    # The server ends the connection (GoAway / ~10 min limit); Pipecat resumes with its handle.
    llm._session_resumption_handle = "resumption-handle"
    second = AsyncMock()

    async def resume(session_resumption_handle=None):
        await llm._handle_session_ready(second)  # the resumed branch: only marks realtime input ready

    llm._connect = resume
    await llm._reconnect()

    # Connection 2: a new tool call completes; the aggregator pushes the context upstream again.
    llm._tool_call_id_to_name["call-2"] = "list_items"
    context.add_messages(tool_turn("call-2"))
    await llm._handle_context(context, FrameDirection.UPSTREAM)
    print("connection 2 sent:", sent(second))
    # Expected: [('call-2', 'list_items')]
    # Actual:   [('call-1', 'tool_call_result'), ('call-2', 'list_items')]


asyncio.run(main())
