"""Metrics collection for observability and benchmarking.

Tracks every inference call: tokens, latency, cache hits, estimated costs/savings,
quality scores. Pluggable with Langfuse, Prometheus, or console.

Critical for the project's success metric: measurable, reproducible cost reductions
with quality preservation. All numbers in RESEARCH.md and BENCHMARKS.md will come from here.
"""
import time
from dataclasses import dataclass
from typing import Optional, Dict
import json


@dataclass
class CallMetrics:
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cache_hit: bool
    estimated_cost_usd: float
    estimated_savings_usd: float
    quality_score: Optional[float] = None


class MetricsCollector:
    """Collects and reports optimization metrics.

    In production, this would push to Langfuse or a time-series DB.
    For now, console + in-memory for benchmarks.
    """
    def __init__(self, config):
        self.config = config
        self.calls: list[CallMetrics] = []
        self.total_savings = 0.0
        self.cache_hits = 0
        self.total_calls = 0

    def record_call(self, model: str, input_tokens: int, output_tokens: int,
                   latency: float, cache_hit: bool, estimated_savings: float,
                   quality_score: Optional[float] = None):
        """Record a single model call."""
        cost = self._estimate_cost(model, input_tokens, output_tokens)  # Placeholder
        metrics = CallMetrics(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency * 1000,
            cache_hit=cache_hit,
            estimated_cost_usd=cost,
            estimated_savings_usd=estimated_savings,
            quality_score=quality_score
        )
        self.calls.append(metrics)
        self.total_calls += 1
        self.total_savings += estimated_savings
        if cache_hit:
            self.cache_hits += 1

        # In real version, send to Langfuse or log structured
        print(f"[ThriftLLM] {model} | hit={cache_hit} | savings=${estimated_savings:.4f} | "
              f"latency={metrics.latency_ms:.1f}ms | quality={quality_score or 'N/A'}")

    def record_error(self, error_msg: str):
        print(f"[ThriftLLM ERROR] {error_msg}")

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost using exact 2026 Vertex AI pricing tables.
        
        Pricing based on Gemini 1.5 and Claude 3/3.5 families.
        Assumes < 128k context window for Gemini pricing tiers for simplicity,
        but can be extended to check input_tokens > 128000.
        """
        model_lower = model.lower()
        
        # Claude Models
        if "claude-3-5-sonnet" in model_lower:
            return (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)
        elif "claude-3-opus" in model_lower:
            return (input_tokens * 15.0 / 1_000_000) + (output_tokens * 75.0 / 1_000_000)
        elif "claude-3-haiku" in model_lower:
            return (input_tokens * 0.25 / 1_000_000) + (output_tokens * 1.25 / 1_000_000)
        elif "claude-3-sonnet" in model_lower:
            return (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)
            
        # Gemini Models
        elif "gemini-1.5-flash" in model_lower:
            if input_tokens <= 128000:
                return (input_tokens * 0.075 / 1_000_000) + (output_tokens * 0.30 / 1_000_000)
            else:
                return (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)
        elif "gemini-1.5-pro" in model_lower or "gemini-pro" in model_lower:
            if input_tokens <= 128000:
                return (input_tokens * 1.25 / 1_000_000) + (output_tokens * 5.00 / 1_000_000)
            else:
                return (input_tokens * 2.50 / 1_000_000) + (output_tokens * 10.00 / 1_000_000)
        
        # Fallback (approximate Pro-like)
        return (input_tokens * 1.25 / 1_000_000) + (output_tokens * 5.00 / 1_000_000)

    def get_summary(self) -> Dict:
        """Return aggregate stats for benchmarks."""
        if not self.total_calls:
            return {"total_calls": 0}
        hit_rate = (self.cache_hits / self.total_calls) * 100
        return {
            "total_calls": self.total_calls,
            "cache_hit_rate_pct": round(hit_rate, 2),
            "total_savings_usd": round(self.total_savings, 4),
            "avg_latency_ms": round(sum(c.latency_ms for c in self.calls) / self.total_calls, 2),
        }

    def reset(self):
        self.calls.clear()
        self.total_savings = 0.0
        self.cache_hits = 0
        self.total_calls = 0
