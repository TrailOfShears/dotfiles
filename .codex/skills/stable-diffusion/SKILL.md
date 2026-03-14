---
name: stable-diffusion
description: Generate images from text prompts using Stable Diffusion via the AUTOMATIC1111 WebUI REST API or the Hugging Face diffusers library. Use when the user wants to generate, render, or create images from a text description, prompt, or concept. Also handles img2img (image-to-image transformation), inpainting, and outpainting workflows. Triggers on phrases like "generate an image", "create a picture", "render this", "make an illustration", or "text to image".
---

# Stable Diffusion

Generate images from text prompts using Stable Diffusion.

**Repo**: https://github.com/AUTOMATIC1111/stable-diffusion-webui
**Alt (diffusers)**: https://github.com/huggingface/diffusers

## Tool Detection

Check which backend is available:

```bash
# AUTOMATIC1111 WebUI (must be running with --api flag)
curl -s http://127.0.0.1:7860/sdapi/v1/sd-models | python3 -c "import sys,json; print('WebUI available')" 2>/dev/null

# diffusers (Python package)
python3 -c "import diffusers; print('diffusers', diffusers.__version__)" 2>/dev/null
```

## Workflow

### Via AUTOMATIC1111 WebUI API

Start the WebUI with `--api` flag, then:

```bash
curl -s http://127.0.0.1:7860/sdapi/v1/txt2img \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "<POSITIVE_PROMPT>",
    "negative_prompt": "blurry, low quality, distorted",
    "steps": 20,
    "width": 512,
    "height": 512,
    "cfg_scale": 7,
    "sampler_name": "DPM++ 2M Karras"
  }' | python3 -c "
import sys, json, base64
r = json.load(sys.stdin)
with open('output.png', 'wb') as f:
    f.write(base64.b64decode(r['images'][0]))
print('Saved output.png')
"
```

### Via diffusers (local, no server required)

```python
from diffusers import StableDiffusionPipeline
import torch

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)
pipe = pipe.to("cuda")  # or "cpu" if no GPU

image = pipe("<PROMPT>").images[0]
image.save("output.png")
```

## Prompt Engineering Tips

- Positive prompt: describe what you want. Add style keywords: `photorealistic`, `8k`, `cinematic lighting`, `oil painting`, `concept art`
- Negative prompt: `blurry, low quality, distorted, watermark, text, bad anatomy`
- CFG scale 7–12: higher = more prompt-adherent, lower = more creative
- Steps 20–50: more steps = higher quality but slower

## img2img

```bash
# WebUI API: base64 encode source image, POST to /sdapi/v1/img2img
python3 -c "
import base64, json, urllib.request
with open('input.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
data = json.dumps({
    'init_images': [b64],
    'prompt': '<PROMPT>',
    'denoising_strength': 0.75,
    'steps': 20
}).encode()
req = urllib.request.Request('http://127.0.0.1:7860/sdapi/v1/img2img',
    data=data, headers={'Content-Type': 'application/json'})
r = json.loads(urllib.request.urlopen(req).read())
with open('output.png', 'wb') as f:
    f.write(base64.b64decode(r['images'][0]))
print('Saved output.png')
"
```

## Guardrails

- If neither backend is available, guide the user to install one (see references/setup.md)
- Default output filename: `output.png` in the current directory unless the user specifies otherwise
- Always confirm the prompt with the user before a long generation run
- Prefer AUTOMATIC1111 WebUI when it's running; fall back to diffusers otherwise

## References

- See `references/setup.md` for installation instructions
- See `references/models.md` for popular model recommendations
