# ThriftLLM Benchmarks

This document outlines the simulated performance and cost-reduction benchmarks for the ThriftLLM middleware against baseline Vertex AI usage.

## Methodology

Benchmarks were generated using the `benchmarks/conversational_benchmark.py` script, which simulates multi-turn conversational traffic typical of the Orion platform. The simulation measures token usage and estimates costs based on standard Vertex AI pricing models (e.g., Gemini 1.5 Pro/Flash).

The benchmark evaluates the following optimization layers:
1.  **Exact Caching:** Redis-backed exact string matching for repeated queries.
2.  **Semantic Caching:** Embedding-based similarity matching for paraphrased queries.
3.  **Prompt Compression:** LLMLingua-based compression of context windows.
4.  **Vertex Context Caching:** Native Vertex AI caching for large, static contexts (e.g., system instructions, document RAG).

## Simulated Results

### Scenario 1: High-Redundancy Conversational Traffic
*Traffic Profile:* 1000 requests, 40% exact repeats, 20% semantic similarity, average context size 4k tokens.

*   **Baseline Vertex AI Cost:** ~$15.00
*   **ThriftLLM Cost:** ~$3.50
*   **Cost Reduction:** **~76%**
*   **Latency Impact:** Average +15ms overhead for cache misses, -800ms reduction for cache hits.

### Scenario 2: Large Context RAG (Deep Research)
*Traffic Profile:* 500 requests, 100k token static context (documents), dynamic user queries.

*   **Baseline Vertex AI Cost:** ~$125.00 (re-processing 100k tokens per request)
*   **ThriftLLM Cost (with Vertex Context Caching):** ~$22.00 (cache storage + dynamic token processing)
*   **Cost Reduction:** **~82%**

## Conclusion

ThriftLLM demonstrates significant potential for cost reduction, particularly in scenarios with high query redundancy or large, static context windows. The combination of local caching and native Vertex caching provides a robust defense against token bloat.

*Note: These are simulated benchmarks. Real-world results will vary based on actual traffic patterns and model selection.*
