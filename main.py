import os
import torch
from PIL import Image
from diffusers.schedulers.scheduling_dpmsolver_multistep import DPMSolverMultistepScheduler
from diffusers.schedulers.scheduling_lcm import LCMScheduler
from diffusers.utils.loading_utils import load_image

from src.image_utils import SUPPORTED_INPUT_FORMATS, SUPPORTED_OUTPUT_FORMATS, invertImage, preprocessImage, cannyPreprocessor, getInputImages
from src.latent_utils import latentUpscale
from src.config import parseArgs
from src.pipeline import buildPipeline

def main():
    args = parseArgs()

    # check cuda availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")  # type: ignore

    # path preparation
    base_path = os.path.dirname(os.path.abspath(__file__))
    models_path = os.path.join(base_path, "models")

    checkpoint_path = os.path.join(models_path, "checkpoints", args.checkpoint_name)
    controlnet_scribble_path = os.path.join(models_path, "controlnet", "control_v11p_sd15_scribble.pth")
    controlnet_canny_path = os.path.join(models_path, "controlnet", "control_v11p_sd15_canny.pth")

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.input_dir, exist_ok=True)

    positive_prompt = args.prompt
    negative_prompt = args.negative_prompt

    print(f"Positive prompt: {positive_prompt}")
    print(f"Negative prompt: {negative_prompt}")

    # load models and pipelines
    pipe, pipe_stage1, pipe_stage2, controlnet_scribble = buildPipeline(
        checkpoint_path, controlnet_scribble_path, controlnet_canny_path, device
    )

    # collect input images
    input_images = getInputImages(args.input_dir)
    print(f"Found {len(input_images)} input images in {args.input_dir}")
    print(f"Supported input formats: {', '.join(SUPPORTED_INPUT_FORMATS)}")

    if not input_images:
        print(f"No supported images found in {args.input_dir}")
        return

    # process each image
    for idx, img_path in enumerate(input_images):
        print(f"\nProcessing {idx + 1}/{len(input_images)}: {os.path.basename(img_path)}")

        # resize to target size
        control_image = load_image(img_path)
        control_image = control_image.resize((args.width, args.height))

        # invert image for controlnet input
        control_image = invertImage(control_image)
        
        # nothing for scribble
        control_image_scribble = preprocessImage(control_image)
        # canny detection
        control_image_canny = cannyPreprocessor(control_image, low_threshold=50, high_threshold=100)

        # stage1 controlnet image input
        control_images_stage1 = [control_image_scribble, control_image_canny]
        
        # random seed
        generator = torch.Generator(device=device).manual_seed(143)

        if not args.single_stage:
            print(f"Stage 1: LCM with {args.lcm_steps} steps, guidance={args.lcm_guidance_scale}, denoise={args.lcm_denoise}")
            
            # Stage 1: LCM with both ControlNets
            control_scales_stage1 = [args.scribble_scale_stage1, args.canny_scale_stage1]

            # Use pure noise latent as stage-1 input
            latent_h = args.height // 8
            latent_w = args.width // 8
            noise_latents = torch.randn(
                (1, pipe_stage1.unet.config.in_channels, latent_h, latent_w),
                generator=generator,
                device=device,
                dtype=pipe_stage1.unet.dtype
            )
            
            with torch.no_grad():
                output_stage1 = pipe_stage1(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    latents=noise_latents,
                    image=control_images_stage1,
                    control_image=control_images_stage1,
                    controlnet_conditioning_scale=control_scales_stage1,
                    num_inference_steps=args.lcm_steps,
                    strength=args.lcm_denoise,
                    guidance_scale=args.lcm_guidance_scale,
                    generator=generator,
                    output_type="latent",  # Get latents for upscaling
                    return_dict=False
                )
                nsfw: bool = output_stage1[1]  # type: ignore
                latents_stage1: torch.Tensor = output_stage1[0]  # type: ignore
            
            print(f"Stage 1 complete, latent shape: {latents_stage1.shape}")
            print(f"NSFW detected in stage 1: {nsfw}")
            
            # Latent upscaling
            print(f"Upscaling latents by factor {args.latent_scale_factor}")
            latents_upscaled = latentUpscale(
                latents_stage1, 
                scale_factor=args.latent_scale_factor,
                mode='nearest-exact'
            )

            # Stage 2: DPMPP with only scribble ControlNet (canny not used here)
            print(f"Stage 2: DPMPP with {args.dpmpp_steps} steps, guidance={args.dpmpp_guidance_scale}, denoise={args.dpmpp_denoise}, canny=0")
            
            # stage2 control image 
            new_width = int(args.width * args.latent_scale_factor)
            new_height = int(args.height * args.latent_scale_factor)
            control_image_stage2 = control_image_scribble.resize((new_width, new_height))
            
            with torch.no_grad():
                output_stage2 = pipe_stage2(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    image=latents_upscaled,
                    control_image=control_image_stage2,
                    controlnet_conditioning_scale=args.scribble_scale_stage2,
                    num_inference_steps=args.dpmpp_steps,
                    strength=args.dpmpp_denoise,
                    guidance_scale=args.dpmpp_guidance_scale,
                    generator=generator,
                    return_dict=False
                )
                nsfw_stage2: bool = output_stage2[1]  # type: ignore
                image_final: Image.Image = output_stage2[0][0]  # type: ignore
                print(f"Stage 2 complete, output image size: {image_final.size}")
                print(f"NSFW detected in stage 2: {nsfw_stage2}")
        
        else:
            print("Single-stage generation was deprecated. Use two-stage mode.")
            return

        # save results
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        output_ext = f".{args.output_format}"
        output_path = os.path.join(args.output_dir, f"{base_name}_output{output_ext}")

        print(f"Saving to: {output_path}")

        control_image_canny.save(os.path.join(args.output_dir, f"{base_name}_canny.png")) # type: ignore

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
