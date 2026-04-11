import os
import argparse
import torch
import numpy as np
from PIL import Image, ImageOps
from diffusers.pipelines.controlnet.pipeline_controlnet import StableDiffusionControlNetPipeline
from diffusers.pipelines.controlnet.pipeline_controlnet_img2img import StableDiffusionControlNetImg2ImgPipeline
from diffusers.models.controlnets.controlnet import ControlNetModel
from diffusers.schedulers.scheduling_euler_discrete import EulerDiscreteScheduler
from diffusers.schedulers.scheduling_ddim import DDIMScheduler
from diffusers.schedulers.scheduling_dpmsolver_multistep import DPMSolverMultistepScheduler
from diffusers.schedulers.scheduling_lcm import LCMScheduler
from diffusers.utils.loading_utils import load_image


def preprocess_image(image):
    image = image.convert("L")
    image = np.array(image)
    image = image[:, :, None]
    image = np.concatenate([image, image, image], axis=2)
    image = Image.fromarray(image)
    return image


def latent_upscale(latents, scale_factor=1.5, mode='nearest-exact'):
    """
    Upscale latent tensor similar to ComfyUI's LatentUpscaleBy node.
    Args:
        latents: torch.Tensor of shape (batch, channels, height, width)
        scale_factor: scaling factor
        mode: interpolation mode ('nearest-exact', 'bilinear', 'bicubic')
    Returns:
        Upscaled latents
    """
    import torch.nn.functional as F
    
    if mode == 'nearest-exact':
        mode = 'nearest'
    
    batch, channels, height, width = latents.shape
    new_height = int(height * scale_factor)
    new_width = int(width * scale_factor)
    
    upscaled = F.interpolate(
        latents,
        size=(new_height, new_width),
        mode=mode,
        align_corners=False if mode in ['bilinear', 'bicubic'] else None
    )
    return upscaled


SUPPORTED_INPUT_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif')
SUPPORTED_OUTPUT_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')


def get_input_images(input_dir):
    input_images = []
    if os.path.exists(input_dir):
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(SUPPORTED_INPUT_FORMATS):
                input_images.append(os.path.join(input_dir, filename))
    return sorted(input_images)


