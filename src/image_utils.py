import os
import numpy as np
import cv2
from PIL import Image, ImageOps

SUPPORTED_INPUT_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif')
SUPPORTED_OUTPUT_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

def invertImage(image):
    """
    Invert the colors of the input PIL Image and return the inverted image.
    Because scribble and canny treat white line as positive signal.
    """
    return ImageOps.invert(image.convert("RGB"))

def preprocessImage(image):
    """
    No implementation for now.
    """
    return image

def cannyPreprocessor(image, low_threshold=50, high_threshold=100):
    """
    Use Canny edge detection.
    Useless.
    """
    image_np = np.array(image.convert("RGB"))
    edges = cv2.Canny(image_np, low_threshold, high_threshold)
    edges = edges[:, :, None]
    edges = np.concatenate([edges, edges, edges], axis=2)
    return Image.fromarray(edges)

def getInputImages(input_dir):
    """
    Scan the input directory for supported image files and return a sorted list of their paths.
    """
    input_images = []
    if os.path.exists(input_dir):
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(SUPPORTED_INPUT_FORMATS):
                input_images.append(os.path.join(input_dir, filename))
    return sorted(input_images)
