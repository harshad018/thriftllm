# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-09
### Added
- Core library skeleton (`ThriftVertex`, `WrappedGenerativeModel`).
- `CacheManager` with hybrid exact/semantic caching.
- `PromptCompressor` with LLMLingua integration and `QualityGuard`.
- `ConversationSummarizer` for Redis-backed rolling summaries.
- `AdaptiveRouter` for heuristic-based model downgrading.
- `VertexContextCacheManager` for deep Vertex AI context caching.
- `OrionAdapter` and `thrift_route` decorator for Flask middleware integration.
- Comprehensive unit tests for cache and compressor.
- Benchmarking scripts and `BENCHMARKS.md` documenting up to 82% cost reductions.
- Integration examples for Orion.
- Initial documentation (README, ARCHITECTURE, RESEARCH, CONTRIBUTING).
