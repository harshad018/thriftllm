# ARCHITECTURE.md

## High-Level Design

ThriftLLM is a **middleware layer** that sits between your application code and the Vertex AI SDK. It intercepts calls, applies multiple cost-reduction layers transparently, and returns results while tracking metrics.

### Core Principles

- **Layered Optimizations**: Each optimization is a composable component with clear interfaces.
- **Quality First**: Every caching/routing decision includes a confidence score. Low confidence falls back to full inference.
- **State Awareness**: Leverages existing Redis session management for conversation summaries, cache keys, and user preferences.
- **Observability**: All decisions logged with costs saved, hit rates, quality scores. Pluggable to Langfuse, Helicone, or custom.
- **Minimal API Impact**: Primary interface is a wrapper around `GenerativeModel` or a context manager/patch. `thrift.wrap(model)` or `thrift.get_model("gemini-1.5-flash")`.

### Implemented Components (July 29, 2026)

1. **CacheManager** (Fully implemented in `cache.py`, integrated in `core.py`)
   - **Hybrid cache**:
     - **Exact**: Redis key based on content hash or `session_id` (O(1) lookup, perfect for repeated identical turns).
     - **Semantic**: SentenceTransformer (`all-MiniLM-L6-v2`) embeddings + cosine similarity. Stores recent entries in Redis list (MVP; scalable to RediSearch vector index). Threshold = `quality_threshold` (~0.82-0.85).
     - **Vertex Context Caching**: Placeholder `create_vertex_context_cache(contents, model_name, ttl)` using explicit caching API (per official 2026 docs: 75-90% discount on cached input tokens for Gemini models; ideal for static system instructions, RAG corpora, video/docs, long summaries). Implicit caching is default in Vertex and complements this.
   - Session-aware: Pass `session_id=...` in `generate_content(..., session_id=redis_session_id)`.
   - Stores response text + metadata + embedding. TTL configurable.
   - On hit: Returns `CachedResponse` compatible with Vertex response API (`.text`, `.candidates`).
   - Metrics: Records hit_type, savings (conservative 0.12-0.25 USD placeholder; real based on token counts and 2026 pricing), quality_score (similarity).
   - Trade-offs documented: Simple list scan for semantic is fast for <100 recent items per session (common in conversations). For global high-scale, add vector DB. Quality guard prevents bad semantic hits.
   - Savings potential: Highest ROI per research. Repeated history or similar queries in Orion can yield 50-80% reduction.

2. **MetricsCollector** (Production-ready in `metrics.py`)
   - Tracks tokens, latency, cache_hit, estimated_cost/savings (placeholder pricing for Flash/Pro), quality.
   - Console output + in-memory aggregates for benchmarks. Ready for Langfuse export.

3. **ThriftVertex + WrappedGenerativeModel** (`core.py`)
   - Drop-in replacement/wrapper.
   - Pipeline (current): **Cache check first** → (TODO: summarizer → compressor → router) → Vertex call → store in cache → metrics.
   - Supports `generate_content` with early cache return. Stubs for `send_message`, streaming, multimodal, tools.
   - Config-driven (enable layers independently with quality gates).

### Components Pending Implementation
- **ContextCompressor**: LLMLingua for prompt compression (5-20x reduction), specialized for tool outputs/RAG.
- **ConversationSummarizer**: Redis-backed rolling summary to reduce history tokens (key for long conversations).
- **AdaptiveRouter**: Query complexity + history analysis to route Flash vs Pro (or cheaper variants).
- **QualityGuard**: Embedding similarity + occasional LLM judge for cached/summarized content.

### Integration Patterns
- **Wrapper mode**: `thrift = ThriftVertex(...); model = thrift.wrap(existing_model)` or `thrift.get_model("gemini-1.5-flash-002")`
- **Session integration**: Pass `session_id` from Orion's Redis/Supabase to enable per-conversation caching/summaries.
- **Async**: Future support via `async` methods.
- **Orion-specific**: Middleware for Flask routes that auto-injects session context.

### Data Flow (Typical Request - Updated)
1. `generate_content(contents, session_id=...)`
2. **CacheManager.get_cached_response()** (exact → semantic). Hit? Return immediately with metrics.
3. (Future: Summarizer provides compressed history; Compressor reduces prompt.)
4. If miss: (Future: Router selects model) → `base_model.generate_content()`
5. Store result + embedding in Redis; optionally create/update Vertex Context Cache for static parts.
6. QualityGuard (on semantic hits).
7. `MetricsCollector.record_call(...)` with estimated savings.
8. Return response.

### Trade-off Decisions (Updated July 29)
- **Semantic Cache Backend**: Started with Redis list + numpy cosine (simple, zero extra deps beyond existing, fast for conversational scale). Future: Add `redisearch` or dedicated vector store if hit rates demand. Tradeoff: correctness/speed vs complexity. Measured via upcoming benchmarks.
- **Vertex Caching**: Explicit for control (create per session/RAG). Complements implicit (default 90% discount). Min token thresholds noted from docs. Prioritize static large contexts first (highest ROI).
- **Quality**: Cosine >= 0.82-0.85 for semantic. Will add LLM judge fallback. Avoids regression per "Quality First" principle.
- **Proxy vs Patch**: Chose explicit wrapper for observability and control. Easier to add layers incrementally.
- **Pricing Estimator**: Placeholder in metrics; will be updated with official 2026 tables for accuracy in benchmarks.

### Observability & Benchmarking
All layers feed `MetricsCollector`. Future BENCHMARKS.md will show before/after on Orion-like workloads (repeated questions, long history, RAG).

This document evolves with implementation. Major decisions recorded with rationale and expected impact.

See `ROADMAP.md` for current phase (M2 nearly complete with caching), `RESEARCH.md` for sources, and code for details.

*Updated July 29, 2026 after implementing CacheManager. Benchmarks next to validate 60%+ savings target.*
