---
name: style-transfer
description: Apply the artistic style of one image onto the content of another using neural style transfer. Use when the user wants to repaint a photo in the style of Van Gogh, Picasso, or any reference artwork; apply a texture or visual aesthetic to an image; or create artistic stylized versions of photos. Triggers on "style transfer", "apply style", "make it look like", "paint in the style of", "artistic filter", "neural style", "stylize image". Repos: https://github.com/lengstrom/fast-style-transfer (TensorFlow) and https://github.com/gordicaleksa/pytorch-neural-style-transfer (PyTorch)
---

# Neural Style Transfer

Apply the visual style of a reference artwork onto a content image.

**Repos**:
- PyTorch: https://github.com/gordicaleksa/pytorch-neural-style-transfer (recommended)
- Fast/real-time TF: https://github.com/lengstrom/fast-style-transfer

## Option A: PyTorch (recommended, single-image, high quality)

### Setup

```bash
git clone https://github.com/gordicaleksa/pytorch-neural-style-transfer
cd pytorch-neural-style-transfer
pip install -r requirements.txt
```

### Run Style Transfer

```bash
python neural_style_transfer.py \
  --content_img_name content.jpg \
  --style_img_name starry_night.jpg \
  --model vgg19 \
  --optimizer lbfgs \
  --num_of_iterations 1000 \
  --saving_freq 100
```

Output is saved to `data/output-images/`.

Key parameters:

| Flag | Default | Effect |
|------|---------|--------|
| `--content_weight` | 1e5 | How much to preserve content structure |
| `--style_weight` | 3e4 | How much style to apply |
| `--tv_weight` | 1e0 | Smoothness/noise reduction |
| `--num_of_iterations` | 1000 | More = higher quality, slower |
| `--height` | 400 | Output image height in pixels |

```bash
# Stronger style, weaker content
python neural_style_transfer.py \
  --content_img_name photo.jpg \
  --style_img_name monet.jpg \
  --content_weight 1e4 \
  --style_weight 1e5

# High resolution output
python neural_style_transfer.py \
  --content_img_name photo.jpg \
  --style_img_name style.jpg \
  --height 800 \
  --num_of_iterations 1500
```

## Option B: Fast Style Transfer (TensorFlow, pre-trained models, ~100ms)

### Setup

```bash
git clone https://github.com/lengstrom/fast-style-transfer
cd fast-style-transfer
pip install tensorflow scipy pillow
```

Download a pre-trained model (e.g. `wave.ckpt` from the repo's README links).

### Run

```bash
python evaluate.py \
  --checkpoint wave.ckpt \
  --in-path input.jpg \
  --out-path output.jpg

# Batch a folder
python evaluate.py \
  --checkpoint wave.ckpt \
  --in-path photos/ \
  --out-path styled/
```

Pre-trained style models available in the repo README:
- Wave (Hokusai), Udnie, Rain Princess, La Muse, Scream, Wreck

## Option C: diffusers / IP-Adapter (modern approach)

```python
from diffusers import StableDiffusionImg2ImgPipeline
import torch
from PIL import Image

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16
).to("cuda")

content = Image.open("content.jpg").resize((512, 512))

# Describe the target style as a prompt
result = pipe(
    prompt="in the style of Van Gogh, swirling brush strokes, oil painting",
    image=content,
    strength=0.6,      # 0=no change, 1=ignore content completely
    guidance_scale=7.5
).images[0]
result.save("output.jpg")
```

## Workflow

1. Ask the user for: content image path, style image path (or named style)
2. Choose backend:
   - Fast (~seconds): Option B with a pre-trained checkpoint
   - High quality (~minutes): Option A (PyTorch LBFGS optimization)
   - Modern/flexible: Option C via diffusers img2img
3. Run and save output
4. Offer to adjust style/content balance if result isn't right

## Guardrails

- Content images larger than 800px slow down optimization significantly; resize first
- Optimization-based (Option A) requires no style checkpoint but takes minutes on CPU
- Fast style transfer (Option B) is instant but limited to pre-trained styles
- GPU strongly recommended for all options
