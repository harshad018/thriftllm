# ThriftLLM

**Drastically reduce Vertex AI inference costs for conversational AI applications.**

Production-grade middleware that intelligently applies prompt/context caching, semantic caching, adaptive model routing, context compression, conversation summarization, and other optimizations. Designed for seamless drop-in use in Flask backends like [Orion](https://github.com/harshad018/Orion) while preserving (or improving) response quality.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
![GitHub last commit](https://img.shields.io/github/last-commit/harshad018/thriftllm)

## Problem Statement

Running production conversational AI on Vertex AI (Gemini, Claude via Vertex, etc.) is expensive. Long conversation histories, repeated tool calls, RAG contexts, web search results, and multimodal inputs cause token usage to explode. Naive implementations can cost thousands per month even at moderate scale. Existing general-purpose proxies help but lack deep, opinionated optimizations tailored to long-running, stateful, agentic conversational workloads.

## Project Goals

- **Measurable cost reduction**: Target 60-90%+ savings on Vertex AI spend through layered optimizations.
- **Zero quality degradation**: Use quality gates, LLM-as-judge where appropriate, and fallback mechanisms.
- **Easy integration**: Drop-in replacement or middleware for existing `vertexai` client code. Minimal configuration.
- **Production ready**: Observability, monitoring, caching persistence (Redis), error handling, retries, testing, benchmarks.
- **Focused on real workloads**: Optimized for chat, deep research, tool use, RAG, PDFs/images, session memory — exactly like Orion.
- **Open source excellence**: Clean code, comprehensive docs, tests, CI/CD, ROADMAP, contribution guidelines.

## Research Findings (Summary)

From extensive research (July 2026):

- **Vertex AI Pricing**: Token-based (input/output differentiated). Gemini Flash variants are significantly cheaper than Pro. Context Caching (for Gemini) provides major discounts on repeated prefix tokens (often 75-90% off). Batch prediction offers further discounts.
- **Prompt/Context Caching**: Highest impact (up to 90% on input tokens). Providers now support it natively; middleware can manage cache keys intelligently for conversations.
- **Semantic Caching**: Vector similarity on query embeddings + response reuse. Excellent for similar user intents. Papers like "Semantic Caching for Low-Cost LLM Serving" (arXiv:2508.07675) show strong results.
- **Context Compression**: Tools like LLMLingua achieve 5-20x reduction with acceptable quality loss. Critical for long histories.
- **Conversation Summarization**: Keep running summaries of history to bound context size.
- **Adaptive Model Routing**: Route simple queries to Flash/Lite models, complex reasoning to Pro. Libraries like RouteLLM and LiteLLM provide foundations; we add session/context awareness.
- **Other**: Response caching, request deduplication, tool output compression, batching for non-urgent work, prompt engineering for brevity.
- **Open Source Landscape**: LiteLLM (proxy with caching/routing), Portkey (gateway), awesome-llm-token-optimization list, LLMLingua, vLLM ecosystem. **Gap**: No focused, high-quality middleware specifically for Vertex AI conversational patterns with built-in summarization, Orion-style session management, rigorous quality preservation, and published benchmarks.

We will not copy these projects. Instead, we synthesize the best ideas into a clean, maintainable, measurable library optimized for the target use case.

See `RESEARCH.md` (forthcoming) and `ROADMAP.md` for details.

## Design Philosophy (Gilfoyle-approved)

- Correctness > elegance > speed of implementation.
- Measure everything (cost, latency, quality, hit rates).
- Automate optimizations with smart defaults; allow overrides.
- Prefer simple, composable components over monolithic magic.
- Keep API surface small and stable.
- Documentation and benchmarks are first-class.
- Refactor relentlessly.

## Non-Goals

- Replacing the entire Orion backend.
- Self-hosted model serving (focus on MaaS/Vertex).
- Being a general LLM proxy (LiteLLM already exists; we focus on deep cost optimizations for conversational use).
- Supporting every possible model/provider from day one (start with Vertex Gemini/Claude, expand later).

## Quick Start

```python
from thriftllm import ThriftVertex
from thriftllm.providers.claude import ClaudeVertex

# 1. Using Gemini on Vertex AI
client = ThriftVertex(
    project_id="your-project",
    location="us-central1",
    config={"enable_caching": True, "redis_url": "redis://localhost:6379"}
)

model = client.get_model("gemini-2.5-flash")
response = model.generate_content("Your prompt here...", session_id="user-123")

# 2. Using Claude on Vertex AI
claude_client = ClaudeVertex(
    project_id="your-project",
    region="us-central1",
    thrift_app=client  # Share the same cache and metrics configuration
)

claude_model = claude_client.get_model("claude-3-sonnet@20240229", max_tokens=1024)
messages = [{"role": "user", "content": "Explain quantum computing."}]
claude_response = claude_model.create_message(messages, session_id="user-123")
```

See `examples/orion_integration_example.py` for advanced Flask integration.

## Architecture (High-level, to be detailed in ARCHITECTURE.md)

- **Cache Layer**: Hybrid (exact, semantic, context/prompt cache using Vertex APIs + Redis).
- **Compressor**: LLMLingua-inspired + custom for tool outputs/RAG.
- **Router**: Adaptive based on query complexity, history length, confidence.
- **Summarizer**: Maintains compressed conversation state in Redis/Supabase.
- **Observer**: Integrates with Langfuse/Helicone for cost tracking.
- **Quality Guard**: LLM judge or embedding similarity before serving cached responses.

All components designed for low overhead and high hit rates in conversational flows.

## Repository Structure

```
thriftllm/
├── src/thriftllm/          # Main package
├── tests/                  # Comprehensive test suite
├── examples/               # Orion integration, benchmarks
├── docs/                   # Detailed documentation
├── .github/workflows/      # CI/CD
├── pyproject.toml
├── README.md
├── ROADMAP.md
├── LICENSE
├── CONTRIBUTING.md
└── BENCHMARKS.md
```

## Future Vision

Become the de-facto standard middleware for cost-efficient Vertex AI deployments in agentic and conversational applications. Expand to full multi-provider support, advanced agent optimizations, auto-benchmarking, and community-contributed optimizers.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Major decisions documented in `ARCHITECTURE.md` and ROADMAP.

This project follows the engineering standards of its maintainer (inspired by *Silicon Valley*'s Gilfoyle): research-first, benchmark-driven, documentation-obsessed, technical-debt-intolerant.

---

**Status**: M5 - Community adoption and additional providers.

Last updated: August 14, 2026