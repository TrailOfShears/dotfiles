---
name: controlnet
description: Generate images with precise structural control using ControlNet, a neural network extension for Stable Diffusion that conditions generation on poses, edges, depth maps, sketches, and other spatial signals. Use when the user wants to control image composition, preserve a pose from a reference image, guide generation with a sketch or line drawing, maintain depth structure, or create images that match a specific layout. Triggers on "controlnet", "guided generation", "pose to image", "sketch to image", "edge guided", "depth guided", "control composition". Repos: https://github.com/lllyasviel/ControlNet and https://github.com/Mikubill/sd-webui-controlnet
---

# ControlNet

Condition Stable Diffusion generation on spatial signals (poses, edges, depth, sketches).

**Original Repo**: https://github.com/lllyasviel/ControlNet
**WebUI Extension**: https://github.com/Mikubill/sd-webui-controlnet

## Installation

### Via AUTOMATIC1111 WebUI Extension (recommended)

1. Open WebUI → Extensions → Install from URL
2. URL: `https://github.com/Mikubill/sd-webui-controlnet`
3. Apply and restart
4. Download models to `models/ControlNet/`

### Via diffusers (Python, standalone)

```bash
pip install diffusers controlnet-aux accelerate
```

## Control Types

| Control Type | What it does | Model name |
|-------------|--------------|------------|
| Canny edges | Sharp edge detection | control_v11p_sd15_canny |
| Depth | Monocular depth map | control_v11f1p_sd15_depth |
| HED/SoftEdge | Soft edges | control_v11p_sd15_softedge |
| OpenPose | Human body pose | control_v11p_sd15_openpose |
| Scribble | Hand-drawn sketch | control_v11p_sd15_scribble |
| Lineart | Clean lineart | control_v11p_sd15_lineart |
| Seg | Semantic segmentation | control_v11p_sd15_seg |
| Tile | High-res tile refinement | control_v11f1e_sd15_tile |
| MLSD | Straight lines/architecture | control_v11p_sd15_mlsd |

## diffusers Pipeline (Standalone)

### Canny Edge Control

```python
import cv2
import numpy as np
from PIL import Image
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
import torch

# 1. Prepare control image (Canny edges)
image = cv2.imread("reference.png")
edges = cv2.Canny(image, 100, 200)
edges = Image.fromarray(edges)

# 2. Load ControlNet + SD pipeline
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_canny", torch_dtype=torch.float16
)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16
).to("cuda")

# 3. Generate
output = pipe(
    prompt="a beautiful landscape painting",
    image=edges,
    num_inference_steps=20,
    controlnet_conditioning_scale=1.0,
).images[0]
output.save("output.png")
```

### OpenPose Control

```python
from controlnet_aux import OpenposeDetector
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
import torch

# Extract pose
detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
pose = detector(Image.open("person.png"))

controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_openpose", torch_dtype=torch.float16
)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", controlnet=controlnet, torch_dtype=torch.float16
).to("cuda")

output = pipe("a superhero in this pose", image=pose, num_inference_steps=20).images[0]
output.save("output.png")
```

## Via AUTOMATIC1111 WebUI API

```python
import requests, base64, json

with open("control_image.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    "prompt": "your prompt",
    "steps": 20,
    "alwayson_scripts": {
        "controlnet": {
            "args": [{
                "enabled": True,
                "image": b64,
                "module": "canny",         # preprocessor
                "model": "control_v11p_sd15_canny [d14c016b]",
                "weight": 1.0,
                "guidance_start": 0.0,
                "guidance_end": 1.0,
            }]
        }
    }
}

r = requests.post("http://127.0.0.1:7860/sdapi/v1/txt2img", json=payload)
result = r.json()
with open("output.png", "wb") as f:
    f.write(base64.b64decode(result["images"][0]))
```

## Workflow

1. Identify the control type based on user intent (pose → OpenPose, sketch → Scribble, etc.)
2. Prepare the control image (apply preprocessor if needed)
3. Choose backend: diffusers (standalone) or WebUI API
4. Generate with appropriate `controlnet_conditioning_scale` (0.5–1.5)
5. Save and show the output path

## Guardrails

- `controlnet_conditioning_scale`: 1.0 = strong control; lower (0.5) = more creative freedom
- Always check that the correct ControlNet model is downloaded
- For WebUI, list available models via `GET /controlnet/model_list`
