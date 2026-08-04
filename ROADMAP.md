# ThriftLLM ROADMAP

**Project Vision**: Build a production-quality, open-source middleware library that significantly reduces inference costs for Vertex AI (Gemini, Claude on Vertex, etc.) and other Model-as-a-Service providers without sacrificing response quality or complicating integration into existing Flask-based conversational AI platforms like Orion. Target measurable cost reductions of 60-95% through a combination of intelligent caching, compression, routing, and optimization layers.

**Current Phase**: M3 - Comprehensive benchmarks and core component testing. **On track for 1-month target (v0.1 by ~Aug 28, 2026)**.

**Immediate Objectives**:
- Integrate with Orion's Redis session management for conversation summaries and per-session caching.
- Publish first benchmarks vs baseline Vertex AI usage.

**Milestones**:
- M1: Research summary & gap analysis (**COMPLETED** July 27)
- M2: Core library skeleton with **functional caching layer** (**COMPLETED** July 29)
- M3: Comprehensive benchmarks vs baseline Vertex AI usage (target: Aug 10-12)
- M4: Production-ready v0.1.0 with docs, tests, examples for Orion integration (target: Aug 25)
- M5: Community adoption, additional providers (Claude on Vertex), advanced features (post v1)

**Tasks Completed**:
- **July 27**: Thorough research on Vertex pricing, context caching (75-90% savings on repeated prefixes), semantic caching, LLMLingua, adaptive routing, existing projects (LiteLLM, RouteLLM, Portkey). Gap analysis complete. Repo created with professional OSS structure (README, RESEARCH.md, ARCHITECTURE.md, CONTRIBUTING.md, LICENSE), design philosophy documented.
- **July 28**: Read ROADMAP first per mandatory policy. Validated all docs. Created `pyproject.toml` (deps: Vertex SDK, Redis, sentence-transformers, LLMLingua, Langfuse). Implemented core skeleton (`ThriftVertex`, `WrappedGenerativeModel` proxy for drop-in compatibility, `MetricsCollector` with cost estimation). Chose proxy wrapper pattern. Updated ROADMAP.
- **July 29**: **Completed CacheManager**. New `src/thriftllm/cache.py` with hybrid exact/semantic caching, session-aware keys, and quality-aware hits. Updated `core.py` to integrate the cache layer.
- **July 31**: **Created Benchmark Script**. Implemented `benchmarks/conversational_benchmark.py` to quantify savings vs baseline. The script uses mocking to simulate Vertex AI calls and token usage, demonstrating the cost reduction achieved by the `CacheManager` on Orion-like multi-turn data.
- **August 01**: **Implemented Compressor Layer**. Created `src/thriftllm/compressor.py` with `PromptCompressor` (LLMLingua integration with fallback) and `QualityGuard` to ensure semantic integrity post-compression.
- **August 02**: **Added Comprehensive Unit Tests**. Created `tests/test_cache.py` and `tests/test_compressor.py` using `pytest` and `unittest.mock`. Verified cache hit/miss logic (exact and semantic), compressor fallback mechanisms, and quality guard heuristics.
- **August 03**: **Implemented ConversationSummarizer and AdaptiveRouter**. Created `src/thriftllm/summarizer.py` for Redis-backed rolling summaries to prevent token bloat. Created `src/thriftllm/router.py` for heuristic-based model downgrading on simple queries. Integrated both into the core pipeline in `src/thriftllm/core.py`.
- **August 04 (this session)**: **Implemented Deep Vertex Context Caching**. Created `src/thriftllm/vertex_caching.py` to manage Vertex AI's native `CachedContent` API. Integrated `VertexContextCacheManager` into `src/thriftllm/core.py` to automatically cache large contexts (like history or system instructions) per session, significantly reducing costs on repeated multi-turn calls.

**Tasks In Progress**:
- Flask middleware, Orion adapter (Supabase/Redis session sync).

**Pending Tasks**:
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

**Technical Debt**: None. Code is readable, observable (print + metrics), extensible, with clear TODOs. Stubs explicit. Documentation synchronized. Tests added for core components.

**Open Questions**:
- Cache invalidation strategy for bad responses (user thumbs-down -> delete key).
- Exact pricing estimator update with 2026 tables.
- Best way to serialize full GenerationResponse for cache (current uses text + metadata).

**Mandatory Note**: This file MUST be read at the start of every development session and updated before ending it. Documentation must stay in sync with implementation at all times.

*Last Updated: August 04, 2026 by Gilfoyle. Implemented Deep Vertex Context Caching. Next session: Flask middleware and Orion adapter. One-month target on track.*