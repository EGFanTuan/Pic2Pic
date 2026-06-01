import pytest
from PIL import Image
import numpy as np
import sys
import os

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.image_utils import invertImage, preprocessImage, cannyPreprocessor

def test_invertImage():
    # Create a 10x10 black image
    img = Image.new('RGB', (10, 10), color='black')
    inverted = invertImage(img)
    
    # Check if the inverted image is white
    arr = np.array(inverted)
    assert np.all(arr == 255), "Inverted black image should be completely white"

def test_preprocessImage():
    img = Image.new('RGB', (10, 10), color='white')
    processed = preprocessImage(img)
    
    # Check if it returns a valid PIL Image of same size
    assert isinstance(processed, Image.Image)
    assert processed.size == (10, 10)

def test_cannyPreprocessor():
    # Create a simple image with a sharp edge
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[50:, :] = 255
    img = Image.fromarray(arr)
    
    edges = cannyPreprocessor(img, 50, 100)
    assert isinstance(edges, Image.Image)
    assert edges.size == (100, 100)
    
    # Check if edges were found
    edge_arr = np.array(edges)
    assert np.any(edge_arr > 0), "Canny preprocessor should detect edges"
