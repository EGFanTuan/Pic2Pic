import torch
from diffusers.pipelines.controlnet.pipeline_controlnet import StableDiffusionControlNetPipeline
from diffusers.pipelines.controlnet.pipeline_controlnet_img2img import StableDiffusionControlNetImg2ImgPipeline
from diffusers.models.controlnets.controlnet import ControlNetModel
from diffusers.schedulers.scheduling_dpmsolver_multistep import DPMSolverMultistepScheduler
from diffusers.schedulers.scheduling_lcm import LCMScheduler

def buildPipeline(checkpoint_path, controlnet_scribble_path, controlnet_canny_path, device):
    print("Loading ControlNet models...")
    # load scribble controlnet
    controlnet_scribble = ControlNetModel.from_single_file(
        controlnet_scribble_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=False
    )
    print("Scribble ControlNet loaded.")
    # load canny controlnet
    controlnet_canny = ControlNetModel.from_single_file(
        controlnet_canny_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=False
    )
    print("Canny ControlNet loaded.")
    controlnets = [controlnet_scribble, controlnet_canny]

    print("Loading Stable Diffusion pipeline...")
    pipe = StableDiffusionControlNetPipeline.from_single_file(
        checkpoint_path,
        controlnet=controlnets,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
        safety_checker=None
    )

    print("Initializing stage pipelines...")
    # stage1: text2img ControlNet pipeline (supports noise latents directly)
    pipe_stage1 = pipe
    # stage2: img2img ControlNet pipeline (keeps strength-based denoise)
    pipe_stage2 = StableDiffusionControlNetImg2ImgPipeline(**pipe.components)
    pipe_stage2.controlnet = controlnet_scribble

    pipe_stage1.scheduler = LCMScheduler.from_config(pipe.scheduler.config) # type: ignore
    pipe_stage2.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True) # type: ignore

    pipe = pipe.to(device)

    if device == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        try:
            pipe.enable_xformers_memory_efficient_attention()
        except (ImportError, ModuleNotFoundError, ValueError):
            print("xformers did not load.")
        
        pipe.vae.enable_tiling()

    return pipe, pipe_stage1, pipe_stage2, controlnet_scribble
