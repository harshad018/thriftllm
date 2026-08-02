import pytest
from unittest.mock import MagicMock, patch

from thriftllm.compressor import PromptCompressor, QualityGuard

def test_compressor_init_no_llmlingua():
    with patch.dict('sys.modules', {'llmlingua': None}):
        compressor = PromptCompressor(enable_llmlingua=True)
        assert compressor.enable_llmlingua is False
        assert compressor.llmlingua_model is None

def test_compressor_fallback_whitespace():
    compressor = PromptCompressor(enable_llmlingua=False)
    prompt = "This   is  a    test   prompt   with  too much   space."
    # Length is > 100 to trigger compression logic
    prompt = prompt * 3 
    
    compressed, metrics = compressor.compress(prompt)
    
    assert "  " not in compressed
    assert metrics["method"] == "whitespace_normalization"
    assert metrics["compressed_len"] < metrics["original_len"]

def test_compressor_short_prompt():
    compressor = PromptCompressor(enable_llmlingua=False)
    prompt = "Short prompt."
    
    compressed, metrics = compressor.compress(prompt)
    
    assert compressed == prompt
    assert metrics["method"] == "none"
    assert metrics["ratio"] == 1.0

@patch('thriftllm.compressor.PromptCompressor._initialize_llmlingua')
def test_compressor_with_mocked_llmlingua(mock_init):
    compressor = PromptCompressor(enable_llmlingua=True)
    # Manually set up the mock model since we patched init
    compressor.llmlingua_model = MagicMock()
    compressor.llmlingua_model.compress_prompt.return_value = {
        'compressed_prompt': "Mocked compressed text",
        'saving_tokens': 50
    }
    
    prompt = "This is a long prompt that needs to be compressed by the model." * 5
    compressed, metrics = compressor.compress(prompt)
    
    assert compressed == "Mocked compressed text"
    assert metrics["method"] == "llmlingua"
    compressor.llmlingua_model.compress_prompt.assert_called_once()

def test_quality_guard_pass():
    guard = QualityGuard()
    original = "This is a test string of reasonable length."
    compressed = "This is a test string."
    assert guard.check_quality(original, compressed) is True

def test_quality_guard_fail():
    guard = QualityGuard()
    original = "This is a very long test string that contains a lot of information and should not be compressed too much." * 5
    compressed = "Short."
    assert guard.check_quality(original, compressed) is False

def test_quality_guard_empty():
    guard = QualityGuard()
    assert guard.check_quality("", "") is True
