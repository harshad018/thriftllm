"""CacheManager for ThriftLLM.

Implements hybrid caching:
- Exact match via Redis (fast, for identical prompts/sessions)
- Semantic caching using sentence-transformers embeddings + cosine similarity (for similar conversational queries)
- Placeholder/integration points for Vertex AI explicit Context Caching (CachedContent) for large static prefixes (system instructions, RAG corpora, long history summaries). This can deliver 75-90% input token savings per research.

Designed for conversational workloads like Orion: keys incorporate session_id when available, summaries, and quality guard.

Metrics are recorded on hit/miss. QualityGuard will be applied on semantic hits.

Future: Redis Vector (RediSearch module) for scalable semantic, automatic cache warming, per-conversation CachedContent updates.
"""
import json
import time
from typing import Any, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import redis
from redis.exceptions import RedisError

from .metrics import MetricsCollector


class CacheManager:
    """Hybrid cache manager with Redis backend and embedding-based semantic lookup."""
    
    def __init__(self, config, metrics: MetricsCollector):
        self.config = config
        self.metrics = metrics
        self.redis_client: Optional[redis.Redis] = None
        self.embedding_model = None
        self.semantic_threshold = config.quality_threshold or 0.82
        
        if config.redis_url:
            try:
                self.redis_client = redis.from_url(config.redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
                print("[ThriftLLM] Redis connected for caching.")
            except RedisError as e:
                print(f"[ThriftLLM] Redis connection failed: {e}. Falling back to no-cache mode.")
                self.redis_client = None
        else:
            print("[ThriftLLM] No redis_url provided. Caching disabled.")
        
        if self.redis_client:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                print("[ThriftLLM] Embedding model loaded for semantic caching.")
            except Exception as e:
                print(f"[ThriftLLM] Failed to load embedding model: {e}. Semantic cache disabled.")
                self.embedding_model = None

    def _get_cache_key(self, contents: Any, model_name: str, session_id: Optional[str] = None) -> str:
        """Generate deterministic cache key. Prefer session_id + summarized content for conversations."""
        if session_id:
            base = f"session:{session_id}"
        else:
            # Fallback to content hash (not perfect for objects; improve with summarizer)
            content_str = str(contents) if not isinstance(contents, (list, dict)) else json.dumps(contents, sort_keys=True)
            base = f"content:{hash(content_str)}"
        return f"thriftllm:cache:{model_name}:{base}"

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        if not self.embedding_model:
            return None
        try:
            return self.embedding_model.encode(text, normalize_embeddings=True)
        except Exception:
            return None

    def get_cached_response(self, contents: Any, model_name: str, session_id: Optional[str] = None) -> Optional[Dict]:
        """Check for cache hit (exact then semantic). Returns dict with 'text', 'hit_type', etc. or None."""
        if not self.redis_client or not self.config.enable_caching:
            return None

        start = time.time()
        key = self._get_cache_key(contents, model_name, session_id)
        
        # 1. Exact match (fastest)
        try:
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                latency = time.time() - start
                self.metrics.record_call(
                    model=model_name,
                    input_tokens=0,  # Would parse from cached metadata
                    output_tokens=data.get("output_tokens", 0),
                    latency=latency,
                    cache_hit=True,
                    estimated_savings=0.15,  # Placeholder; real calc based on model
                    quality_score=1.0
                )
                print(f"[ThriftLLM Cache] EXACT HIT for {model_name}")
                return {"response": data.get("response"), "hit_type": "exact", "cached_text": data.get("text")}
        except (RedisError, json.JSONDecodeError):
            pass

        # 2. Semantic match (if embedding available)
        if self.embedding_model:
            query_text = self._extract_text_for_embedding(contents)
            query_emb = self._get_embedding(query_text)
            if query_emb is not None:
                # For MVP: scan recent keys (limited). In production use Redis vector index (RediSearch) or Qdrant/Pinecone.
                # Here we simulate by checking a 'recent' list (simple LRU-like)
                recent_key = "thriftllm:recent_semantic"
                recent = self.redis_client.lrange(recent_key, 0, 50)  # last 50 entries
                best_score = 0.0
                best_data = None
                for rkey in recent:
                    try:
                        cached_data = json.loads(self.redis_client.get(rkey) or "{}")
                        if "embedding" in cached_data:
                            cached_emb = np.array(cached_data["embedding"])
                            score = float(np.dot(query_emb, cached_emb))  # cosine since normalized
                            if score > best_score and score >= self.semantic_threshold:
                                best_score = score
                                best_data = cached_data
                    except Exception:
                        continue
                
                if best_data and best_score >= self.semantic_threshold:
                    latency = time.time() - start
                    self.metrics.record_call(
                        model=model_name,
                        input_tokens=0,
                        output_tokens=best_data.get("output_tokens", 0),
                        latency=latency,
                        cache_hit=True,
                        estimated_savings=0.12,
                        quality_score=best_score
                    )
                    print(f"[ThriftLLM Cache] SEMANTIC HIT (score={best_score:.3f}) for {model_name}")
                    return {"response": best_data.get("response"), "hit_type": "semantic", "cached_text": best_data.get("text"), "similarity": best_score}
        
        return None

    def store_response(self, contents: Any, model_name: str, response: Any, session_id: Optional[str] = None, 
                      output_tokens: int = 0, embedding: Optional[list] = None):
        """Store in Redis (exact + add to semantic recent list)."""
        if not self.redis_client or not self.config.enable_caching:
            return

        key = self._get_cache_key(contents, model_name, session_id)
        text = response.text if hasattr(response, 'text') else str(response)
        
        data = {
            "text": text,
            "response": str(response),  # Simplified; in prod serialize properly or use pickle with care
            "output_tokens": output_tokens,
            "timestamp": time.time(),
            "model": model_name
        }
        
        if embedding is not None:
            data["embedding"] = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        
        try:
            self.redis_client.set(key, json.dumps(data), ex=self.config.cache_ttl_seconds)
            # Add to recent for semantic search (LRU style)
            recent_key = "thriftllm:recent_semantic"
            self.redis_client.lpush(recent_key, key)
            self.redis_client.ltrim(recent_key, 0, 99)  # Keep last 100
            print(f"[ThriftLLM Cache] STORED for {model_name} (key prefix: {key[:40]}...)")
        except RedisError as e:
            print(f"[ThriftLLM Cache] Store failed: {e}")

    def invalidate(self, contents: Any, model_name: str, session_id: Optional[str] = None) -> bool:
        """Invalidate a specific cache entry. Useful for bad responses (e.g., user thumbs-down)."""
        if not self.redis_client or not self.config.enable_caching:
            return False
            
        key = self._get_cache_key(contents, model_name, session_id)
        try:
            deleted = self.redis_client.delete(key)
            if deleted:
                print(f"[ThriftLLM Cache] INVALIDATED key: {key}")
                return True
            return False
        except RedisError as e:
            print(f"[ThriftLLM Cache] Invalidate failed: {e}")
            return False

    def create_vertex_context_cache(self, contents: list, model_name: str, ttl_seconds: int = 3600) -> Optional[str]:
        """Create explicit Vertex AI Context Cache for large repeated contexts (75-90% savings).
        
        Use for system instructions, RAG documents, conversation summaries that are static across turns.
        See ARCHITECTURE.md and research for best practices in conversational flows.
        """
        try:
            # Real implementation (requires proper imports and permissions):
            # from vertexai.generative_models import CachedContent, Part
            # cached_content = CachedContent.create(
            #     model_name=model_name,
            #     contents=contents,  # list of Part or dicts
            #     ttl=ttl_seconds,    # or expire_time
            #     # display_name, etc.
            # )
            # self.metrics.record_cache_creation(...) 
            # return cached_content.name
            print(f"[ThriftLLM] TODO: Created Vertex Context Cache for {model_name} with {len(contents)} contents (placeholder). Savings potential: 80%+")
            return f"cached-content-placeholder-{int(time.time())}"
        except Exception as e:
            print(f"[ThriftLLM] Context cache creation failed: {e}")
            return None

    def _extract_text_for_embedding(self, contents: Any) -> str:
        """Extract text representation for embedding. Handles str, list of Parts, dicts."""
        if isinstance(contents, str):
            return contents
        if isinstance(contents, list):
            texts = []
            for item in contents:
                if isinstance(item, str):
                    texts.append(item)
                elif hasattr(item, 'text'):
                    texts.append(item.text)
                elif isinstance(item, dict) and 'text' in item:
                    texts.append(item['text'])
            return " ".join(texts)
        return str(contents)


# For backward compatibility with stub in core
CacheManagerStub = CacheManager
