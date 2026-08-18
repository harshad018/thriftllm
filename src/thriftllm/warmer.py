"""
Cache Warmer for ThriftLLM.

This module provides utilities to proactively warm the cache with context,
such as documents retrieved during Orion's deep research RAG process.
By pre-computing and caching these contexts, subsequent generation requests
can benefit from reduced latency and cost.
"""

import logging
from typing import List, Dict, Any, Optional
from .core import ThriftVertex

logger = logging.getLogger(__name__)

class CacheWarmer:
    """
    Proactively warms the ThriftLLM cache with provided contexts.
    Useful for RAG pipelines where retrieved documents can be cached
    before the user explicitly queries them.
    """
    
    def __init__(self, thrift_client: ThriftVertex):
        self.thrift_client = thrift_client

    def warm_from_rag_documents(
        self, 
        model_name: str, 
        documents: List[str], 
        session_id: str, 
        system_instruction: Optional[str] = None,
        background: bool = False
    ) -> Dict[str, Any]:
        """
        Warms the cache using a list of documents retrieved from a RAG process.
        
        Args:
            model_name: The model to use for warming.
            documents: List of document texts to cache.
            session_id: The session ID to associate with the cached context.
            system_instruction: Optional system instruction to prepend.
            background: If True, warming could be dispatched to a background task (not implemented here, but flag provided for integration).
            
        Returns:
            A dictionary containing warming metrics (e.g., tokens processed).
        """
        logger.info(f"Warming cache for session {session_id} with {len(documents)} documents.")
        
        # Combine documents into a single context block
        combined_context = "\\n\\n".join([f"Document {i+1}:\\n{doc}" for i, doc in enumerate(documents)])
        
        prompt = f"Context:\\n{combined_context}\\n\\nPlease acknowledge that you have received and processed this context."
        
        if system_instruction:
            prompt = f"System: {system_instruction}\\n\\n{prompt}"
            
        try:
            # We call generate_content to force the cache to process and store the prompt.
            # In a real scenario, we might use a specific caching API if the provider supports it,
            # but for ThriftLLM, calling generate_content will trigger the CacheManager and VertexContextCacheManager.
            response = self.thrift_client.generate_content(
                model_name=model_name,
                prompt=prompt,
                session_id=session_id
            )
            
            logger.info(f"Cache warming successful for session {session_id}.")
            return {
                "status": "success",
                "documents_processed": len(documents),
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Failed to warm cache for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
