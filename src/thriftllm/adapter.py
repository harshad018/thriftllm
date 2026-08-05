"""
Flask Middleware and Orion Adapter for ThriftLLM.

This module provides integration points for Flask applications, specifically
tailored for the Orion backend architecture which utilizes Redis for session
management and Supabase for persistence.
"""

import functools
import json
import logging
from typing import Callable, Any, Dict, Optional

try:
    from flask import request, g, current_app, jsonify
except ImportError:
    request = None
    g = None
    current_app = None
    jsonify = None

from .core import ThriftVertex

logger = logging.getLogger(__name__)

class OrionAdapter:
    """
    Adapter for integrating ThriftLLM with Orion's specific architecture.
    Handles session synchronization between Redis and Supabase, and injects
    the ThriftVertex client into the Flask request context.
    """
    
    def __init__(self, app=None, redis_client=None, supabase_client=None, thrift_config: Dict = None):
        self.redis_client = redis_client
        self.supabase_client = supabase_client
        self.thrift_config = thrift_config or {}
        self.thrift_client = None
        
        if app is not None:
            self.init_app(app)
            
    def init_app(self, app):
        """Initialize the Flask extension."""
        if request is None:
            raise ImportError("Flask is required to use OrionAdapter. Install it with `pip install flask`.")
            
        app.extensions['thriftllm'] = self
        
        # Initialize the core ThriftVertex client
        self.thrift_client = ThriftVertex(**self.thrift_config)
        
        # Register before/after request handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
    def _before_request(self):
        """
        Inject the ThriftVertex client into the global request context (g).
        Extract session ID from headers or token to enable session-aware caching.
        """
        g.thrift_client = self.thrift_client
        
        # Attempt to extract session ID (Orion specific logic)
        session_id = request.headers.get('X-Session-ID')
        if not session_id and request.authorization:
            # Fallback to user ID if session ID is not present but user is auth'd
            session_id = f"user_{request.authorization.username}"
            
        g.session_id = session_id
        
    def _after_request(self, response):
        """
        Optional: Inject cost savings metrics into response headers for observability.
        """
        if hasattr(g, 'thrift_metrics') and g.thrift_metrics:
            try:
                metrics_json = json.dumps(g.thrift_metrics)
                response.headers['X-ThriftLLM-Metrics'] = metrics_json
            except Exception as e:
                logger.warning(f"Failed to serialize ThriftLLM metrics: {e}")
                
        return response

def thrift_route(model_name: str = "gemini-1.5-pro"):
    """
    Flask route decorator to automatically wrap the endpoint with ThriftLLM processing.
    
    Usage:
        @app.route('/chat', methods=['POST'])
        @thrift_route(model_name="gemini-1.5-pro")
        def chat_endpoint():
            # g.thrift_client is available here
            prompt = request.json.get('prompt')
            response = g.thrift_client.generate_content(model_name, prompt, session_id=g.session_id)
            return jsonify({"response": response.text})
    """
    def decorator(f: Callable):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if request is None:
                raise RuntimeError("thrift_route decorator must be used within a Flask application context.")
                
            if not hasattr(g, 'thrift_client'):
                logger.error("ThriftVertex client not found in request context. Ensure OrionAdapter is initialized.")
                return jsonify({"error": "Internal Server Error: LLM Middleware not initialized"}), 500
                
            # The actual endpoint logic is executed here.
            # The endpoint can access g.thrift_client and g.session_id
            return f(*args, **kwargs)
        return wrapped
    return decorator
