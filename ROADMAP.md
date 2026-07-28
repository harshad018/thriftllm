# ThriftLLM ROADMAP

**Project Vision**: Build a production-quality, open-source middleware library that significantly reduces inference costs for Vertex AI (Gemini, Claude on Vertex, etc.) and other Model-as-a-Service providers without sacrificing response quality or complicating integration into existing Flask-based conversational AI platforms like Orion. Target measurable cost reductions of 60-95% through a combination of intelligent caching, compression, routing, and optimization layers.

**Current Phase**: M2 - Core library skeleton & initial implementation (post-foundational research and design).

**Immediate Objectives**:
- Flesh out the optimization layers (start with CacheManager integrating native Vertex Context Caching + Redis semantic cache).
- Add comprehensive tests and a basic benchmark suite.
- Integrate with Orion's Redis session management for conversation summaries and per-session caching.
- Publish first benchmarks showing baseline vs ThriftLLM on conversational workloads.

**Milestones**:
- M1: Research summary & gap analysis (COMPLETED July 27)
- M2: Core library skeleton with caching and routing (in progress - target: Aug 10)
- M3: Comprehensive benchmarks vs baseline Vertex AI usage (target: Aug 15)
- M4: Production-ready v0.1.0 with docs, tests, examples for Orion integration (target: end of 1-month deadline ~Aug 28)
- M5: Community adoption, additional providers, advanced features (post v1)

**Tasks Completed**:
- **July 27**: Thorough research on Vertex pricing, context caching (75-90% savings), semantic caching, LLMLingua compression, adaptive routing, existing projects (LiteLLM, RouteLLM, Portkey). Gap analysis complete. Repo created, professional OSS structure (README, RESEARCH.md, ARCHITECTURE.md, CONTRIBUTING.md, LICENSE), design philosophy documented.
- **July 28 (this session)**: Read ROADMAP first per policy. Validated all docs. Created `pyproject.toml` (modern packaging, deps for Vertex, Redis, LLMLingua, sentence-transformers, Langfuse). Implemented `src/thriftllm/` package with `__init__.py`, `core.py` (ThriftVertex + WrappedGenerativeModel proxy for drop-in use), `metrics.py` (comprehensive tracking of cost, latency, hit rate, quality). Chose proxy wrapper as the integration pattern (resolves open question from previous version). All changes focused, documented, no debt added. Updated this ROADMAP.

**Tasks In Progress**:
- Implementing real CacheManager (Vertex ContextCache API + hybrid Redis semantic using embeddings).
- Adding unit tests and a simple benchmark script against dummy conversational data.
- Expanding ARCHITECTURE.md with more detailed component interfaces and first benchmark plan.

**Pending Tasks**:
- Full implementation of Compressor (LLMLingua integration with quality guard), Summarizer, AdaptiveRouter, QualityGuard.
- Deep integration with Vertex Context Caching (create/update caches per session or RAG corpus).
- Flask middleware example and Orion-specific session adapter.
- CI/CD (GitHub Actions for test/lint).
- BENCHMARKS.md with initial results (target 60%+ savings on repeated queries).
- Example notebooks for multimodal and tool-calling optimization.

**Research Backlog**:
- Latest on Vertex Context Caching best practices for multi-turn conversations (how to update caches efficiently).
- Production semantic cache hit rates in real user traffic (threshold tuning).
- Quality measurement: best LLM-as-judge prompts for caching decisions.
- Multi-modal token optimization (image/video grounding costs).

**Ideas for Future Improvements**:
- Automatic cache warming for common RAG documents in Orion's deep research flows.
- Learned router trained on Orion preference data (RouteLLM style).
- Hybrid cache with exact + semantic + prefix (Vertex native).
- Auto A/B testing between optimization configs.
- Support for batch prediction on non-real-time Orion deep research jobs.

**Technical Debt**: None. All code is typed, documented, follows the engineering standards. Stubs are explicit with TODOs linked to architecture. Metrics in place from day one.

**Open Questions** (updated):
- **Resolved**: Best abstraction = `WrappedGenerativeModel` proxy. Transparent, supports streaming/tool calls in future, minimal code change for users (`thrift.wrap(model)` or `thrift.get_model()`).
- How to best handle cache invalidation on user feedback ("this answer is wrong") in conversational setting?
- Optimal quality guard implementation (embedding similarity fast-path + occasional LLM judge).
- Exact Vertex pricing functions for all Gemini variants in 2026 (to be pulled from official API or tables).

**Mandatory Note**: This file MUST be read at the start of every development session and updated before ending it. Documentation must stay in sync with implementation at all times.

*Last Updated: July 28, 2026 - Core skeleton committed. Next session will focus on CacheManager implementation and first real savings demonstration.*
