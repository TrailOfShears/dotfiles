---
name: rembg
description: Remove the background from images using rembg, a fast open-source background removal tool powered by U2-Net neural networks. Use when the user wants to remove a background, cut out a subject, create a transparent PNG, isolate a foreground object, or prepare images for compositing. Triggers on "remove background", "cut out", "transparent background", "isolate subject", "background eraser". Repo: https://github.com/danielgatis/rembg
---

# rembg

Remove image backgrounds using U2-Net neural networks.

**Repo**: https://github.com/danielgatis/rembg

## Installation

```bash
pip install rembg
# With GPU support (CUDA):
pip install rembg[gpu]
```

## CLI Usage

```bash
# Single image
rembg i input.png output.png

# Batch process a folder
rembg p input_folder/ output_folder/

# Pipe from URL
curl -s https://example.com/photo.jpg | rembg i > output.png
```

## Python API

```python
from rembg import remove
from PIL import Image
import io

# From file
with open("input.png", "rb") as f:
    input_data = f.read()

output_data = remove(input_data)

with open("output.png", "wb") as f:
    f.write(output_data)

# Or with PIL
input_img = Image.open("input.png")
output_img = remove(input_img)
output_img.save("output.png")
```

## Models

rembg supports multiple segmentation models:

```bash
rembg i -m u2net input.png output.png          # General (default)
rembg i -m u2net_human_seg input.png output.png # Human portraits (best for people)
rembg i -m u2net_cloth_seg input.png output.png # Clothing segmentation
rembg i -m isnet-general-use input.png output.png # ISNet (high quality)
rembg i -m isnet-anime input.png output.png     # Anime/illustrations
rembg i -m silueta input.png output.png         # Silhouette mode
```

## Compositing on a New Background

```python
from rembg import remove
from PIL import Image

fg = remove(Image.open("subject.png"))
bg = Image.open("background.jpg").resize(fg.size)
bg.paste(fg, mask=fg.split()[3])   # use alpha channel as mask
bg.save("composited.png")
```

## Workflow

1. Identify the input image file(s)
2. Choose the appropriate model (default `u2net`; use `u2net_human_seg` for people)
3. Run rembg via CLI or Python
4. Save output as PNG (preserves transparency)
5. If compositing, paste the foreground onto a new background

## Guardrails

- Output is always PNG (supports transparency); inform user if they expect JPEG
- For batch jobs, confirm the output folder path before processing
- Model downloads happen automatically on first use (~170 MB per model)
