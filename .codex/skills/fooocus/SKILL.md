---
name: fooocus
description: Generate high-quality images with Fooocus, a streamlined Stable Diffusion interface that hides complexity behind a simple prompt-and-generate workflow. Use when the user wants hassle-free text-to-image generation without tuning parameters, wants SDXL-quality results with minimal setup, or wants to use Fooocus presets and styles. Also supports image prompts, upscaling, inpainting, and variation generation. Triggers on "generate image with fooocus", "fooocus", "simple image generation", "sdxl image". Repo: https://github.com/lllyasviel/Fooocus
---

# Fooocus

Simple, high-quality text-to-image generation powered by SDXL.

**Repo**: https://github.com/lllyasviel/Fooocus

## Setup

```bash
git clone https://github.com/lllyasviel/Fooocus
cd Fooocus
pip install -r requirements_versions.txt
# Models download automatically on first run (~7 GB)
python entry_with_update.py
# or with API enabled:
python entry_with_update.py --listen --port 7865 --share
```

Enable the API:
```bash
python entry_with_update.py --listen --always-high-vram
# API available at http://127.0.0.1:7865
```

## Using the Fooocus API

Fooocus exposes an OpenAPI-compatible endpoint:

```python
import requests, base64, json

FOOOCUS = "http://127.0.0.1:7865"

def generate(prompt: str, negative: str = "", style: str = "Fooocus V2",
             width=1024, height=1024, steps=30, seed=-1) -> bytes:
    payload = {
        "prompt": prompt,
        "negative_prompt": negative,
        "style_selections": [style],
        "performance_selection": "Speed",  # or "Quality", "Extreme Speed"
        "aspect_ratios_selection": f"{width}*{height}",
        "image_number": 1,
        "image_seed": seed,
        "sharpness": 2.0,
        "guidance_scale": 7.0,
    }
    r = requests.post(f"{FOOOCUS}/v1/generation/text-to-image", json=payload)
    r.raise_for_status()
    results = r.json()
    return base64.b64decode(results[0]["base64"])

image_bytes = generate("a majestic lion on a mountain at sunset, photorealistic")
with open("output.png", "wb") as f:
    f.write(image_bytes)
print("Saved output.png")
```

## Fooocus Styles

Popular style presets (pass in `style_selections` list):

| Style | Effect |
|-------|--------|
| `Fooocus V2` | Default balanced style |
| `Fooocus Photograph` | Photorealistic |
| `Fooocus Anime` | Anime/manga style |
| `Fooocus Masterpiece` | Painterly/artistic |
| `Cinematic` | Movie look |
| `Watercolor` | Watercolor painting |
| `Oil Painting` | Classic oil painting |

Multiple styles can be combined: `["Fooocus Photograph", "Cinematic"]`

## Performance Modes

| Mode | Steps | Speed |
|------|-------|-------|
| Extreme Speed (LCM) | ~8 | Fastest |
| Speed | 30 | Balanced |
| Quality | 60 | Slower, sharper |

## Image-to-Image and Variations

```python
import base64

with open("input.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    "prompt": "same scene but at night",
    "image_prompts": [{"cn_img": b64, "cn_type": "ImagePrompt", "cn_weight": 0.6}],
}
```

## Workflow

1. Verify Fooocus is running (`curl http://127.0.0.1:7865/docs`)
2. Craft a descriptive prompt; let Fooocus handle the rest
3. Choose a style preset if the user has a preference
4. POST to the API and decode the base64 result
5. Save and show the output path

## Guardrails

- Default resolution is 1024×1024 (SDXL native); inform user about aspect ratio options
- First run downloads ~7 GB of models automatically
- Requires 8 GB VRAM for SDXL; 4 GB possible with `--lowvram`
