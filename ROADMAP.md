# ThriftLLM ROADMAP

**Project Vision**: Build a production-quality, open-source middleware library that significantly reduces inference costs for Vertex AI (Gemini, Claude on Vertex, etc.) and other Model-as-a-Service providers without sacrificing response quality or complicating integration into existing Flask-based conversational AI platforms like Orion. Target measurable cost reductions of 60-95% through a combination of intelligent caching, compression, routing, and optimization layers.

**Current Phase**: Phase 1-4 (Research, Repository Initialization, Documentation, Roadmap). This is the foundational session. No code written yet — deliberate research-first approach.

**Immediate Objectives**:
- Complete thorough research on Vertex AI pricing, existing cost-optimization techniques, academic papers, and open-source projects.
- Identify unique gaps for a Vertex-AI-first middleware (especially for conversational, tool-calling, long-context, multi-modal, RAG-heavy workloads in Orion).
- Establish professional repo structure, core docs, and this ROADMAP.
- Design initial architecture based on evidence.

**Milestones**:
- M1: Research summary & gap analysis (this session)
- M2: Core library skeleton with caching and routing (target: 2 weeks)
- M3: Comprehensive benchmarks vs baseline Vertex AI usage (target: 3 weeks)
- M4: Production-ready v0.1.0 with docs, tests, examples for Orion integration (target: end of 1-month deadline)
- M5: Community adoption, additional providers, advanced features (post v1)

**Tasks Completed** (this session):
- Activated research and GitHub skills.
- Researched Vertex AI pricing, prompt/semantic caching, context compression, model routing, speculative decoding, academic papers, and open-source projects (awesome-llm-token-optimization, LiteLLM, Portkey, RouteLLM, LLMLingua, LMCache, etc.).
- Created GitHub repo `harshad018/thriftllm` (public).
- Initialized core files: README.md, ROADMAP.md, LICENSE, CONTRIBUTING.md, docs/, etc. (in progress via commits).
- Documented initial research findings and gaps.

**Tasks In Progress**:
- Finalizing research documentation and gap analysis.
- Populating full repository structure with professional open-source boilerplate.
- Drafting architecture design document.

**Pending Tasks**:
- Deep-dive into specific Vertex AI features (Context Caching API, Batch Prediction, model-specific pricing for Gemini 2.5, Claude 3.5/4 on Vertex).
- Benchmark existing techniques in context of Orion's workload (conversational, web search, deep research, tool calling, PDFs/images).
- Implement core components: semantic cache, prompt compressor, adaptive router, conversation summarizer.
- Integration examples for Flask + Vertex AI.
- Comprehensive test suite and CI/CD.
- Performance benchmarks showing cost/latency/quality tradeoffs.

**Research Backlog**:
- Latest papers on semantic caching (arXiv 2508.07675), KV cache compression, speculative decoding for serving.
- Production case studies from Helicone, Langfuse, Portkey, LiteLLM on real cost savings.
- Multi-modal and RAG-specific optimizations (image/PDF token reduction).
- Agent/tool-call optimization (reduce unnecessary tool calls via planning/summarization).
- Request deduplication and batching for non-real-time queries in Orion.

**Ideas for Future Improvements**:
- Automatic conversation summarization with quality gates.
- Hybrid cache (semantic + exact + prompt prefix).
- Learned router using preference data (inspired by RouteLLM).
- Integration with vLLM/SGLang for self-hosted fallback.
- Observability hooks for Langfuse/Helicone.
- Support for more providers (OpenAI, Anthropic direct, Groq, etc.) while prioritizing Vertex.
- Auto A/B testing framework for optimizations.

**Technical Debt**: None yet (starting from scratch). Will track any shortcuts taken under time pressure of 1-month deadline.

**Open Questions**:
- What is the best abstraction for easy drop-in replacement in existing Vertex AI client code? (decorator? proxy? patched client? middleware class?)
- How to measure "response quality" rigorously for caching/routing decisions (e.g., LLM-as-judge, ROUGE, human eval proxies)?
- Balance between cache hit rate, freshness, and privacy (especially for user conversations in Orion).
- Should we include speculative decoding or focus on API-level optimizations only?

**Mandatory Note**: This file MUST be read at the start of every development session and updated before ending it. Documentation must stay in sync with implementation at all times.

*Last Updated: July 27, 2026*
