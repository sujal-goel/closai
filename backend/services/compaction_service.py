"""
Compaction Service - Implements sliding window + summarization to prevent context rot.
Used by the chat route when conversation history exceeds the threshold.
"""
import logging
from services.gemini_service import call_gemini

logger = logging.getLogger(__name__)

COMPACTION_THRESHOLD = 10

SUMMARY_PROMPT = """
You are a conversation memory manager for a cloud architecture design tool.
Distill the following session into a concise "Conversation State" block.

Include:
- User intent and workload type (e.g., ai_ml, web_app)
- Confirmed constraints (region, scale, budget, GPU needs, compliance)
- Key architectural decisions made so far
- Remaining open questions or unknowns

Keep it under 200 words. Output as a plain text paragraph — no JSON, no bullet points.
"""


async def compact_history(history: list[dict], current_summary: str = "") -> str:
    """
    Summarizes the history and combines it with any existing summary.
    Returns the updated summary string.
    """
    if not history:
        return current_summary

    history_text = "\n".join(
        [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history]
    )
    prompt = f"Existing Summary: {current_summary}\n\nNew Messages:\n{history_text}"

    try:
        new_summary = await call_gemini(prompt, SUMMARY_PROMPT, use_json=False)
        return new_summary
    except Exception as e:
        logger.error(f"Compaction failed: {e}")
        return current_summary


def get_sliding_window(messages: list[dict], window_size: int = 10) -> list[dict]:
    """Returns the last N messages from the history."""
    if len(messages) <= window_size:
        return messages
    return messages[-window_size:]


def needs_compaction(messages: list[dict], threshold: int = COMPACTION_THRESHOLD) -> bool:
    """Check if the message history has exceeded the compaction threshold."""
    return len(messages) >= threshold
