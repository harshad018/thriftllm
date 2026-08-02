import pytest
import json
from unittest.mock import MagicMock, patch
import numpy as np

from thriftllm.cache import CacheManager
from thriftllm.metrics import MetricsCollector

class MockConfig:
    def __init__(self, redis_url="redis://localhost:6379", enable_caching=True, quality_threshold=0.8, cache_ttl_seconds=3600):
        self.redis_url = redis_url
        self.enable_caching = enable_caching
        self.quality_threshold = quality_threshold
        self.cache_ttl_seconds = cache_ttl_seconds

@pytest.fixture
def mock_metrics():
    return MagicMock(spec=MetricsCollector)

@pytest.fixture
def mock_redis():
    with patch('redis.from_url') as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_sentence_transformer():
    with patch('thriftllm.cache.SentenceTransformer') as mock_st:
        mock_model = MagicMock()
        # Return a dummy embedding (e.g., 384-dimensional vector of ones)
        mock_model.encode.return_value = np.ones(384) / np.linalg.norm(np.ones(384))
        mock_st.return_value = mock_model
        yield mock_model

def test_cache_init_no_redis(mock_metrics):
    config = MockConfig(redis_url=None)
    cache = CacheManager(config, mock_metrics)
    assert cache.redis_client is None
    assert cache.embedding_model is None

def test_exact_cache_hit(mock_redis, mock_metrics, mock_sentence_transformer):
    config = MockConfig()
    cache = CacheManager(config, mock_metrics)
    
    # Setup mock Redis to return a hit
    cached_data = {
        "text": "cached response",
        "response": "cached response object",
        "output_tokens": 10
    }
    mock_redis.get.return_value = json.dumps(cached_data)
    
    result = cache.get_cached_response("test prompt", "gemini-1.5-flash")
    
    assert result is not None
    assert result["hit_type"] == "exact"
    assert result["cached_text"] == "cached response"
    mock_metrics.record_call.assert_called_once()

def test_exact_cache_miss_semantic_miss(mock_redis, mock_metrics, mock_sentence_transformer):
    config = MockConfig()
    cache = CacheManager(config, mock_metrics)
    
    # Setup mock Redis to return None for exact match and empty list for semantic
    mock_redis.get.return_value = None
    mock_redis.lrange.return_value = []
    
    result = cache.get_cached_response("test prompt", "gemini-1.5-flash")
    
    assert result is None
    mock_metrics.record_call.assert_not_called()

def test_semantic_cache_hit(mock_redis, mock_metrics, mock_sentence_transformer):
    config = MockConfig()
    cache = CacheManager(config, mock_metrics)
    
    # Setup mock Redis: miss on exact, hit on semantic
    # First call to get() is for exact match (returns None)
    # Second call to get() is inside the semantic loop
    
    dummy_emb = np.ones(384) / np.linalg.norm(np.ones(384))
    semantic_data = {
        "text": "semantic response",
        "response": "semantic response object",
        "output_tokens": 15,
        "embedding": dummy_emb.tolist()
    }
    
    def mock_get_side_effect(key):
        if "recent_semantic" not in key and "content:" in key:
            return None # Exact miss
        return json.dumps(semantic_data) # Semantic hit data
        
    mock_redis.get.side_effect = mock_get_side_effect
    mock_redis.lrange.return_value = ["dummy_key"]
    
    result = cache.get_cached_response("test prompt", "gemini-1.5-flash")
    
    assert result is not None
    assert result["hit_type"] == "semantic"
    assert result["cached_text"] == "semantic response"
    mock_metrics.record_call.assert_called_once()

def test_store_response(mock_redis, mock_metrics, mock_sentence_transformer):
    config = MockConfig()
    cache = CacheManager(config, mock_metrics)
    
    class DummyResponse:
        text = "dummy text"
        def __str__(self): return "dummy text"
        
    cache.store_response("prompt", "model", DummyResponse(), output_tokens=5)
    
    mock_redis.set.assert_called_once()
    mock_redis.lpush.assert_called_once()
    mock_redis.ltrim.assert_called_once()
