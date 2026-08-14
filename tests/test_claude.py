import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock anthropic before importing ClaudeVertex
sys.modules['anthropic'] = MagicMock()
from anthropic import AnthropicVertex

from thriftllm.providers.claude import ClaudeVertex, WrappedClaudeModel

@pytest.fixture
def mock_thrift_app():
    app = MagicMock()
    app.config.enable_caching = True
    app.cache_manager = MagicMock()
    app.metrics = MagicMock()
    return app

@pytest.fixture
def claude_vertex(mock_thrift_app):
    with patch('thriftllm.providers.claude.AnthropicVertex') as mock_anthropic:
        provider = ClaudeVertex(project_id="test-project", region="us-central1", thrift_app=mock_thrift_app)
        return provider

def test_claude_vertex_init(claude_vertex):
    assert claude_vertex.project_id == "test-project"
    assert claude_vertex.region == "us-central1"
    assert claude_vertex.client is not None

def test_get_model(claude_vertex):
    model = claude_vertex.get_model("claude-3-sonnet@20240229", max_tokens=2048)
    assert isinstance(model, WrappedClaudeModel)
    assert model.model_name == "claude-3-sonnet@20240229"
    assert model.default_kwargs == {"max_tokens": 2048}

def test_create_message_cache_hit(claude_vertex, mock_thrift_app):
    model = claude_vertex.get_model("claude-3-sonnet@20240229")
    
    # Setup cache hit
    mock_thrift_app.cache_manager.get_cached_response.return_value = {
        "cached_text": "This is a cached response.",
        "similarity": 1.0
    }
    
    messages = [{"role": "user", "content": "Hello Claude"}]
    response = model.create_message(messages, session_id="session-123")
    
    # Verify cache was checked
    mock_thrift_app.cache_manager.get_cached_response.assert_called_once_with("Hello Claude", "claude-3-sonnet@20240229", "session-123")
    
    # Verify response structure
    assert response.content[0].text == "This is a cached response."
    assert response.usage.input_tokens == 0
    
    # Verify metrics recorded
    mock_thrift_app.metrics.record_call.assert_called_once()
    call_args = mock_thrift_app.metrics.record_call.call_args[1]
    assert call_args["cache_hit"] is True
    assert call_args["model"] == "claude-3-sonnet@20240229"

def test_create_message_cache_miss(claude_vertex, mock_thrift_app):
    model = claude_vertex.get_model("claude-3-sonnet@20240229")
    
    # Setup cache miss
    mock_thrift_app.cache_manager.get_cached_response.return_value = None
    
    # Setup mock client response
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is a live response."
    mock_response.content = [mock_content]
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 20
    model.client.messages.create.return_value = mock_response
    
    messages = [{"role": "user", "content": "Hello Claude"}]
    response = model.create_message(messages, session_id="session-123")
    
    # Verify client was called
    model.client.messages.create.assert_called_once()
    
    # Verify cache store was called
    mock_thrift_app.cache_manager.store_response.assert_called_once()
    
    # Verify metrics recorded
    mock_thrift_app.metrics.record_call.assert_called_once()
    call_args = mock_thrift_app.metrics.record_call.call_args[1]
    assert call_args["cache_hit"] is False
    assert call_args["input_tokens"] == 10
    assert call_args["output_tokens"] == 20
