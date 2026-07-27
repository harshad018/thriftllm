# ARCHITECTURE.md

## High-Level Design

ThriftLLM is a **middleware layer** that sits between your application code and the Vertex AI SDK. It intercepts calls, applies multiple cost-reduction layers transparently, and returns results while tracking metrics.

### Core Principles

- **Layered Optimizations**: Each optimization is a composable component with clear interfaces.
- **Quality First**: Every caching/routing decision includes a confidence score. Low confidence falls back to full inference.
- **State Awareness**: Leverages existing Redis session management for conversation summaries, cache keys, and user preferences.
- **Observability**: All decisions logged with costs saved, hit rates, quality scores. Pluggable to Langfuse, Helicone, or custom.
- **Minimal API Impact**: Primary interface is a wrapper around `GenerativeModel` or a context manager/patch.

### Proposed Components

1. **CacheManager**
   - Hybrid cache: exact (Redis), semantic (vector store), Vertex Context Cache (for long prefixes).
   - Key generation based on conversation ID, user ID, summarized history, query embedding.

2. **ContextCompressor**
   - Uses LLMLingua or similar for prompt compression.
   - Specialized compressors for tool outputs, web results, RAG chunks.
   - Maintains quality metrics.

3. **ConversationSummarizer**
   - Periodically (or on token threshold) summarizes history.
   - Stores summary in Redis/Supabase alongside full history.
   - Used to reduce context in subsequent calls.

4. **AdaptiveRouter**
   - Analyzes query complexity, history length, previous performance.
   - Routes to cheapest sufficient model (Flash vs Pro, etc.).
   - Can use lightweight classifier or small LLM call (amortized).

5. **QualityGuard**
   - For cached responses: embedding similarity or small LLM judge to validate relevance.
   - Threshold configurable.

6. **MetricsCollector**
   - Tracks tokens in/out, cache hits, estimated savings, latency.
   - Exports to Prometheus, Langfuse, etc.

### Integration Patterns

- **Wrapper mode**: `thrift_client.wrap(vertex_model)`
- **Middleware mode**: For Flask routes.
- **Async support**: Full async compatibility.

### Data Flow (Typical Request)

1. Incoming prompt + history.
2. Summarizer provides compressed history if beneficial.
3. Compressor reduces prompt size.
4. Cache check (semantic + exact + context cache).
5. If miss: Router selects model → Call Vertex → Store in cache.
6. Quality check on cached result.
7. Return response + metrics.

### Trade-off Decisions (Documented Here for Future Reference)

- **Semantic Cache Backend**: Start with simple Redis + embeddings (sentence-transformers or Vertex embedding API). Later add more advanced vector DB if needed. Tradeoff: speed vs accuracy.
- **Compression Strategy**: Prefer lossless where possible; fall back to aggressive only with quality guard.
- **Router Training**: Initially rule-based + heuristics. Future: collect preference data for RouteLLM-style training.
- **Privacy**: Cache keys should be per-user or per-org by default. Configurable TTLs and opt-out.

This document will evolve. Major changes will be recorded with rationale and benchmark impact.

See `ROADMAP.md` for implementation order.

*Drafted during initial research phase — July 27, 2026*
