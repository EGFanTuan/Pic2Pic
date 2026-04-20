import os
import sys

# Add the project root to sys.path so we can import src
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import torch
import argparse
from threading import Lock
from typing import Any, Dict, Tuple, cast
from PIL import Image
import io
import json
import time
import uuid
from flask import Flask, request, jsonify, send_from_directory

from src.image_utils import invertImage, preprocessImage, cannyPreprocessor
from src.latent_utils import latentUpscale
from src.pipeline import buildPipeline
from diffusers.pipelines.controlnet.pipeline_controlnet_img2img import StableDiffusionControlNetImg2ImgPipeline

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'dist')

# Global state
pipe = None
pipe_stage1 = None
pipe_stage2 = None
controlnet_scribble = None
device = None
gpu_name = None
server_config = None
generation_lock = Lock()
MANDATORY_NEGATIVE_PREFIX = 'not safe fot work, not suitable for work, NSFW'

DEFAULT_GENERATION_PARAMS: Dict[str, Any] = {
    'prompt': 'masterpiece, best quality, anime style \n',
    'negative_prompt': 'not safe fot work, not suitable for work, NSFW, worst quality, low quality, blurry, bad anatomy, bad hands, words, text',
    'lcm_steps': 4,
    'lcm_guidance_scale': 2.5,
    'lcm_denoise': 0.9,
    'scribble_scale_stage1': 0.9,
    'canny_scale_stage1': 0.4,
    'latent_scale_factor': 1.5,
    'dpmpp_steps': 35,
    'dpmpp_guidance_scale': 8.0,
    'dpmpp_denoise': 0.6,
    'scribble_scale_stage2': 0.9,
    'seed': 143,
    'single_stage': False,
}

BASIC_MODE_PRESETS: Dict[str, Dict[str, Any]] = {
    'Noob': {
        'label': 'Noob',
        'description': '这会为unet留足发挥空间 | 选择此项如果您认为自己的草图拉完了',
        'scribble_scale_stage1': 0.6,
        'canny_scale_stage1': 0.3,
        'scribble_scale_stage2': 0.5,
    },
    'Normal': {
        'label': 'Normal',
        'description': '平衡您的想法与unet的发挥空间 | 选择此项如果您认为自己的草图是NPC水平',
        'scribble_scale_stage1': 0.8,
        'canny_scale_stage1': 0.5,
        'scribble_scale_stage2': 0.8,
    },
    'Hardcore': {
        'label': 'Hardcore',
        'description': '画面由您主导 | 选择此项如果您认为自己的草图是人上人',
        'scribble_scale_stage1': 1.1,
        'canny_scale_stage1': 0.7,
        'scribble_scale_stage2': 1.1,
    },
    'God': {
        'label': 'God',
        'description': '您将作为达芬奇 | 选择此项如果您认为自己的草图能给到夯',
        'scribble_scale_stage1': 1.3,
        'canny_scale_stage1': 0.9,
        'scribble_scale_stage2': 1.3,
    },
}

DEFAULT_BASIC_MODE_PRESET = 'Normal'


