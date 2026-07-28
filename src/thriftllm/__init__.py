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

__version__ = "0.1.0"
__all__ = ["ThriftVertex", "OptimizationConfig", "MetricsCollector"]

# TODO: Implement individual optimization layers in subsequent modules
# - cache/: Hybrid semantic + Vertex Context Cache + Redis
# - compression/: LLMLingua + custom for RAG/tools
# - routing/: Adaptive model selection (Flash vs Pro)
# - summarization/: Rolling conversation state management
# - quality/: LLM-as-judge and embedding similarity guards
# - integration/: Flask middleware, session awareness with Redis/Supabase
