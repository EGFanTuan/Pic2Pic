import os
import cv2
import numpy as np
from PIL import Image
from src.image_utils import getInputImages, invertImage, SUPPORTED_INPUT_FORMATS

def main():
    input_dir = "./input"
    output_dir = "./output/canny_test"
    os.makedirs(output_dir, exist_ok=True)

    input_images = getInputImages(input_dir)
    if not input_images:
        print(f"No images found in {input_dir}")
        return

    # 选取第一张图片进行测试
    test_img_path = input_images[1]
    print(f"Testing Canny thresholds on: {test_img_path}")
    
    # 读取并反转（模拟 main.py 中的逻辑：黑底白线 -> 白底黑线）
    image = Image.open(test_img_path)
    image = invertImage(image)
    image_np = np.array(image.convert("RGB"))

    # 定义测试的阈值组合
    # low_thresholds = [50, 100, 150]
    # high_thresholds = [150, 200, 250]
    threshold_pairs = [
        (50, 100),
        (50, 150),
        (100, 200),
        (100, 250),
        (150, 250)
    ]

    for low, high in threshold_pairs:
        edges = cv2.Canny(image_np, low, high)
        
        # 将结果转换为可保存的格式
        edges_color = np.concatenate([edges[:, :, None]] * 3, axis=2)
        edges_pil = Image.fromarray(edges_color)
        
        # 保存结果
        base_name = os.path.splitext(os.path.basename(test_img_path))[0]
        save_path = os.path.join(output_dir, f"{base_name}_canny_{low}_{high}.png")
        edges_pil.save(save_path)
        print(f"Saved: {save_path}")

    print(f"\nTest complete. Check results in: {output_dir}")

if __name__ == "__main__":
    main()
