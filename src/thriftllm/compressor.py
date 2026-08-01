import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PromptCompressor:
    """
    Compresses prompts to reduce token count and inference costs,
    utilizing LLMLingua for semantic compression while preserving key information.
    """
    def __init__(self, target_ratio: float = 0.5, enable_llmlingua: bool = True):
        self.target_ratio = target_ratio
        self.enable_llmlingua = enable_llmlingua
        self.llmlingua_model = None

        if self.enable_llmlingua:
            self._initialize_llmlingua()

    def _initialize_llmlingua(self):
        try:
            from llmlingua import PromptCompressor as LLMLinguaCompressor
            # Initialize with a small model for speed, or allow configuration
            self.llmlingua_model = LLMLinguaCompressor(
                model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
                use_auth_token=False
            )
            logger.info("LLMLingua initialized successfully.")
        except ImportError:
            logger.warning("llmlingua package not found. Falling back to basic compression.")
            self.enable_llmlingua = False
        except Exception as e:
            logger.error(f"Failed to initialize LLMLingua: {e}")
            self.enable_llmlingua = False

    def compress(self, prompt: str, context: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Compresses the prompt and returns the compressed string along with metrics.
        """
        original_length = len(prompt)
        if original_length < 100:
            # Too short to bother compressing
            return prompt, {"original_len": original_length, "compressed_len": original_length, "ratio": 1.0, "method": "none"}

        if self.enable_llmlingua and self.llmlingua_model:
            try:
                # LLMLingua compression
                results = self.llmlingua_model.compress_prompt(
                    context=[context] if context else [],
                    instruction=prompt,
                    question="",
                    target_token=int(original_length * self.target_ratio),
                    condition_compare=True,
                    condition_in_question='after',
                    rank_method='longllmlingua',
                    use_context_level_fallback=True
                )
                compressed_prompt = results['compressed_prompt']
                metrics = {
                    "original_len": original_length,
                    "compressed_len": len(compressed_prompt),
                    "ratio": len(compressed_prompt) / original_length,
                    "method": "llmlingua",
                    "saving_tokens": results.get('saving_tokens', 0)
                }
                return compressed_prompt, metrics
            except Exception as e:
                logger.error(f"LLMLingua compression failed: {e}. Falling back.")

        # Fallback: Basic heuristic compression (e.g., removing excessive whitespace)
        compressed_prompt = " ".join(prompt.split())
        metrics = {
            "original_len": original_length,
            "compressed_len": len(compressed_prompt),
            "ratio": len(compressed_prompt) / original_length if original_length > 0 else 1.0,
            "method": "whitespace_normalization"
        }
        return compressed_prompt, metrics

class QualityGuard:
    """
    Ensures that compression or caching doesn't degrade the prompt quality below an acceptable threshold.
    """
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def check_quality(self, original: str, compressed: str) -> bool:
        """
        Basic length-based heuristic for now. If it's compressed to less than 10% of original,
        it might have lost too much meaning.
        Future: Use sentence-transformers to check semantic similarity.
        """
        if len(original) == 0:
            return True
        ratio = len(compressed) / len(original)
        if ratio < 0.1:
            logger.warning(f"QualityGuard triggered: Compression ratio {ratio:.2f} is suspiciously low.")
            return False
        return True
