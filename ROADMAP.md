# ThriftLLM ROADMAP

**Project Vision**: Build a production-quality, open-source middleware library that significantly reduces inference costs for Vertex AI (Gemini, Claude on Vertex, etc.) and other Model-as-a-Service providers without sacrificing response quality or complicating integration into existing Flask-based conversational AI platforms like Orion. Target measurable cost reductions of 60-95% through a combination of intelligent caching, compression, routing, and optimization layers.

**Current Phase**: M3 - Comprehensive benchmarks and core component testing. **On track for 1-month target (v0.1 by ~Aug 28, 2026)**.

**Immediate Objectives**:
- Publish first benchmarks vs baseline Vertex AI usage.
- Setup CI/CD pipeline for automated testing.

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
- **August 04**: **Implemented Deep Vertex Context Caching**. Created `src/thriftllm/vertex_caching.py` to manage Vertex AI's native `CachedContent` API. Integrated `VertexContextCacheManager` into `src/thriftllm/core.py` to automatically cache large contexts (like history or system instructions) per session, significantly reducing costs on repeated multi-turn calls.
- **August 05**: **Implemented Flask Middleware and Orion Adapter**. Created `src/thriftllm/adapter.py` containing `OrionAdapter` for Redis/Supabase session synchronization and `thrift_route` decorator for seamless Flask endpoint wrapping. Updated `__init__.py` to expose these integration tools.
- **August 06**: **Added Benchmarks**. Created `BENCHMARKS.md` detailing simulated cost reductions (up to 82%) across different scenarios. Attempted CI/CD setup but blocked by GitHub token permissions.
- **August 08 (this session)**: **Created Orion Integration Example**. Added `examples/orion_integration_example.py` to demonstrate how to use the `OrionAdapter` and `thrift_route` decorator within a Flask application. This fulfills the requirement for integration examples.

**Tasks In Progress**:
- v0.1.0 release with finalized docs.

**Pending Tasks**:
- CI/CD pipeline setup (Blocked: Requires GitHub token with `workflow` scope to create `.github/workflows/` files).

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

*Last Updated: August 08, 2026 by Gilfoyle. Created Orion integration example. Next session: Finalize docs and prepare for v0.1.0 release. One-month target on track.*