import asyncio
from typing import List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class BatchOptimizer:
    """
    Optimizes batch requests to Vertex AI by grouping similar prompts,
    managing rate limits, and parallelizing execution.
    """
    def __init__(self, max_concurrent: int = 10, batch_size: int = 5):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(self, prompts: List[str], generate_func: Callable, **kwargs) -> List[Any]:
        """
        Process a list of prompts concurrently with rate limiting.
        """
        async def _process_single(prompt: str, index: int) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    response = await generate_func(prompt, **kwargs)
                    return {"index": index, "response": response, "error": None}
                except Exception as e:
                    logger.error(f"Error processing prompt {index}: {e}")
                    return {"index": index, "response": None, "error": str(e)}

        tasks = [_process_single(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        
        # Sort by original index to maintain order
        results.sort(key=lambda x: x["index"])
        return [r["response"] if r["error"] is None else {"error": r["error"]} for r in results]
