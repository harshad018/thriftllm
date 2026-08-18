"""ThriftLLM - Production middleware for low-cost Vertex AI inference.

This package provides intelligent optimization layers (caching, compression,
routing, summarization) for Vertex AI models, with special focus on
conversational, long-context, tool-using workloads like those in Orion.

Core philosophy: Measure everything. Preserve quality. Maximize savings.
Research-driven, benchmarked, documented.

See README.md, ARCHITECTURE.md, and ROADMAP.md for details.
"""

from .core import ThriftVertex, OptimizationConfig
from .metrics import MetricsCollector
from .adapter import OrionAdapter, thrift_route
from .providers.claude import ClaudeVertex
from .warmer import CacheWarmer

__version__ = "0.1.0"
__all__ = ["ThriftVertex", "OptimizationConfig", "MetricsCollector", "OrionAdapter", "thrift_route", "ClaudeVertex", "CacheWarmer"]

# TODO: Implement individual optimization layers in subsequent modules
# - cache/: Hybrid semantic + Vertex Context Cache + Redis (Implemented)
# - compression/: LLMLingua + custom for RAG/tools (Implemented)
# - routing/: Adaptive model selection (Flash vs Pro) (Implemented)
# - summarization/: Rolling conversation state management (Implemented)
# - quality/: LLM-as-judge and embedding similarity guards
# - integration/: Flask middleware, session awareness with Redis/Supabase (Implemented)
