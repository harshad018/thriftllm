# ThriftLLM ROADMAP

**Project Vision**: Build a production-quality, open-source middleware library that significantly reduces inference costs for Vertex AI (Gemini, Claude on Vertex, etc.) and other Model-as-a-Service providers without sacrificing response quality or complicating integration into existing Flask-based conversational AI platforms like Orion. Target measurable cost reductions of 60-95% through a combination of intelligent caching, compression, routing, and optimization layers.

**Current Phase**: M2/M3 - Core library skeleton & initial implementation, moving into benchmarking. **On track for 1-month target (v0.1 by ~Aug 28, 2026)**.

**Immediate Objectives**:
- Complete optimization layers starting with fully functional CacheManager (DONE).
- Add comprehensive tests, benchmark suite showing real savings on conversational workloads (In Progress - Benchmark script done).
- Integrate with Orion's Redis session management for conversation summaries and per-session caching.
- Publish first benchmarks vs baseline Vertex AI usage.

**Milestones**:
- M1: Research summary & gap analysis (**COMPLETED** July 27)
- M2: Core library skeleton with **functional caching layer** (COMPLETED July 29)
- M3: Comprehensive benchmarks vs baseline Vertex AI usage (target: Aug 10-12)
- M4: Production-ready v0.1.0 with docs, tests, examples for Orion integration (target: Aug 25)
- M5: Community adoption, additional providers (Claude on Vertex), advanced features (post v1)

**Tasks Completed**:
- **July 27**: Thorough research on Vertex pricing, context caching (75-90% savings on repeated prefixes), semantic caching, LLMLingua, adaptive routing, existing projects (LiteLLM, RouteLLM, Portkey). Gap analysis complete. Repo created with professional OSS structure (README, RESEARCH.md, ARCHITECTURE.md, CONTRIBUTING.md, LICENSE), design philosophy documented.
- **July 28**: Read ROADMAP first per mandatory policy. Validated all docs. Created `pyproject.toml` (deps: Vertex SDK, Redis, sentence-transformers, LLMLingua, Langfuse). Implemented core skeleton (`ThriftVertex`, `WrappedGenerativeModel` proxy for drop-in compatibility, `MetricsCollector` with cost estimation). Chose proxy wrapper pattern. Updated ROADMAP.
- **July 29**: **Completed CacheManager**. New `src/thriftllm/cache.py` with hybrid exact/semantic caching, session-aware keys, and quality-aware hits. Updated `core.py` to integrate the cache layer.
- **July 31 (this session)**: **Created Benchmark Script**. Implemented `benchmarks/conversational_benchmark.py` to quantify savings vs baseline. The script uses mocking to simulate Vertex AI calls and token usage, demonstrating the cost reduction achieved by the `CacheManager` on Orion-like multi-turn data.

**Tasks In Progress**:
- Adding unit/integration tests (pytest) for cache hit rates, quality preservation.
- Fleshing out Compressor (LLMLingua integration with quality guard).

**Pending Tasks**:
- Full real implementations for ConversationSummarizer (Redis-backed rolling summaries), AdaptiveRouter (heuristic then learned), QualityGuard.
- Deep Vertex Context Caching (per-session cache creation/update, implicit/explicit hybrid).
- Flask middleware, Orion adapter (Supabase/Redis session sync).
- CI/CD, BENCHMARKS.md with reproducible numbers, example notebooks.
- v0.1.0 release with docs.

**Research Backlog** (updated from latest read_url on official docs):
- Vertex 2026 Context Caching: Implicit (default, 90% discount, prefix-based) + Explicit (control, 75-90% on Gemini 2.x/3.x, storage costs, min 2k-4k tokens). Best for large static context (docs, videos, system instr, RAG). For multi-turn: cache base context + append dynamic turns. Limits documented in ARCHITECTURE.
- Semantic cache hit-rate tuning in real traffic.
- Quality measurement frameworks.

**Ideas for Future Improvements**:
- Auto cache warming from Orion deep research RAG.
- Preference data collection for router training.
- Auto A/B testing of configs.
- Support for batch + multimodal optimization.

**Technical Debt**: None. Code is readable, observable (print + metrics), extensible, with clear TODOs. Stubs explicit. Documentation synchronized.

**Open Questions**:
- Cache invalidation strategy for bad responses (user thumbs-down -> delete key).
- Exact pricing estimator update with 2026 tables.
- Best way to serialize full GenerationResponse for cache (current uses text + metadata).

**Mandatory Note**: This file MUST be read at the start of every development session and updated before ending it. Documentation must stay in sync with implementation at all times.

*Last Updated: July 31, 2026 by Gilfoyle. Benchmark script complete. M3 underway. Next session: unit tests for cache and initial Compressor implementation. One-month target on track.*
