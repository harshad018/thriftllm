"""Core module for ThriftLLM.

Provides the main ThriftVertex class that acts as a smart wrapper around
Vertex AI GenerativeModel. Applies optimizations in a layered fashion.

Updated (this session): Integrated ConversationSummarizer and AdaptiveRouter.
Pipeline in WrappedGenerativeModel now checks cache, summarizes history, routes, and generates.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, List
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
from google.api_core.exceptions import GoogleAPIError

from .metrics import MetricsCollector
from .cache import CacheManager
from .summarizer import ConversationSummarizer
from .router import AdaptiveRouter


@dataclass
class OptimizationConfig:
    """Configuration for all optimization layers."""
    enable_caching: bool = True
    enable_compression: bool = True
    enable_routing: bool = True
    enable_summarization: bool = True
    cache_ttl_seconds: int = 3600 * 24  # 1 day default
    quality_threshold: float = 0.85  # For cache hits and routing
    redis_url: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None


class ThriftVertex:
    """Main entrypoint. Wraps Vertex AI usage with cost optimizations."""
    def __init__(self, project_id: str, location: str = "us-central1", config: Optional[OptimizationConfig] = None):
        self.project_id = project_id
        self.location = location
        self.config = config or OptimizationConfig()
        self.metrics = MetricsCollector(self.config)

        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)

        # Layer instances
        self.cache_manager = None
        self.compressor = None
        self.summarizer = None
        self.router = None
        self.quality_guard = None

        self._init_layers()
        print(f"ThriftLLM initialized with config: caching={self.config.enable_caching}, "
              f"summarization={self.config.enable_summarization}, routing={self.config.enable_routing}")

    def _init_layers(self):
        """Initialize real optimization components where available."""
        if self.config.enable_caching:
            self.cache_manager = CacheManager(self.config, self.metrics)
        if self.config.enable_summarization:
            # In a real deployment, pass a configured Redis client here
            self.summarizer = ConversationSummarizer()
        if self.config.enable_routing:
            self.router = AdaptiveRouter()
        if self.config.enable_compression:
            self.compressor = CompressorStub(self.config, self.metrics)

    def get_model(self, model_name: str, **kwargs) -> "WrappedGenerativeModel":
        """Return a wrapped model that applies optimizations on every call."""
        base_model = GenerativeModel(model_name, **kwargs)
        return WrappedGenerativeModel(base_model, self)

    def wrap(self, model: GenerativeModel) -> "WrappedGenerativeModel":
        """Wrap an existing GenerativeModel instance."""
        return WrappedGenerativeModel(model, self)


class WrappedGenerativeModel:
    """Proxy that intercepts generate_content, send_message, etc."""
    def __init__(self, base_model: GenerativeModel, thrift: ThriftVertex):
        self.base_model = base_model
        self.thrift = thrift
        self.model_name = getattr(base_model, '_model_name', getattr(base_model, 'model_name', 'unknown'))

    def _extract_text(self, contents: Any) -> str:
        """Helper to extract text from various content formats for routing/summarization."""
        if isinstance(contents, str):
            return contents
        if isinstance(contents, list) and len(contents) > 0:
            if isinstance(contents[-1], dict) and "content" in contents[-1]:
                return contents[-1]["content"]
            if hasattr(contents[-1], "text"):
                return contents[-1].text
        return str(contents)

    def generate_content(self, contents: Any, generation_config: Optional[GenerationConfig] = None, **kwargs) -> Any:
        """Optimized generate_content with full pipeline."""
        start_time = time.time()
        session_id = kwargs.pop("session_id", None)

        cache_manager = self.thrift.cache_manager
        summarizer = self.thrift.summarizer
        router = self.thrift.router
        
        cache_result = None
        cache_hit = False
        estimated_savings = 0.0
        quality_score = 1.0
        
        current_model_name = self.model_name
        active_model = self.base_model

        # Layer 1: Cache check
        if cache_manager and self.thrift.config.enable_caching:
            cache_result = cache_manager.get_cached_response(contents, current_model_name, session_id)
            if cache_result:
                cache_hit = True
                estimated_savings = 0.25
                quality_score = cache_result.get("similarity", 1.0)
                class CachedResponse:
                    def __init__(self, text: str):
                        self.text = text
                        self.candidates = [type("Candidate", (), {"text": text})()]
                        self.usage_metadata = type("Usage", (), {"prompt_token_count": 0, "candidates_token_count": 0})()
                    def __getattr__(self, name):
                        return None
                response = CachedResponse(cache_result.get("cached_text", "[ThriftLLM Cached Response]"))
                latency = time.time() - start_time
                self.thrift.metrics.record_call(
                    model=current_model_name, input_tokens=0, output_tokens=0,
                    latency=latency, cache_hit=True, estimated_savings=estimated_savings, quality_score=quality_score
                )
                print(f"[ThriftLLM] Cache hit returned in {latency*1000:.1f}ms")
                return response

        # Layer 2: Summarization (if session_id and history provided)
        if summarizer and self.thrift.config.enable_summarization and session_id and isinstance(contents, list):
            # Assuming contents is a list of dicts for history
            try:
                contents = summarizer.process_history(session_id, contents)
            except Exception as e:
                print(f"[ThriftLLM] Summarization failed, proceeding with original contents: {e}")

        # Layer 3: Routing
        if router and self.thrift.config.enable_routing:
            prompt_text = self._extract_text(contents)
            history_len = len(contents) if isinstance(contents, list) else 0
            routed_model_name, reason = router.route(prompt_text, history_len)
            
            if routed_model_name != current_model_name:
                print(f"[ThriftLLM] Routing request from {current_model_name} to {routed_model_name} (Reason: {reason})")
                current_model_name = routed_model_name
                active_model = GenerativeModel(current_model_name)

        # Layer 4: Generation
        try:
            response = active_model.generate_content(
                contents, generation_config=generation_config, **kwargs
            )

            latency = time.time() - start_time
            input_tokens = getattr(getattr(response, 'usage_metadata', None), 'prompt_token_count', 100)
            output_tokens = getattr(getattr(response, 'usage_metadata', None), 'candidates_token_count', 50)

            # Layer 5: Store in cache
            if cache_manager and not cache_hit:
                emb = None
                if hasattr(cache_manager, '_get_embedding'):
                    query_text = cache_manager._extract_text_for_embedding(contents)
                    emb = cache_manager._get_embedding(query_text)
                cache_manager.store_response(contents, current_model_name, response, session_id, output_tokens, emb)

            self.thrift.metrics.record_call(
                model=current_model_name, input_tokens=input_tokens, output_tokens=output_tokens,
                latency=latency, cache_hit=False, estimated_savings=estimated_savings, quality_score=quality_score
            )

            return response
        except GoogleAPIError as e:
            self.thrift.metrics.record_error(str(e))
            raise

class CompressorStub:
    def __init__(self, config, metrics):
        self.config = config
        self.metrics = metrics
