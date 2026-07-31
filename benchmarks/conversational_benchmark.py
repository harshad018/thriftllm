import time
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path so we can import thriftllm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from thriftllm.core import ThriftVertex, OptimizationConfig

# Simulated conversational data (Orion-like)
# Includes exact repeats and semantically similar queries to test the hybrid cache.
CONVERSATION = [
    "What is the capital of France?",
    "Tell me about the history of Paris.",
    "What is the capital of France?",  # Exact repeat
    "Can you summarize the history of Paris?", # Semantically similar
    "How do I write a binary search in Python?",
    "Write a python script for binary search.", # Semantically similar
    "What is the weather like today?",
]

class MockResponse:
    def __init__(self, text, prompt_tokens=10, candidates_tokens=20):
        self.text = text
        self.candidates = [MagicMock(text=text)]
        self.usage_metadata = MagicMock(
            prompt_token_count=prompt_tokens,
            candidates_token_count=candidates_tokens
        )

def mock_generate_content(contents, **kwargs):
    # Simulate network latency
    time.sleep(0.1)
    return MockResponse(f"Simulated response for: {contents}")

def run_baseline():
    print("--- Running Baseline (No Optimization) ---")
    total_latency = 0
    total_cost = 0
    # Assuming $0.0001 per token for simplicity in this benchmark
    cost_per_token = 0.0001 
    
    for query in CONVERSATION:
        start = time.time()
        # Simulate the call
        resp = mock_generate_content(query)
        latency = time.time() - start
        total_latency += latency
        
        tokens = resp.usage_metadata.prompt_token_count + resp.usage_metadata.candidates_token_count
        cost = tokens * cost_per_token
        total_cost += cost
        
        print(f"Query: '{query[:30]}...' | Latency: {latency:.3f}s | Cost: ${cost:.4f}")
        
    print(f"Baseline Total Latency: {total_latency:.3f}s")
    print(f"Baseline Total Cost: ${total_cost:.4f}\n")
    return total_cost, total_latency

@patch('thriftllm.core.vertexai.init')
@patch('thriftllm.core.GenerativeModel')
def run_thriftllm(mock_gen_model_class, mock_init):
    print("--- Running ThriftLLM (With CacheManager) ---")
    
    # Setup mock GenerativeModel
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = mock_generate_content
    mock_model_instance._model_name = "mock-gemini"
    mock_gen_model_class.return_value = mock_model_instance

    config = OptimizationConfig(enable_caching=True)
    thrift = ThriftVertex(project_id="test-project", config=config)
    model = thrift.get_model("mock-gemini")
    
    total_latency = 0
    total_cost = 0
    cost_per_token = 0.0001
    cache_hits = 0
    
    for query in CONVERSATION:
        start = time.time()
        resp = model.generate_content(query, session_id="bench-session-1")
        latency = time.time() - start
        total_latency += latency
        
        # Check if it was a cache hit (our mock CachedResponse has 0 tokens)
        prompt_tokens = getattr(resp.usage_metadata, 'prompt_token_count', 0)
        cand_tokens = getattr(resp.usage_metadata, 'candidates_token_count', 0)
        
        if prompt_tokens == 0 and cand_tokens == 0:
            cache_hits += 1
            cost = 0 # Cache hit is free in this simulation
        else:
            cost = (prompt_tokens + cand_tokens) * cost_per_token
            
        total_cost += cost
        print(f"Query: '{query[:30]}...' | Latency: {latency:.3f}s | Cost: ${cost:.4f} | Hit: {prompt_tokens == 0}")

    print(f"ThriftLLM Total Latency: {total_latency:.3f}s")
    print(f"ThriftLLM Total Cost: ${total_cost:.4f}")
    print(f"Cache Hits: {cache_hits}/{len(CONVERSATION)}\n")
    return total_cost, total_latency

if __name__ == "__main__":
    print("Starting Conversational Benchmark...\n")
    base_cost, base_latency = run_baseline()
    thrift_cost, thrift_latency = run_thriftllm()
    
    savings_pct = ((base_cost - thrift_cost) / base_cost) * 100 if base_cost > 0 else 0
    latency_diff = base_latency - thrift_latency
    
    print("--- Benchmark Summary ---")
    print(f"Cost Savings: {savings_pct:.1f}%")
    print(f"Latency Reduction: {latency_diff:.3f}s")
    
    if savings_pct >= 40:
        print("SUCCESS: Target savings of 40-70% achieved.")
    else:
        print("WARNING: Target savings not met. Review cache configuration.")
