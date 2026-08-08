"""
Example: Integrating ThriftLLM with a Flask Application (Orion Backend Style)

This example demonstrates how to use the `OrionAdapter` and `thrift_route`
decorator to seamlessly integrate ThriftLLM's cost-saving features into an
existing Flask application.

Prerequisites:
    pip install flask thriftllm
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/gcp-service-account.json"
"""

import os
from flask import Flask, request, jsonify, g
from thriftllm.adapter import OrionAdapter, thrift_route

# 1. Initialize the Flask application
app = Flask(__name__)

# 2. Configure ThriftLLM
# In a real Orion deployment, you would pass your Redis and Supabase clients here.
# The thrift_config dictionary configures the underlying ThriftVertex core.
thrift_config = {
    "project_id": os.environ.get("GOOGLE_CLOUD_PROJECT", "my-gcp-project"),
    "location": "us-central1",
    "enable_caching": True,
    "enable_compression": True,
    "compression_target_ratio": 0.7
}

# 3. Initialize the OrionAdapter
# This automatically registers before/after request handlers to manage
# the ThriftVertex client lifecycle and session injection.
adapter = OrionAdapter(app=app, thrift_config=thrift_config)

# 4. Define your routes using the @thrift_route decorator
@app.route('/api/v1/chat', methods=['POST'])
@thrift_route(model_name="gemini-1.5-flash")
def chat_endpoint():
    """
    A standard chat endpoint.
    The @thrift_route decorator ensures that `g.thrift_client` is available.
    The OrionAdapter's before_request handler ensures `g.session_id` is populated
    (e.g., from the 'X-Session-ID' header).
    """
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400
        
    prompt = data['prompt']
    
    try:
        # 5. Use the injected ThriftVertex client
        # The client will automatically handle caching, compression, and routing
        # based on the configuration provided during adapter initialization.
        # Passing the session_id enables session-aware caching (e.g., for conversation history).
        response = g.thrift_client.generate_content(
            model_name="gemini-1.5-flash", 
            contents=prompt, 
            session_id=g.session_id
        )
        
        # The response object is a proxy that mimics the Vertex AI response structure
        return jsonify({
            "response": response.text,
            "session_id": g.session_id,
            "status": "success"
        })
        
    except Exception as e:
        # In a production app, you'd log this properly
        print(f"Error during generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "thriftllm_enabled": hasattr(g, 'thrift_client')})

if __name__ == '__main__':
    print("Starting Orion-style Flask app with ThriftLLM integration...")
    print("Send a POST request to http://localhost:5000/api/v1/chat")
    print("Example curl:")
    print('curl -X POST http://localhost:5000/api/v1/chat -H "Content-Type: application/json" -H "X-Session-ID: user-123" -d \'{"prompt": "Explain quantum computing in simple terms."}\'')
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
