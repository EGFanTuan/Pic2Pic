def latentUpscale(latents, scale_factor=1.5, mode='nearest-exact'):
    """
    Upscale latent tensors by a specified factor using interpolation.
    This is a simplified version of the latent upscaling process, directly using PyTorch's interpolate function for upscaling.
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