def _to_bool(value: Any) -> bool:
    """
    A simple helper to convert various truthy/falsy values to bool, for more flexible param parsing.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _has_mandatory_negative_prefix(text: str) -> bool:
    """
    Check if the text has the mandatory negative prefix.
    """
    normalized = text.strip().lower()
    return normalized.startswith(MANDATORY_NEGATIVE_PREFIX.lower())


def _apply_mandatory_negative_prefix(user_negative_prompt: str) -> str:
    """
    Add the mandatory negative prefix to the user-provided negative prompt if it's not already present.
    """
    if _has_mandatory_negative_prefix(user_negative_prompt):
        return user_negative_prompt.strip()
    extra = user_negative_prompt.strip()
    if not extra:
        return MANDATORY_NEGATIVE_PREFIX
    return f'{MANDATORY_NEGATIVE_PREFIX}, {extra}'


def _is_nsfw_flagged(flag: Any) -> bool:
    """
    Check if the given flag is NSFW (Not Safe For Work).
    """
    if flag is None:
        return False
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, (list, tuple, set)):
        return any(_is_nsfw_flagged(item) for item in flag)
    if isinstance(flag, torch.Tensor):
        return bool(torch.any(flag).item())
    return bool(flag)


def _parse_generation_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate generation parameters from the request,
    applying defaults from server config and hardcoded defaults,
    and ensuring mandatory negative prompt prefix is included.
    """
    if server_config is None:
        raise RuntimeError('Server config is not initialized')

    merged: Dict[str, Any] = {}
    merged['width'] = int(params.get('width', server_config.width))
    merged['height'] = int(params.get('height', server_config.height))
    merged['output_format'] = str(params.get('output_format', server_config.output_format)).lower()

    for key, default_val in DEFAULT_GENERATION_PARAMS.items():
        raw_val = params.get(key, default_val)
        if isinstance(default_val, bool):
            merged[key] = _to_bool(raw_val)
        elif isinstance(default_val, int):
            merged[key] = int(raw_val)
        elif isinstance(default_val, float):
            merged[key] = float(raw_val)
        else:
            merged[key] = str(raw_val)

    if merged['width'] <= 0 or merged['height'] <= 0:
        raise ValueError('width and height must be positive')
    if merged['width'] % 8 != 0 or merged['height'] % 8 != 0:
        raise ValueError('width and height must be divisible by 8')
    if merged['output_format'] not in {'png', 'jpg', 'jpeg', 'webp', 'bmp'}:
        raise ValueError('output_format must be one of png/jpg/jpeg/webp/bmp')

    merged['negative_prompt'] = _apply_mandatory_negative_prefix(merged['negative_prompt'])

    return merged

def parse_server_args():
    """  
    Parse command-line arguments for server configuration.
    Not generation parameters.
    """
    parser = argparse.ArgumentParser(description='Pic2Pic Server')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind')
    parser.add_argument('--checkpoint_name', type=str, default='dreamshaper_8.safetensors', help='Checkpoint filename in models/checkpoints/')
    parser.add_argument('--width', type=int, default=400, help='Default output width')
    parser.add_argument('--height', type=int, default=600, help='Default output height')
    parser.add_argument('--output_dir', type=str, default='./output', help='Directory to save output images')
    parser.add_argument('--output_format', type=str, default='png', choices=['png', 'jpg', 'jpeg', 'webp', 'bmp'], help='Default output image format')
    parser.add_argument('--models_path', type=str, default='./models', help='Base path for models')
    return parser.parse_args()

def initialize_models(config):
    """
    Initialize the Stable Diffusion pipelines and ControlNet models.
    """
    global pipe, pipe_stage1, pipe_stage2, controlnet_scribble, device
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Using device: {device}')
    if torch.cuda.is_available():
        global gpu_name
        gpu_name = torch.cuda.get_device_name(0)
        print(f'GPU: {gpu_name}')
        print(f'CUDA version: {torch.version.cuda}')  # type: ignore[attr-defined]
    else:
        # Try to detect if an NVIDIA GPU exists but is not usable by torch
        try:
            import subprocess
            res = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0:
                print("\n" + "!"*60)
                print("WARNING: NVIDIA GPU detected, but PyTorch is using CPU.")
                print("To enable GPU acceleration, please run:")
                print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --force-reinstall")
                print("!"*60 + "\n")
        except Exception:
            pass
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_path, '..', '..'))
    models_path = config.models_path if os.path.isabs(config.models_path) else os.path.join(project_root, config.models_path)
    
    checkpoint_path = os.path.join(models_path, 'checkpoints', config.checkpoint_name)
    controlnet_scribble_path = os.path.join(models_path, 'controlnet', 'control_v11p_sd15_scribble.pth')
    controlnet_canny_path = os.path.join(models_path, 'controlnet', 'control_v11p_sd15_canny.pth')
    
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f'Checkpoint not found: {checkpoint_path}')
    if not os.path.exists(controlnet_scribble_path):
        raise FileNotFoundError(f'ControlNet scribble not found: {controlnet_scribble_path}')
    if not os.path.exists(controlnet_canny_path):
        raise FileNotFoundError(f'ControlNet canny not found: {controlnet_canny_path}')
    
    print('Loading models...')
    pipe, pipe_stage1, pipe_stage2, controlnet_scribble = buildPipeline(
        checkpoint_path, controlnet_scribble_path, controlnet_canny_path, device
    )
    print('Models loaded successfully')
    
    os.makedirs(config.output_dir, exist_ok=True)

