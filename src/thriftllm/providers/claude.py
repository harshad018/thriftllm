"""Claude on Vertex provider for ThriftLLM."""

import time
from typing import Any, Dict, Optional, List

try:
    from anthropic import AnthropicVertex
except ImportError:
    AnthropicVertex = None

class ClaudeVertex:
    """Wrapper for Claude on Vertex AI using AnthropicVertex SDK."""
    
    def __init__(self, project_id: str, region: str = "us-central1", thrift_app=None):
        self.project_id = project_id
        self.region = region
        self.thrift = thrift_app
        if AnthropicVertex is None:
            raise ImportError("anthropic[vertex] is not installed. Please install it to use ClaudeVertex.")
        self.client = AnthropicVertex(project_id=project_id, region=region)
        
    def get_model(self, model_name: str, **kwargs):
        return WrappedClaudeModel(self.client, model_name, self.thrift, **kwargs)

    def invalidate_cache(self, messages: List[Dict[str, Any]], model_name: str, session_id: Optional[str] = None) -> bool:
        """Invalidate a specific cache entry for Claude."""
        if self.thrift and self.thrift.cache_manager:
            prompt_text = self._extract_text(messages)
            return self.thrift.cache_manager.invalidate(prompt_text, model_name, session_id)
        return False

    def _extract_text(self, messages: List[Dict[str, Any]]) -> str:
        if not messages:
            return ""
        last_msg = messages[-1]
        if isinstance(last_msg, dict) and "content" in last_msg:
            return str(last_msg["content"])
        return str(last_msg)

class WrappedClaudeModel:
    def __init__(self, client, model_name: str, thrift, **kwargs):
        self.client = client
        self.model_name = model_name
        self.thrift = thrift
        self.default_kwargs = kwargs
        
    def _extract_text(self, messages: List[Dict[str, Any]]) -> str:
        if not messages:
            return ""
        last_msg = messages[-1]
        if isinstance(last_msg, dict) and "content" in last_msg:
            return str(last_msg["content"])
        return str(last_msg)

    def create_message(self, messages: List[Dict[str, Any]], **kwargs):
        start_time = time.time()
        session_id = kwargs.pop("session_id", None)
        
        cache_manager = self.thrift.cache_manager if self.thrift else None
        
        # Layer 1: Cache check
        if cache_manager and self.thrift and self.thrift.config.enable_caching:
            prompt_text = self._extract_text(messages)
            cache_result = cache_manager.get_cached_response(prompt_text, self.model_name, session_id)
            if cache_result:
                class CachedMessage:
                    def __init__(self, text):
                        self.content = [type("Content", (), {"text": text})()]
                        self.usage = type("Usage", (), {"input_tokens": 0, "output_tokens": 0})()
                
                latency = time.time() - start_time
                if self.thrift:
                    self.thrift.metrics.record_call(
                        model=self.model_name, input_tokens=0, output_tokens=0,
                        latency=latency, cache_hit=True, estimated_savings=0.25, quality_score=cache_result.get("similarity", 1.0)
                    )
                return CachedMessage(cache_result.get("cached_text", ""))

        # Merge kwargs
        call_kwargs = {**self.default_kwargs, **kwargs}
        if "max_tokens" not in call_kwargs:
            call_kwargs["max_tokens"] = 1024
            
        response = self.client.messages.create(
            model=self.model_name,
            messages=messages,
            **call_kwargs
        )
        
        latency = time.time() - start_time
        input_tokens = getattr(response.usage, 'input_tokens', 0)
        output_tokens = getattr(response.usage, 'output_tokens', 0)
        
        if cache_manager and self.thrift:
            prompt_text = self._extract_text(messages)
            # Adapt response for cache_manager
            class AdaptedResponse:
                def __init__(self, text):
                    self.text = text
            
            response_text = response.content[0].text if response.content else ""
            adapted_resp = AdaptedResponse(response_text)
            
            emb = None
            if hasattr(cache_manager, '_get_embedding'):
                emb = cache_manager._get_embedding(prompt_text)
            cache_manager.store_response(prompt_text, self.model_name, adapted_resp, session_id, output_tokens, emb)
            
        if self.thrift:
            self.thrift.metrics.record_call(
                model=self.model_name, input_tokens=input_tokens, output_tokens=output_tokens,
                latency=latency, cache_hit=False, estimated_savings=0.0, quality_score=1.0
            )
            
        return response
