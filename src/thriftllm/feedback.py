import json
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FeedbackCollector:
    """
    Collects preference data and feedback for router training and quality monitoring.
    This data can be used to fine-tune the AdaptiveRouter or evaluate model performance.
    """
    def __init__(self, storage_path: str = "feedback_log.jsonl"):
        self.storage_path = storage_path

    def log_feedback(self, 
                     request_id: str, 
                     prompt: str, 
                     model_used: str, 
                     response: str, 
                     rating: int, 
                     correction: Optional[str] = None, 
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Logs user feedback for a specific generation request.
        
        Args:
            request_id: Unique identifier for the request.
            prompt: The original prompt sent to the model.
            model_used: The model that generated the response (e.g., 'gemini-1.5-flash').
            response: The generated response.
            rating: User rating (e.g., 1 for thumbs up, -1 for thumbs down, or 1-5 scale).
            correction: Optional corrected response provided by the user.
            metadata: Additional context (e.g., latency, cost, user_id).
        """
        feedback_entry = {
            "timestamp": time.time(),
            "request_id": request_id,
            "prompt": prompt,
            "model_used": model_used,
            "response": response,
            "rating": rating,
            "correction": correction,
            "metadata": metadata or {}
        }
        
        try:
            with open(self.storage_path, "a") as f:
                f.write(json.dumps(feedback_entry) + "\n")
            logger.info(f"Feedback logged for request {request_id}")
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")

    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Returns basic statistics about the collected feedback.
        """
        stats = {"total_entries": 0, "average_rating": 0.0, "model_ratings": {}}
        total_rating = 0
        
        try:
            with open(self.storage_path, "r") as f:
                for line in f:
                    entry = json.loads(line)
                    stats["total_entries"] += 1
                    rating = entry.get("rating", 0)
                    total_rating += rating
                    
                    model = entry.get("model_used", "unknown")
                    if model not in stats["model_ratings"]:
                        stats["model_ratings"][model] = {"count": 0, "total_rating": 0}
                    
                    stats["model_ratings"][model]["count"] += 1
                    stats["model_ratings"][model]["total_rating"] += rating
                    
            if stats["total_entries"] > 0:
                stats["average_rating"] = total_rating / stats["total_entries"]
                
            for model, data in stats["model_ratings"].items():
                if data["count"] > 0:
                    data["average"] = data["total_rating"] / data["count"]
                    
        except FileNotFoundError:
            logger.warning(f"Feedback file {self.storage_path} not found.")
        except Exception as e:
            logger.error(f"Error reading feedback stats: {e}")
            
        return stats
