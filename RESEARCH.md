# Research Findings & Gap Analysis

## Vertex AI Cost Model (as of July 2026)

- Pricing is primarily token-based with different rates for input, cached input, output, and different model tiers (Flash vs Pro).
- Gemini models on Vertex support **Context Caching** — a powerful feature that significantly discounts repeated prompt prefixes (often 75-90% cheaper).
- Claude models available via Vertex have their own pricing and limited caching support.
- Additional costs for batch prediction, agents, grounding, etc.
- Hidden costs: long context, repeated history in conversations, large RAG contexts, tool outputs, image/PDF tokens.

Majority of cost in conversational apps like Orion comes from:
1. Repeated conversation history in every turn.
2. Similar user queries across sessions.
3. Large retrieved contexts.
4. Over-use of expensive models for trivial tasks.
5. Uncompressed tool responses and web scrape results.

## Key Techniques Researched

1. **Prompt & Context Caching** — Highest ROI. Native in many providers. Middleware can intelligently manage keys for multi-turn conversations.
2. **Semantic Caching** — Use embeddings to detect near-duplicate queries and serve cached responses. See arXiv:2508.07675.
3. **Context Compression** — LLMLingua, selective summarization. 5-20x token reduction possible.
4. **Conversation Summarization** — Maintain a rolling summary instead of full history.
5. **Adaptive Model Routing** — Complexity detection to route to cheaper models (inspired by RouteLLM, NotDiamond).
6. **Response Caching & Deduplication** — Exact match or fuzzy.
7. **Tool & Agent Optimization** — Compress tool outputs, reduce unnecessary calls via planning.
8. **Batching** — For non-real-time parts of deep research.
9. **Speculative Decoding / KV Optimization** — More relevant for self-hosted; less for pure MaaS but can inform design.

## Existing Open-Source Projects

- **LiteLLM**: Broad proxy with fallback, routing, basic caching. Very useful but general-purpose; not deeply optimized for conversational state or Vertex-specific features.
- **Portkey AI Gateway**: Comprehensive gateway with caching, guardrails. Acquired; still open-source but broader scope.
- **RouteLLM**: Focused on routing with preference data.
- **LLMLingua**: Excellent prompt compression.
- **Langfuse / Helicone**: Observability with cost tracking.
- Many academic prototypes and KV-cache tools (vLLM ecosystem).

**Key Gaps This Project Addresses**:

- No existing library provides an **opinionated, integrated stack** specifically tuned for **long-running conversational AI** on **Vertex AI** with tight integration to Redis session stores and Supabase.
- Lack of **combined** semantic + context caching with automatic conversation summarization and quality-aware routing.
- Few projects publish rigorous **benchmarks** on real conversational workloads (cost, latency, quality metrics).
- Opportunity to create a **clean middleware** that can wrap `vertexai` clients with almost zero code change while applying multiple layers transparently.
- Focus on **maintainability, observability, and extensibility** rather than being another massive gateway.

This project will synthesize the best ideas from the landscape into a focused, high-leverage library. We will implement, benchmark, document, and iterate based on real Orion usage patterns.

See `ROADMAP.md` for current priorities and `ARCHITECTURE.md` (forthcoming) for design decisions.

*Research conducted July 27, 2026. Will be updated as new papers and provider features emerge.*
