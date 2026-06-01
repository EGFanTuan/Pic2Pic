import pytest
import sys
import os
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipeline import buildPipeline

@pytest.mark.slow
def test_real_pipeline_build():
    """
    This test actually builds the pipeline using the real models.
    It will fail if models are not downloaded or run out of GPU memory.
    Run explicitly with: pytest test/test_pipeline_real.py
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    models_path = os.path.join(base_path, '..', 'models')
    
    checkpoint_path = os.path.join(models_path, 'checkpoints', 'dreamshaper_8.safetensors')
    controlnet_scribble_path = os.path.join(models_path, 'controlnet', 'control_v11p_sd15_scribble.pth')
    controlnet_canny_path = os.path.join(models_path, 'controlnet', 'control_v11p_sd15_canny.pth')
    
    # Skip if missing files
    if not os.path.exists(checkpoint_path):
        pytest.skip(f"Model file not found: {checkpoint_path}")
        
    try:
        pipe, pipe_stage1, pipe_stage2, _ = buildPipeline(
            checkpoint_path, controlnet_scribble_path, controlnet_canny_path, device
        )
        assert pipe is not None
        assert pipe_stage1 is not None
        assert pipe_stage2 is not None
    except Exception as e:
        pytest.fail(f"Pipeline building failed: {e}")