def decode_latents(latents: torch.Tensor) -> Image.Image:
    """
    Decode latents using VAE.
    Return the first image if batch size > 1.
    """
    if pipe is None:
        raise RuntimeError('Pipeline not initialized')

    with torch.no_grad():
        latents = latents / pipe.vae.config.scaling_factor
        image = pipe.vae.decode(latents).sample
        image = (image / 2 + 0.5).clamp(0, 1)
        image = image.cpu().permute(0, 2, 3, 1).float().numpy()
        image = (image[0] * 255).astype('uint8')
        return Image.fromarray(image)


def _load_request_image_and_params() -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Load the request image and parameters.
    """
    if 'image' not in request.files:
        raise ValueError('No image file provided')

    file = request.files['image']
    if file.filename == '':
        raise ValueError('No selected file')

    try:
        image_data = file.read()
        control_image = Image.open(io.BytesIO(image_data)).convert('RGB')
    except Exception as e:
        raise ValueError(f'Failed to load image: {e}')

    params: Dict[str, Any] = {}
    if 'params' in request.form:
        try:
            params = json.loads(request.form['params'])
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON in params: {e}')

    return control_image, params


def run_stage1(control_image: Image.Image, resolved_params: Dict[str, Any]) -> Tuple[torch.Tensor, Image.Image, Image.Image, Image.Image, bool]:
    """  
    Run the first stage of the pipeline (LCM) with the given control image and parameters.
    """
    global pipe_stage1, device

    if pipe_stage1 is None or device is None:
        raise RuntimeError('Stage1 pipeline is not initialized yet')

    width = resolved_params['width']
    height = resolved_params['height']
    prompt = resolved_params['prompt']
    negative_prompt = resolved_params['negative_prompt']
    lcm_steps = resolved_params['lcm_steps']
    lcm_guidance_scale = resolved_params['lcm_guidance_scale']
    lcm_denoise = resolved_params['lcm_denoise']
    scribble_scale_stage1 = resolved_params['scribble_scale_stage1']
    canny_scale_stage1 = resolved_params['canny_scale_stage1']
    seed = resolved_params['seed']

    control_image = control_image.resize((width, height))
    control_image = invertImage(control_image)

    control_image_scribble = preprocessImage(control_image)
    control_image_canny = cannyPreprocessor(control_image, low_threshold=50, high_threshold=100)

    control_images_stage1 = [control_image_scribble, control_image_canny]
    control_scales_stage1 = [scribble_scale_stage1, canny_scale_stage1]

    generator = torch.Generator(device=device).manual_seed(seed)

    print(f'Stage 1: LCM with {lcm_steps} steps')
    latent_h = height // 8
    latent_w = width // 8
    noise_latents = torch.randn(
        (1, pipe_stage1.unet.config.in_channels, latent_h, latent_w),
        generator=generator,
        device=device,
        dtype=pipe_stage1.unet.dtype
    )

    with torch.no_grad():
        output_stage1 = pipe_stage1(
            prompt=prompt,
            negative_prompt=negative_prompt,
            latents=noise_latents,
            image=control_images_stage1,
            control_image=control_images_stage1,
            controlnet_conditioning_scale=control_scales_stage1,
            num_inference_steps=lcm_steps,
            strength=lcm_denoise,
            guidance_scale=lcm_guidance_scale,
            generator=generator,
            output_type='latent',
            return_dict=False
        )
        nsfw = output_stage1[1]
        latents_stage1 = cast(torch.Tensor, output_stage1[0])
        nsfw_flagged = _is_nsfw_flagged(nsfw)

    print(f'Stage 1 complete, latent shape: {latents_stage1.shape}')
    print(f'NSFW detected in stage 1: {nsfw_flagged}')

    stage1_decoded = decode_latents(latents_stage1)
    return latents_stage1, stage1_decoded, control_image_canny, control_image_scribble, nsfw_flagged


def run_stage2(latents_stage1: torch.Tensor, control_image_scribble: Image.Image, resolved_params: Dict[str, Any]) -> Tuple[Image.Image, bool]:
    """   
    Run the second stage of the pipeline (DPMPP) with the latents denoised by stage1(LCM), scribble control image, and parameters.
    """
    global pipe_stage2, device

    if pipe_stage2 is None or device is None:
        raise RuntimeError('Stage2 pipeline is not initialized yet')

    width = resolved_params['width']
    height = resolved_params['height']
    prompt = resolved_params['prompt']
    negative_prompt = resolved_params['negative_prompt']
    latent_scale_factor = resolved_params['latent_scale_factor']
    dpmpp_steps = resolved_params['dpmpp_steps']
    dpmpp_guidance_scale = resolved_params['dpmpp_guidance_scale']
    dpmpp_denoise = resolved_params['dpmpp_denoise']
    scribble_scale_stage2 = resolved_params['scribble_scale_stage2']
    seed = resolved_params['seed']

    generator = torch.Generator(device=device).manual_seed(seed)

    print(f'Upscaling latents by factor {latent_scale_factor}')
    latents_upscaled = latentUpscale(
        latents_stage1,
        scale_factor=latent_scale_factor,
        mode='nearest-exact'
    )

    print(f'Stage 2: DPMPP with {dpmpp_steps} steps')
    new_width = int(width * latent_scale_factor)
    new_height = int(height * latent_scale_factor)
    control_image_stage2 = control_image_scribble.resize((new_width, new_height))

    with torch.no_grad():
        output_stage2 = pipe_stage2(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=latents_upscaled,
            control_image=control_image_stage2,
            controlnet_conditioning_scale=scribble_scale_stage2,
            num_inference_steps=dpmpp_steps,
            strength=dpmpp_denoise,
            guidance_scale=dpmpp_guidance_scale,
            generator=generator,
            return_dict=False
        )
        output_stage2_any = cast(Any, output_stage2)
        nsfw_stage2 = output_stage2_any[1]
        image_final = cast(Image.Image, output_stage2_any[0][0])
        nsfw_stage2_flagged = _is_nsfw_flagged(nsfw_stage2)

    print(f'Stage 2 complete, output image size: {image_final.size}')
    print(f'NSFW detected in stage 2: {nsfw_stage2_flagged}')
    return image_final, nsfw_stage2_flagged

def generate_image(control_image: Image.Image, params: Dict[str, Any]) -> Tuple[Image.Image, Image.Image, Image.Image, Dict[str, Any], bool, bool]:
    """
    Generate image from control image with given parameters.
    It will run both stage1 and stage2.
    Returns tuple (final_image, stage1_decoded_image, canny_image)
    """
    global pipe, pipe_stage1, pipe_stage2, device

    if pipe is None or pipe_stage1 is None or pipe_stage2 is None or device is None:
        raise RuntimeError('Pipelines are not initialized yet')

    resolved_params = _parse_generation_params(params)
    
    if resolved_params['single_stage']:
        raise NotImplementedError('Single-stage generation is deprecated')

    latents_stage1, stage1_decoded, control_image_canny, control_image_scribble, stage1_nsfw = run_stage1(
        control_image,
        resolved_params,
    )
    image_final, stage2_nsfw = run_stage2(latents_stage1, control_image_scribble, resolved_params)
    
    return image_final, stage1_decoded, control_image_canny, resolved_params, stage1_nsfw, stage2_nsfw


@app.route('/preview', methods=['POST'])
def handle_preview():
    """
    Handle preview requests  for fast feedback on stage1 results.
    Run stage1 with the given control image and parameters, return the decoded stage1 image and canny image for preview.
    """
    if pipe is None:
        return jsonify({'error': 'Model is not ready'}), 503

    if not generation_lock.acquire(blocking=False):
        return jsonify({'error': 'Server is busy generating. Please retry shortly.'}), 429

    try:
        control_image, params = _load_request_image_and_params()
        resolved_params = _parse_generation_params(params)
        if resolved_params['single_stage']:
            raise ValueError('single_stage is deprecated')

        _, stage1_image, canny_image, _, stage1_nsfw = run_stage1(control_image, resolved_params)
    except ValueError as e:
        return jsonify({'error': f'Invalid request: {e}'}), 400
    except Exception as e:
        return jsonify({'error': f'Preview failed: {e}'}), 500
    finally:
        generation_lock.release()

    if stage1_nsfw:
        return jsonify({
            'success': False,
            'warning': 'Preview blocked: NSFW content detected in stage1 output.',
            'nsfw_blocked': True,
        })

    if server_config is None:
        return jsonify({'error': 'Server config is not initialized'}), 500

    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    base_name = f'preview_{timestamp}_{unique_id}'

    stage1_path = os.path.join(server_config.output_dir, f'{base_name}_stage1.png')
    canny_path = os.path.join(server_config.output_dir, f'{base_name}_canny.png')
    stage1_image.save(stage1_path)
    canny_image.save(canny_path)

    return jsonify({
        'success': True,
        'stage1_image': f'{base_name}_stage1.png',
        'canny_image': f'{base_name}_canny.png',
        'output_dir': server_config.output_dir,
        'resolved_params': resolved_params,
        'preview_urls': {
            'stage1': f'/outputs/{base_name}_stage1.png',
            'canny': f'/outputs/{base_name}_canny.png',
        }
    })

@app.route('/generate', methods=['POST'])
def handle_generate():
    """
    Handle generate requests for full image generation.
    Run both stage1 and stage2 with the given control image and parameters, return the final generated image, stage1 decoded image, and canny image.
    """
    if pipe is None:
        return jsonify({'error': 'Model is not ready'}), 503

    try:
        control_image, params = _load_request_image_and_params()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # Generate (single-flight to avoid concurrent GPU OOM/race)
    if not generation_lock.acquire(blocking=False):
        return jsonify({'error': 'Server is busy generating. Please retry shortly.'}), 429

    try:
        final_image, stage1_image, canny_image, resolved_params, stage1_nsfw, stage2_nsfw = generate_image(
            control_image, params
        )
    except ValueError as e:
        return jsonify({'error': f'Invalid params: {e}'}), 400
    except Exception as e:
        return jsonify({'error': f'Generation failed: {e}'}), 500
    finally:
        generation_lock.release()

    if server_config is None:
        return jsonify({'error': 'Server config is not initialized'}), 500

    if stage1_nsfw or stage2_nsfw:
        return jsonify({
            'success': False,
            'warning': 'Final output blocked: NSFW content detected, image will not be returned to frontend.',
            'nsfw_blocked': True,
            'resolved_params': resolved_params,
        })
    
    # Save images
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    base_name = f'output_{timestamp}_{unique_id}'
    
    # Save stage1 decoded latent image
    stage1_path = os.path.join(server_config.output_dir, f'{base_name}_stage1.png')
    stage1_image.save(stage1_path)
    
    # Save canny image
    canny_path = os.path.join(server_config.output_dir, f'{base_name}_canny.png')
    canny_image.save(canny_path)
    
    # Save final image
    output_format = resolved_params['output_format']
    final_path = os.path.join(server_config.output_dir, f'{base_name}_final.{output_format}')
    if output_format in ['jpg', 'jpeg']:
        rgb_image = final_image.convert('RGB')
        rgb_image.save(final_path, quality=95)
    else:
        final_image.save(final_path)
    
    # Prepare response
    response = {
        'success': True,
        'stage1_image': f'{base_name}_stage1.png',
        'canny_image': f'{base_name}_canny.png',
        'final_image': f'{base_name}_final.{output_format}',
        'output_dir': server_config.output_dir,
        'resolved_params': resolved_params,
        'preview_urls': {
            'stage1': f'/outputs/{base_name}_stage1.png',
            'canny': f'/outputs/{base_name}_canny.png',
            'final': f'/outputs/{base_name}_final.{output_format}',
        }
    }
    
    return jsonify(response)


@app.route('/', methods=['GET'])
def index_page():
    return send_from_directory(WEB_DIR, 'index.html')

@app.route('/outputs/<path:filename>', methods=['GET'])
def get_output_file(filename):
    if server_config is None:
        return jsonify({'error': 'Server config is not initialized'}), 500
    return send_from_directory(server_config.output_dir, filename)


@app.route('/status', methods=['GET'])
def status():
    defaults = {
        **DEFAULT_GENERATION_PARAMS,
        'width': server_config.width if server_config else None,
        'height': server_config.height if server_config else None,
        'output_format': server_config.output_format if server_config else None,
    }

    return jsonify({
        'status': 'ready' if pipe is not None else 'initializing',
        'busy': generation_lock.locked(),
        'device': device,
        'gpu_name': gpu_name,
        'defaults': defaults,
        'basic_mode': {
            'default_preset': DEFAULT_BASIC_MODE_PRESET,
            'presets': BASIC_MODE_PRESETS,
            'note': '普通模式会自动设置三项关键控制强度（S1 Scribble / S1 Canny / S2 Scribble）。',
        },
        'config': {
            'checkpoint_name': server_config.checkpoint_name if server_config else None,
            'width': server_config.width if server_config else None,
            'height': server_config.height if server_config else None,
            'output_dir': server_config.output_dir if server_config else None,
            'output_format': server_config.output_format if server_config else None,
        }
    })

@app.route('/switch_device', methods=['POST'])
def switch_device():
    """
    Switch between CPU and GPU.
    """
    global device, pipe, pipe_stage1, pipe_stage2
    
    if pipe is None:
        return jsonify({'error': 'Server not ready'}), 400
        
    target = request.json.get('device', 'cpu')
    if target == 'cuda' and not torch.cuda.is_available():
        return jsonify({'error': 'CUDA not available'}), 400
        
    with generation_lock:
        try:
            device = target
            if pipe:
                # Cast to float32 for CPU (fp16 not supported on CPU)
                # Cast to float16 for GPU (performance/memory optimization)
                dtype = torch.float16 if device == 'cuda' else torch.float32
                pipe = pipe.to(device=device, dtype=dtype)
                
            # Update stage pipelines
            if pipe_stage2 and pipe:
                pipe_stage2 = StableDiffusionControlNetImg2ImgPipeline(**pipe.components)
                pipe_stage2.controlnet = controlnet_scribble
            
            return jsonify({'status': 'success', 'device': device, 'gpu_name': gpu_name})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    config = parse_server_args()
    server_config = config
    
    # Start model initialization in a background thread
    import threading
    init_thread = threading.Thread(target=initialize_models, args=(config,), daemon=True)
    init_thread.start()
    
    print(f'Server starting on http://{config.host}:{config.port}')
    print('Models are loading in the background...')
    app.run(host=config.host, port=config.port, debug=False)