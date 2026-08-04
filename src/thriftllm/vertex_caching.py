import time
from typing import Optional, Dict, Any, List

# Try to import Vertex AI caching, fallback to mock for testing/stubbing if not available
try:
    from vertexai.preview.generative_models import CachedContent
    VERTEX_CACHING_AVAILABLE = True
except ImportError:
    VERTEX_CACHING_AVAILABLE = False
    class CachedContent:
        @classmethod
        def create(cls, *args, **kwargs):
            return type("MockCachedContent", (), {"name": "mock-cache-123", "update": lambda *a, **kw: None, "delete": lambda *a, **kw: None})()
        
        def __init__(self, name=None):
            self.name = name

class VertexContextCacheManager:
    """
    Manages Vertex AI native context caching (Explicit Caching).
    Useful for large static contexts (>32k tokens) to reduce costs on repeated calls.
    """
    def __init__(self, config: Any = None):
        self.config = config
        self.active_caches: Dict[str, Any] = {} # session_id -> CachedContent
        self.min_tokens_for_cache = 32768 # Vertex AI typically requires a minimum token count for caching

    def get_or_create_cache(self, session_id: str, model_name: str, system_instruction: Optional[str] = None, contents: Optional[List[Any]] = None, ttl_minutes: int = 60) -> Optional[str]:
        """
        Retrieves an existing cache for the session or creates a new one if conditions are met.
        Returns the cache name if successful, None otherwise.
        """
        if not VERTEX_CACHING_AVAILABLE:
            print("[ThriftLLM] Vertex AI CachedContent API not available in this SDK version.")
            return None

        if session_id in self.active_caches:
            print(f"[ThriftLLM] Using existing Vertex Context Cache for session: {session_id}")
            return self.active_caches[session_id].name

        try:
            print(f"[ThriftLLM] Creating new Vertex Context Cache for session: {session_id}")
            cache = CachedContent.create(
                model_name=model_name,
                system_instruction=system_instruction,
                contents=contents,
                ttl=f"{ttl_minutes}m"
            )
            self.active_caches[session_id] = cache
            return cache.name
        except Exception as e:
            print(f"[ThriftLLM] Failed to create Vertex Context Cache: {e}")
            return None

    def delete_cache(self, session_id: str):
        """Deletes a cache associated with a session."""
        if session_id in self.active_caches:
            try:
                self.active_caches[session_id].delete()
                del self.active_caches[session_id]
                print(f"[ThriftLLM] Deleted Vertex Context Cache for session: {session_id}")
            except Exception as e:
                print(f"[ThriftLLM] Error deleting cache for {session_id}: {e}")
