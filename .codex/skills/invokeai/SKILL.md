---
name: invokeai
description: Generate and edit images using InvokeAI, a professional-grade creative engine supporting Stable Diffusion, SDXL, and Flux models with a node-based workflow system. Use when the user wants professional image generation features like unified canvas (infinite painting), multi-step node workflows, LoRA/ControlNet stacking, Flux model generation, IP-Adapter reference images, or prompt syntax with attention weights. Triggers on "invokeai", "invoke ai", "flux image generation", "unified canvas", "professional image generation", "node workflow generation". Repo: https://github.com/invoke-ai/InvokeAI
---

# InvokeAI

Professional creative image generation engine with CLI and REST API.

**Repo**: https://github.com/invoke-ai/InvokeAI

## Installation

```bash
pip install invokeai
invokeai-configure          # first-time setup, downloads models
invokeai-web                # start web UI at http://localhost:9090
```

Or the installer (recommended for most users):
```bash
# Download from https://github.com/invoke-ai/InvokeAI/releases
python installer/install.py
```

## REST API

InvokeAI exposes a full OpenAPI-documented REST API at `http://localhost:9090`.

### List available models

```bash
curl http://localhost:9090/api/v1/models/ | python3 -m json.tool
```

### Enqueue a text-to-image generation

```python
import requests, json, time

BASE = "http://localhost:9090"

def txt2img(prompt: str, model_key: str, width=512, height=512,
            steps=30, cfg=7.5, seed=None) -> str:
    """Queue a generation and return the output image path."""
    payload = {
        "prepend": False,
        "batch": {
            "graph": {
                "id": "sdxl_text_to_image",
                "nodes": {
                    "model_loader": {
                        "type": "main_model_loader",
                        "id": "model_loader",
                        "model": {"key": model_key}
                    },
                    "positive_conditioning": {
                        "type": "compel",
                        "id": "positive_conditioning",
                        "prompt": prompt
                    },
                    "negative_conditioning": {
                        "type": "compel",
                        "id": "negative_conditioning",
                        "prompt": "blurry, low quality"
                    },
                    "noise": {
                        "type": "noise",
                        "id": "noise",
                        "seed": seed or 0,
                        "width": width,
                        "height": height
                    },
                    "denoise_latents": {
                        "type": "denoise_latents",
                        "id": "denoise_latents",
                        "cfg_scale": cfg,
                        "steps": steps,
                        "denoising_start": 0,
                        "denoising_end": 1,
                        "scheduler": "dpmpp_2m_k"
                    },
                    "decode_latents": {"type": "l2i", "id": "decode_latents"},
                    "save_image": {"type": "save_image", "id": "save_image",
                                   "is_intermediate": False}
                },
                "edges": [
                    {"source": {"node_id": "model_loader", "field": "unet"},
                     "destination": {"node_id": "denoise_latents", "field": "unet"}},
                    {"source": {"node_id": "model_loader", "field": "clip"},
                     "destination": {"node_id": "positive_conditioning", "field": "clip"}},
                    {"source": {"node_id": "model_loader", "field": "clip"},
                     "destination": {"node_id": "negative_conditioning", "field": "clip"}},
                    {"source": {"node_id": "positive_conditioning", "field": "conditioning"},
                     "destination": {"node_id": "denoise_latents", "field": "positive_conditioning"}},
                    {"source": {"node_id": "negative_conditioning", "field": "conditioning"},
                     "destination": {"node_id": "denoise_latents", "field": "negative_conditioning"}},
                    {"source": {"node_id": "noise", "field": "noise"},
                     "destination": {"node_id": "denoise_latents", "field": "noise"}},
                    {"source": {"node_id": "denoise_latents", "field": "latents"},
                     "destination": {"node_id": "decode_latents", "field": "latents"}},
                    {"source": {"node_id": "decode_latents", "field": "image"},
                     "destination": {"node_id": "save_image", "field": "image"}}
                ]
            },
            "runs": 1
        }
    }
    r = requests.post(f"{BASE}/api/v1/queue/default/enqueue_batch", json=payload)
    r.raise_for_status()
    return r.json()

# Check queue and wait for result
def wait_for_image(queue_item_id: str, poll=2.0):
    while True:
        r = requests.get(f"{BASE}/api/v1/queue/default/i/{queue_item_id}")
        status = r.json().get("status")
        if status == "completed":
            return r.json()
        if status in ("failed", "canceled"):
            raise RuntimeError(f"Generation {status}")
        time.sleep(poll)
```

## InvokeAI Prompt Syntax

InvokeAI uses a special syntax with attention weights:

```
a (beautiful:1.2) landscape with (mountains:0.8) and (snow:1.5)
```

- `(word:1.0)` = normal weight
- `(word:1.5)` = stronger emphasis
- `(word:0.5)` = weaker emphasis
- `[word]` = slightly reduced emphasis

## Flux Models

InvokeAI supports Flux.1-dev and Flux.1-schnell (fast):

```bash
# Install a Flux model via invokeai-model-install
invokeai-model-install --source black-forest-labs/FLUX.1-schnell
```

Flux uses a different node type (`flux_model_loader`) in the workflow graph.

## Workflow

1. Confirm InvokeAI is running (`curl http://localhost:9090/api/v1/app/version`)
2. List models to find the model key for the user's request
3. Build and enqueue the workflow graph
4. Poll the queue until complete
5. Retrieve the output image URL from the result and download it
6. Show the file path to the user

## Guardrails

- InvokeAI API changes between major versions; check `/api/v1/app/version` first
- For simple generation, point users to the web UI at `http://localhost:9090`
- For API use, prefer the simpler AUTOMATIC1111 interface unless InvokeAI-specific features are needed
- Model keys are UUIDs assigned at install time; always list them dynamically
