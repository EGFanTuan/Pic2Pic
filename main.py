import os
import argparse
import torch
import numpy as np
from PIL import Image
from diffusers.pipelines.controlnet.pipeline_controlnet import StableDiffusionControlNetPipeline
from diffusers.models.controlnets.controlnet import ControlNetModel
from diffusers.schedulers.scheduling_euler_discrete import EulerDiscreteScheduler
from diffusers.utils.loading_utils import load_image
import PIL.ImageOps


def preprocess_scribble(image):
    image = image.convert("L")
    image = np.array(image)
    image = image[:, :, None]
    image = np.concatenate([image, image, image], axis=2)
    image = Image.fromarray(image)
    return image


def main():
    parser = argparse.ArgumentParser(description='Line Art to Image using ControlNet')
    parser.add_argument('--input', type=str, default="./input.png", help='Path to input line art image')
    parser.add_argument('--output', type=str, default='output.png', help='Path to save output image')
    parser.add_argument('--prompt', type=str, default=None, help='Positive prompt')
    parser.add_argument('--negative_prompt', type=str, default=None, help='Negative prompt')
    parser.add_argument('--steps', type=int, default=25, help='Number of inference steps')
    parser.add_argument('--guidance_scale', type=float, default=7.5, help='Guidance scale')
    parser.add_argument('--controlnet_conditioning_scale', type=float, default=1.0, help='ControlNet conditioning scale')
    parser.add_argument('--width', type=int, default=512, help='Output width')
    parser.add_argument('--height', type=int, default=744, help='Output height')
    parser.add_argument('--controlnet_type', type=str, default='canny', choices=['canny', 'scribble'], help='Which ControlNet to use')
    parser.add_argument('--invert_input', action='store_true', help='Invert input image (ControlNets prefer white lines on black background)')
    
    args = parser.parse_args()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")  # type: ignore
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    models_path = os.path.join(base_path, "models")
    
    checkpoint_path = os.path.join(models_path, "checkpoints", "dreamshaper_8.safetensors")
    
    if args.controlnet_type == 'canny':
        controlnet_filename = "control_v11p_sd15_canny.pth"
    else:
        controlnet_filename = "control_v11p_sd15_scribble.pth"
        
    controlnet_path = os.path.join(models_path, "controlnet", controlnet_filename)

    
    default_positive_prompt = "masterpiece, best quality, anime style, cute girl, detailed, colorful"
    default_negative_prompt = "worst quality, low quality, blurry, bad anatomy, bad hands"
    
    positive_prompt = args.prompt if args.prompt is not None else default_positive_prompt
    negative_prompt = args.negative_prompt if args.negative_prompt is not None else default_negative_prompt
    
    print(f"Positive prompt: {positive_prompt}")
    print(f"Negative prompt: {negative_prompt}")
    
    print("Loading ControlNet model...")
    controlnet = ControlNetModel.from_single_file(
        controlnet_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=False
    )
    
    print("Loading Stable Diffusion pipeline...")
    pipe = StableDiffusionControlNetPipeline.from_single_file(
        checkpoint_path,
        controlnet=controlnet,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
        safety_checker=None
    )
    
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    
    if device == "cuda":
        pipe = pipe.to(device)
        pipe.enable_xformers_memory_efficient_attention() if hasattr(pipe, 'enable_xformers_memory_efficient_attention') else None
    else:
        pipe = pipe.to(device)
    
    print(f"Loading input image: {args.input}")
    control_image = load_image(args.input)
    control_image = control_image.resize((args.width, args.height))
    if args.invert_input:
        control_image = PIL.ImageOps.invert(control_image.convert("RGB"))
    
    control_image = preprocess_scribble(control_image)
    
    print("Generating image...")
    generator = torch.Generator(device=device).manual_seed(42)
    
    with torch.no_grad():
        output = pipe(
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            image=control_image,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance_scale,
            controlnet_conditioning_scale=args.controlnet_conditioning_scale,
            width=args.width,
            height=args.height,
            generator=generator
        )
        image = output.images[0]  # type: ignore
    
    print(f"Saving output image to: {args.output}")
    image.save(args.output)
    print("Done!")


if __name__ == "__main__":
    main()
