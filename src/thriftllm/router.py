import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class AdaptiveRouter:
    """
    Intelligently routes requests to the most cost-effective model based on
    prompt complexity, length, and heuristics.
    """
    
    def __init__(self, default_model: str = "gemini-1.5-pro", fallback_model: str = "gemini-1.5-flash"):
        """
        Initialize the router.
        
        Args:
            default_model: The primary, more capable (and expensive) model.
            fallback_model: The cheaper, faster model for simpler queries.
        """
        self.default_model = default_model
        self.fallback_model = fallback_model
        
        # Heuristic triggers for complex routing
        self.complex_keywords = [
            "analyze", "synthesize", "evaluate", "code", "debug", 
            "architecture", "design", "compare", "contrast", "explain in detail"
        ]
        
    def route(self, prompt: str, history_length: int = 0) -> Tuple[str, str]:
        """
        Determine the optimal model for the given prompt.
        
        Returns:
            Tuple containing (selected_model_name, routing_reason)
        """
        if not prompt:
            return self.fallback_model, "empty_prompt"
            
        prompt_lower = prompt.lower()
        
        # 1. Length Heuristic
        # If the prompt is very short and there's little history, it's likely a simple query.
        if len(prompt) < 100 and history_length < 2:
            # Check if it contains complex keywords despite being short
            if not any(kw in prompt_lower for kw in self.complex_keywords):
                logger.info(f"Routing to {self.fallback_model} based on length heuristic.")
                return self.fallback_model, "short_simple_prompt"
                
        # 2. Keyword Heuristic
        # If the prompt explicitly asks for complex tasks, use the default model.
        if any(kw in prompt_lower for kw in self.complex_keywords):
            logger.info(f"Routing to {self.default_model} based on complexity keywords.")
            return self.default_model, "complex_keyword_detected"
            
        # 3. Default Fallback
        # If no heuristics trigger, default to the primary model to ensure quality.
        # In future versions, this could use a lightweight classifier model.
        logger.info(f"Routing to {self.default_model} (default behavior).")
        return self.default_model, "default_routing"
