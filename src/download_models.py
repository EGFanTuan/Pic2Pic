import urllib.request
import os
import sys

def download_file(url, output_path):
    """Download a file with progress reporting"""
    print(f"Downloading: {url}")
    print(f"Saving to: {output_path}")

    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
        sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB)")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
        print("\nDownload completed!")
        return True
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    controlnet_dir = os.path.join(base_dir, "models", "controlnet")

    os.makedirs(controlnet_dir, exist_ok=True)

    # ControlNet model URLs from Hugging Face
    models = [
        {
            "url": "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_scribble.pth",
            "filename": "control_v11p_sd15_scribble.pth"
        },
        {
            "url": "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth",
            "filename": "control_v11p_sd15_canny.pth"
        }
    ]

    for model in models:
        output_path = os.path.join(controlnet_dir, model["filename"])

        # Skip if file already exists and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100000000:
            print(f"{model['filename']} already exists, skipping...")
            continue

        success = download_file(model["url"], output_path)
        if not success:
            print(f"Failed to download {model['filename']}")
            return 1

    print("\nAll models downloaded successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
