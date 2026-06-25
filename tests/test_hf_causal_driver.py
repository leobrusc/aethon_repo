"""Tests for HuggingFaceCausalLMDriver device_map / accelerate compatibility."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def _mock_torch_cuda(monkeypatch):
    """Patch torch.cuda.is_available to return True."""
    with patch("models.hf_causal_driver.torch") as mock_torch:
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
        yield mock_torch


@pytest.fixture
def _mock_torch_cpu(monkeypatch):
    """Patch torch.cuda.is_available to return False."""
    with patch("models.hf_causal_driver.torch") as mock_torch:
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float16 = "float16"
        yield mock_torch


@patch("models.hf_causal_driver.pipeline")
@patch("models.hf_causal_driver.AutoModelForCausalLM")
@patch("models.hf_causal_driver.AutoTokenizer")
def test_device_map_auto_no_device_arg(mock_tok, mock_model, mock_pipe, _mock_torch_cuda):
    """When CUDA is available, pipeline must NOT receive a device argument."""
    from models.hf_causal_driver import HuggingFaceCausalLMDriver

    mock_tok.from_pretrained.return_value = MagicMock()
    mock_model.from_pretrained.return_value = MagicMock()
    mock_pipe.return_value = MagicMock()

    driver = HuggingFaceCausalLMDriver(model_id="test/model", name="test")

    assert driver._use_device_map is True
    call_kwargs = mock_pipe.call_args[1]
    assert "device" not in call_kwargs


@patch("models.hf_causal_driver.pipeline")
@patch("models.hf_causal_driver.AutoModelForCausalLM")
@patch("models.hf_causal_driver.AutoTokenizer")
def test_cpu_fallback_passes_device(mock_tok, mock_model, mock_pipe, _mock_torch_cpu):
    """When CUDA is not available, pipeline receives device=-1."""
    from models.hf_causal_driver import HuggingFaceCausalLMDriver

    mock_tok.from_pretrained.return_value = MagicMock()
    mock_model.from_pretrained.return_value = MagicMock()
    mock_pipe.return_value = MagicMock()

    driver = HuggingFaceCausalLMDriver(model_id="test/model", name="test")

    assert driver._use_device_map is False
    call_kwargs = mock_pipe.call_args[1]
    assert call_kwargs["device"] == -1


@patch("models.hf_causal_driver.pipeline")
@patch("models.hf_causal_driver.AutoModelForCausalLM")
@patch("models.hf_causal_driver.AutoTokenizer")
def test_available_property_true(mock_tok, mock_model, mock_pipe, _mock_torch_cpu):
    """Driver.available is True when gen pipeline loaded successfully."""
    from models.hf_causal_driver import HuggingFaceCausalLMDriver

    mock_tok.from_pretrained.return_value = MagicMock()
    mock_model.from_pretrained.return_value = MagicMock()
    mock_pipe.return_value = MagicMock()

    driver = HuggingFaceCausalLMDriver(model_id="test/model", name="test")
    assert driver.available is True


@patch("models.hf_causal_driver.AutoModelForCausalLM")
@patch("models.hf_causal_driver.AutoTokenizer")
def test_available_property_false_on_load_error(mock_tok, mock_model, _mock_torch_cpu):
    """Driver.available is False when model loading fails."""
    from models.hf_causal_driver import HuggingFaceCausalLMDriver

    mock_tok.from_pretrained.side_effect = RuntimeError("download failed")

    driver = HuggingFaceCausalLMDriver(model_id="test/model", name="test")
    assert driver.available is False
    assert driver.gen is None
