"""A/B Testing module for ThriftLLM configurations.

Allows routing traffic between two different configurations (e.g., different models,
different cache thresholds, or different compressor settings) and tracking the metrics
(cost, latency, user feedback) for each variant.

This is critical for empirically validating optimization strategies in production
without risking full deployment.
"""
import random
import hashlib
from typing import Dict, Any, Optional, Tuple

class ABTestManager:
    """Manages A/B testing of ThriftLLM configurations."""
    
    def __init__(self, config_a: Dict[str, Any], config_b: Dict[str, Any], split_ratio: float = 0.5):
        """
        Initialize the A/B test manager.
        
        Args:
            config_a: The control configuration (e.g., current production settings).
            config_b: The variant configuration (e.g., new experimental settings).
            split_ratio: The percentage of traffic to route to config_b (0.0 to 1.0).
        """
        self.config_a = config_a
        self.config_b = config_b
        self.split_ratio = max(0.0, min(1.0, split_ratio))
        
        # Metrics tracking per variant
        self.metrics = {
            "A": {"calls": 0, "total_latency": 0.0, "total_cost": 0.0, "cache_hits": 0},
            "B": {"calls": 0, "total_latency": 0.0, "total_cost": 0.0, "cache_hits": 0}
        }

    def get_config(self, session_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Determine which configuration to use for a given request or session.
        
        If session_id is provided, the variant assignment is deterministic for that session.
        Otherwise, it's randomly assigned based on the split_ratio.
        
        Returns:
            A tuple of (variant_name, configuration_dict).
        """
        if session_id:
            # Deterministic assignment based on session_id hash
            hash_val = int(hashlib.md5(session_id.encode('utf-8')).hexdigest(), 16)
            # Normalize to 0.0 - 1.0
            normalized_hash = (hash_val % 10000) / 10000.0
            use_b = normalized_hash < self.split_ratio
        else:
            # Random assignment
            use_b = random.random() < self.split_ratio
            
        if use_b:
            return "B", self.config_b
        return "A", self.config_a

    def record_metrics(self, variant: str, latency_ms: float, cost_usd: float, cache_hit: bool):
        """Record metrics for a specific variant."""
        if variant not in self.metrics:
            return
            
        self.metrics[variant]["calls"] += 1
        self.metrics[variant]["total_latency"] += latency_ms
        self.metrics[variant]["total_cost"] += cost_usd
        if cache_hit:
            self.metrics[variant]["cache_hits"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the A/B test results."""
        summary = {}
        for variant, stats in self.metrics.items():
            calls = stats["calls"]
            if calls == 0:
                summary[variant] = {"calls": 0}
                continue
                
            summary[variant] = {
                "calls": calls,
                "avg_latency_ms": round(stats["total_latency"] / calls, 2),
                "avg_cost_usd": round(stats["total_cost"] / calls, 6),
                "cache_hit_rate_pct": round((stats["cache_hits"] / calls) * 100, 2)
            }
            
        return summary
