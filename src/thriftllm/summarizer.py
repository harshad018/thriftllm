import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConversationSummarizer:
    """
    Manages long conversational contexts by maintaining a rolling summary
    of older turns while keeping recent turns intact. Backed by Redis for
    session persistence.
    """
    
    def __init__(self, redis_client=None, max_history_tokens: int = 4000, summary_model: str = "gemini-1.5-flash"):
        """
        Initialize the summarizer.
        
        Args:
            redis_client: Optional Redis client for session persistence.
            max_history_tokens: Threshold above which history is summarized.
            summary_model: The cheaper model used to generate summaries.
        """
        self.redis = redis_client
        self.max_history_tokens = max_history_tokens
        self.summary_model = summary_model
        self.prefix = "thriftllm:summary:"
        
    def _estimate_tokens(self, text: str) -> int:
        """Rough heuristic: 1 token ~= 4 characters."""
        return len(text) // 4
        
    def _get_session_key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"
        
    def get_summary(self, session_id: str) -> Optional[str]:
        """Retrieve the current summary for a session from Redis."""
        if not self.redis:
            return None
        try:
            summary = self.redis.get(self._get_session_key(session_id))
            return summary.decode('utf-8') if summary else None
        except Exception as e:
            logger.warning(f"Failed to retrieve summary from Redis: {e}")
            return None
            
    def save_summary(self, session_id: str, summary: str, ttl: int = 86400):
        """Save the updated summary to Redis with a TTL (default 24h)."""
        if not self.redis:
            return
        try:
            self.redis.setex(self._get_session_key(session_id), ttl, summary)
        except Exception as e:
            logger.warning(f"Failed to save summary to Redis: {e}")

    def process_history(self, session_id: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Analyzes history. If it exceeds the token limit, it generates a new summary
        (or updates the existing one) and returns a truncated history prepended
        with the summary context.
        
        Note: In a full implementation, this would call the `summary_model` via Vertex.
        For this v0.1 iteration, we implement the structural logic and a stub for the LLM call.
        """
        if not history:
            return history
            
        total_chars = sum(len(turn.get("content", "")) for turn in history)
        estimated_tokens = total_chars // 4
        
        if estimated_tokens <= self.max_history_tokens:
            # History is small enough, no summarization needed.
            # We still prepend any existing summary if one exists from previous sessions.
            existing_summary = self.get_summary(session_id)
            if existing_summary:
                return [{"role": "system", "content": f"Previous conversation summary: {existing_summary}"}] + history
            return history
            
        logger.info(f"Session {session_id} history exceeds {self.max_history_tokens} tokens. Summarizing...")
        
        # Keep the last 4 turns (2 user, 2 assistant) intact
        keep_turns = 4
        if len(history) <= keep_turns:
            return history # Can't summarize if it's too short, even if tokens are high
            
        turns_to_summarize = history[:-keep_turns]
        recent_turns = history[-keep_turns:]
        
        existing_summary = self.get_summary(session_id)
        
        # Generate new summary (Stubbed for now, would call Vertex AI)
        new_summary = self._generate_summary_llm_call(existing_summary, turns_to_summarize)
        
        self.save_summary(session_id, new_summary)
        
        # Return the new context: System prompt with summary + recent turns
        optimized_history = [
            {"role": "system", "content": f"Previous conversation summary: {new_summary}"}
        ] + recent_turns
        
        return optimized_history
        
    def _generate_summary_llm_call(self, existing_summary: Optional[str], new_turns: List[Dict[str, str]]) -> str:
        """
        Stub for the actual LLM call to generate the summary.
        In production, this uses self.summary_model (e.g., gemini-1.5-flash) to compress the text.
        """
        # TODO: Implement actual Vertex AI call here.
        # For now, we simulate a summary to allow the pipeline to function.
        turn_texts = [f"{t['role']}: {t.get('content', '')[:50]}..." for t in new_turns]
        combined = " | ".join(turn_texts)
        
        if existing_summary:
            return f"{existing_summary} [Updated with: {combined}]"
        return f"User discussed: {combined}"
