---
name: real-esrgan
description: Upscale and enhance images using Real-ESRGAN, an AI-powered super-resolution tool. Use when the user wants to upscale an image, increase resolution, enhance image quality, restore old photos, sharpen blurry images, or prepare low-resolution images for print. Also handles face enhancement via GFPGAN integration. Triggers on "upscale", "increase resolution", "enhance image", "super resolution", "make image bigger", "restore photo". Repo: https://github.com/xinntao/Real-ESRGAN
---

# Real-ESRGAN

AI-based image super-resolution and enhancement.

**Repo**: https://github.com/xinntao/Real-ESRGAN

## Installation

```bash
pip install realesrgan
# OR install from source for latest features:
git clone https://github.com/xinntao/Real-ESRGAN
cd Real-ESRGAN
pip install -r requirements.txt
python setup.py develop
```

## CLI Usage

```bash
# Basic 4x upscale (general images)
python inference_realesrgan.py -n RealESRGAN_x4plus -i input.png -o output.png

# 4x upscale for anime/illustrations
python inference_realesrgan.py -n RealESRGAN_x4plus_anime_6B -i input.png -o output.png

# 2x upscale
python inference_realesrgan.py -n RealESRGAN_x2plus -i input.png -o output.png

# With face enhancement (requires GFPGAN)
python inference_realesrgan.py -n RealESRGAN_x4plus -i input.png -o output.png --face_enhance

# Batch process a folder
python inference_realesrgan.py -n RealESRGAN_x4plus -i input_folder/ -o output_folder/

# Custom output scale (e.g., 3x)
python inference_realesrgan.py -n RealESRGAN_x4plus -i input.png -o output.png --outscale 3
```

## Python API

```python
import cv2
import numpy as np
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
upsampler = RealESRGANer(
    scale=4,
    model_path="weights/RealESRGAN_x4plus.pth",  # auto-downloaded on first run
    model=model,
    tile=0,         # 0=no tiling; set 400-500 to avoid VRAM errors on large images
    tile_pad=10,
    pre_pad=0,
    half=True       # fp16; set False for CPU
)

img = cv2.imread("input.png", cv2.IMREAD_UNCHANGED)
output, _ = upsampler.enhance(img, outscale=4)
cv2.imwrite("output.png", output)
```

## Models

| Model | Best For | Scale |
|-------|----------|-------|
| RealESRGAN_x4plus | General photos | 4x |
| RealESRGAN_x2plus | General photos | 2x |
| RealESRGAN_x4plus_anime_6B | Anime, illustrations, cartoons | 4x |
| RealESRNet_x4plus | Faster, less sharp | 4x |

Models download automatically on first use (~65 MB each).

## Workflow

1. Identify the input image path(s)
2. Choose the model based on image type (photo vs. anime)
3. Run inference via CLI or Python
4. Save to output path (default: same directory with `_out` suffix)
5. Show the output path to the user

## Guardrails

- For images larger than ~2000px, use `--tile 400` to avoid running out of VRAM
- CPU mode is very slow (minutes per image); warn the user if no GPU is available
- Face enhancement requires `pip install gfpgan` and adds processing time