def main():
    parser = argparse.ArgumentParser(description='Line Art to Image using Dual ControlNet')
    parser.add_argument('--input_dir', type=str, default="./input", help='Directory with input images')
    parser.add_argument('--output_dir', type=str, default="./output", help='Directory to save output images')
    parser.add_argument('--output_format', type=str, default='png', choices=['png', 'jpg', 'jpeg', 'webp', 'bmp'], help='Output image format')
    parser.add_argument('--prompt', type=str, default="masterpiece, best quality, anime style, landscape \n", help='Positive prompt')
    parser.add_argument('--negative_prompt', type=str, default="not safe fot work, not suitable for work, NSFW, worst quality, low quality, blurry, bad anatomy, bad hands, words, text，", help='Negative prompt')
    parser.add_argument('--width', type=int, default=400, help='Output width')
    parser.add_argument('--height', type=int, default=600, help='Output height')
    parser.add_argument('--scribble_scale', type=float, default=0.9, help='Scribble ControlNet scale')
    parser.add_argument('--canny_scale', type=float, default=0.4, help='Canny ControlNet scale')
    parser.add_argument('--steps', type=int, default=30, help='Number of inference steps')
    parser.add_argument('--guidance_scale', type=float, default=8.0, help='Guidance scale')
    parser.add_argument('--single_stage', action='store_true', default=False, help='Use single-stage generation instead of two-stage (LCM + DPMPP)')
    parser.add_argument('--lcm_steps', type=int, default=4, help='Number of LCM inference steps')
    parser.add_argument('--dpmpp_steps', type=int, default=15, help='Number of DPM++ inference steps')
    parser.add_argument('--latent_scale_factor', type=float, default=1.5, help='Latent upscale factor between stages')
    parser.add_argument('--lcm_guidance_scale', type=float, default=2.5, help='Guidance scale for LCM stage')
    parser.add_argument('--dpmpp_guidance_scale', type=float, default=8.0, help='Guidance scale for DPM++ stage')
    parser.add_argument('--lcm_denoise', type=float, default=0.9, help='Denoise strength for LCM stage')
    parser.add_argument('--dpmpp_denoise', type=float, default=0.6, help='Denoise strength for DPM++ stage')
    parser.add_argument('--scribble_scale_stage1', type=float, default=0.8, help='Scribble ControlNet scale for first stage')
    parser.add_argument('--canny_scale_stage1', type=float, default=0.4, help='Canny ControlNet scale for first stage')
    parser.add_argument('--scribble_scale_stage2', type=float, default=0.8, help='Scribble ControlNet scale for second stage')

    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")  # type: ignore

    base_path = os.path.dirname(os.path.abspath(__file__))
    models_path = os.path.join(base_path, "models")

    checkpoint_path = os.path.join(models_path, "checkpoints", "dreamshaper_8.safetensors")
    controlnet_scribble_path = os.path.join(models_path, "controlnet", "control_v11p_sd15_scribble.pth")
    controlnet_canny_path = os.path.join(models_path, "controlnet", "control_v11p_sd15_canny.pth")

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.input_dir, exist_ok=True)

    positive_prompt = args.prompt
    negative_prompt = args.negative_prompt

    print(f"Positive prompt: {positive_prompt}")
    print(f"Negative prompt: {negative_prompt}")

    print("Loading ControlNet models...")
    controlnet_scribble = ControlNetModel.from_single_file(
        controlnet_scribble_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=False
    )

    controlnet_canny = ControlNetModel.from_single_file(
        controlnet_canny_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=False
    )

    controlnets = [controlnet_scribble, controlnet_canny]

    print("Loading Stable Diffusion pipeline...")
    pipe = StableDiffusionControlNetPipeline.from_single_file(
        checkpoint_path,
        controlnet=controlnets,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
        safety_checker=None
    )

    print("Initializing Img2Img pipeline...")
    pipe_i2i = StableDiffusionControlNetImg2ImgPipeline(**pipe.components)

    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)  # type: ignore
    pipe_i2i.scheduler = pipe.scheduler

    if device == "cuda":
        # 释放现代 N卡 (Ampere架构及以上, 如 RTX 30/40系) 的 TF32 并发性能
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        pipe = pipe.to(device)
        pipe_i2i = pipe_i2i.to(device)
        try:
            pipe.enable_xformers_memory_efficient_attention()
            pipe_i2i.enable_xformers_memory_efficient_attention()
        except (ImportError, ModuleNotFoundError, ValueError):
            print("xformers不在线 - 退回到 PyTorch 2.0 极速原生 SDPA 注意力机制，不使用龟速切片")
        
        # 开启 VAE 及模型的显存重切片/Tiling策略 (有效拉低出图瞬间的峰值显存占用, 且影响极小的时间)
        pipe.vae.enable_tiling()
        pipe_i2i.vae.enable_tiling()
        # 仅推荐在显存极小(如≤6GB)时开启如下两行CPU自动卸载，否则保持常驻显存可保证连续出图最快
        # pipe.enable_model_cpu_offload()
        # pipe_i2i.enable_model_cpu_offload()
    else:
        pipe = pipe.to(device)
        pipe_i2i = pipe_i2i.to(device)

    input_images = get_input_images(args.input_dir)
    print(f"Found {len(input_images)} input images in {args.input_dir}")
    print(f"Supported input formats: {', '.join(SUPPORTED_INPUT_FORMATS)}")

    if not input_images:
        print(f"No supported images found in {args.input_dir}")
        return

    for idx, img_path in enumerate(input_images):
        print(f"\nProcessing {idx + 1}/{len(input_images)}: {os.path.basename(img_path)}")

        control_image = load_image(img_path)
        control_image = control_image.resize((args.width, args.height))

        control_image_inverted = ImageOps.invert(control_image.convert("RGB"))
        control_image_processed = preprocess_image(control_image_inverted)

        control_images = [control_image_processed, control_image_processed]
        
        generator = torch.Generator(device=device).manual_seed(42)

        if not args.single_stage:
            print("Two-stage generation (LCM + DPMPP) like ComfyUI workflow")
            print(f"Stage 1: LCM with {args.lcm_steps} steps, guidance={args.lcm_guidance_scale}, denoise={args.lcm_denoise}")
            
            # Stage 1: LCM with both ControlNets
            pipe_i2i.scheduler = LCMScheduler.from_config(pipe_i2i.scheduler.config)  # type: ignore
            control_scales_stage1 = [args.scribble_scale_stage1, args.canny_scale_stage1]
            
            blank_image = Image.new("RGB", (args.width, args.height), (127, 127, 127))
            
            with torch.no_grad():
                output_stage1 = pipe_i2i(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    image=blank_image,
                    control_image=control_images,
                    controlnet_conditioning_scale=control_scales_stage1,
                    num_inference_steps=int(args.lcm_steps / args.lcm_denoise),
                    strength=args.lcm_denoise,
                    guidance_scale=args.lcm_guidance_scale,
                    generator=generator,
                    output_type="latent",  # Get latents for upscaling
                    return_dict=False
                )
                latents_stage1: torch.Tensor = output_stage1[0]  # type: ignore
            
            print(f"Stage 1 complete, latent shape: {latents_stage1.shape}")
            
            # Latent upscaling
            print(f"Upscaling latents by factor {args.latent_scale_factor}")
            latents_upscaled = latent_upscale(
                latents_stage1, 
                scale_factor=args.latent_scale_factor,
                mode='nearest-exact'
            )
            
            with torch.no_grad():
                upscaled_image_pt = pipe.vae.decode(latents_upscaled / pipe.vae.config.scaling_factor, return_dict=False)[0]
                upscaled_image_pt = (upscaled_image_pt / 2 + 0.5).clamp(0, 1)
                upscaled_image_np = upscaled_image_pt.cpu().permute(0, 2, 3, 1).numpy()
                upscaled_image_pil = pipe.numpy_to_pil(upscaled_image_np)[0]

            # Stage 2: DPMPP with only scribble ControlNet
            print(f"Stage 2: DPMPP with {args.dpmpp_steps} steps, guidance={args.dpmpp_guidance_scale}, denoise={args.dpmpp_denoise}")
            pipe_i2i.scheduler = DPMSolverMultistepScheduler.from_config(
                pipe_i2i.scheduler.config,  # type: ignore
                use_karras_sigmas=True
            )
            # Only use scribble ControlNet for stage 2 (set canny scale to 0)
            control_scales_stage2 = [args.scribble_scale_stage2, 0.0]
            
            new_width = int(args.width * args.latent_scale_factor)
            new_height = int(args.height * args.latent_scale_factor)
            control_images_stage2 = [img.resize((new_width, new_height)) for img in control_images]
            
            with torch.no_grad():
                output_stage2 = pipe_i2i(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    image=upscaled_image_pil,
                    control_image=control_images_stage2,
                    controlnet_conditioning_scale=control_scales_stage2,
                    num_inference_steps=int(args.dpmpp_steps / args.dpmpp_denoise),
                    strength=args.dpmpp_denoise,
                    guidance_scale=args.dpmpp_guidance_scale,
                    generator=generator,
                    return_dict=False
                )
                image_final: Image.Image = output_stage2[0][0]  # type: ignore
        
        else:
            print("Single-stage generation")
            control_scales = [args.scribble_scale, args.canny_scale]
            
            with torch.no_grad():
                output = pipe(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    image=control_images,
                    controlnet_conditioning_scale=control_scales,
                    num_inference_steps=args.steps,
                    guidance_scale=args.guidance_scale,
                    width=args.width,
                    height=args.height,
                    generator=generator,
                    return_dict=False
                )
                image_final: Image.Image = output[0][0]  # type: ignore

        base_name = os.path.splitext(os.path.basename(img_path))[0]
        output_ext = f".{args.output_format}"
        output_path = os.path.join(args.output_dir, f"{base_name}_output{output_ext}")

        print(f"Saving to: {output_path}")

        if args.output_format in ['jpg', 'jpeg']:
            rgb_image = image_final.convert('RGB')
            rgb_image.save(output_path, quality=95)
        else:
            image_final.save(output_path)

    print("\nAll done!")
    print(f"Output format: {args.output_format}")
    print(f"Supported output formats: {', '.join(SUPPORTED_OUTPUT_FORMATS)}")


if __name__ == "__main__":
    main()
