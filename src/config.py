import argparse

def parseArgs():
    parser = argparse.ArgumentParser(description='Line Art to Image using Dual ControlNet')
    # 输入路径
    parser.add_argument('--input_dir', type=str, default="./input", help='Directory with input images')
    # 输出路径
    parser.add_argument('--output_dir', type=str, default="./output", help='Directory to save output images')
    # 输出格式
    parser.add_argument('--output_format', type=str, default='png', choices=['png', 'jpg', 'jpeg', 'webp', 'bmp'], help='Output image format')

    # 提示词参数
    parser.add_argument('--prompt', type=str, default="masterpiece, best quality, anime style \n", help='Positive prompt')
    parser.add_argument('--negative_prompt', type=str, default="not safe fot work, not suitable for work, NSFW, worst quality, low quality, blurry, bad anatomy, bad hands, words, text，", help='Negative prompt')

    # 空的 latent 张量大小, 宽高尽量为8的倍数
    parser.add_argument('--width', type=int, default=400, help='Output width')
    parser.add_argument('--height', type=int, default=600, help='Output height')

    # 是否仅处理LCM阶段来获得更快的预览结果
    parser.add_argument('--single_stage', action='store_true', default=False, help='Use single-stage generation instead of two-stage (LCM + DPMPP)')

    # LCM 阶段相关参数
    parser.add_argument('--lcm_steps', type=int, default=4, help='Number of LCM inference steps')
    parser.add_argument('--lcm_guidance_scale', type=float, default=2.5, help='Guidance scale for LCM stage')
    parser.add_argument('--lcm_denoise', type=float, default=0.9, help='Denoise strength for LCM stage')
    parser.add_argument('--scribble_scale_stage1', type=float, default=0.9, help='Scribble ControlNet scale for first stage')
    parser.add_argument('--canny_scale_stage1', type=float, default=0.4, help='Canny ControlNet scale for first stage')

    # 上采样倍率
    parser.add_argument('--latent_scale_factor', type=float, default=1.5, help='Latent upscale factor between stages')

    # DPMPP 阶段相关参数
    parser.add_argument('--dpmpp_steps', type=int, default=35, help='Number of DPM++ inference steps')
    parser.add_argument('--dpmpp_guidance_scale', type=float, default=8.0, help='Guidance scale for DPM++ stage')
    parser.add_argument('--dpmpp_denoise', type=float, default=0.6, help='Denoise strength for DPM++ stage')
    parser.add_argument('--scribble_scale_stage2', type=float, default=0.9, help='Scribble ControlNet scale for second stage')

    # checkpoint模型名称
    parser.add_argument('--checkpoint_name', type=str, default="dreamshaper_8.safetensors", help='Checkpoint filename in models/checkpoints/ directory')

    return parser.parse_args()
