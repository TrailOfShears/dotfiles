---
name: comfyui
description: Generate images using ComfyUI, a powerful node-based Stable Diffusion interface with a programmable workflow API. Use when the user wants fine-grained control over the image generation pipeline, wants to run ComfyUI workflows, chain multiple models, apply LoRAs, ControlNet nodes, or automate complex pipelines. Also use for batch generation or multi-step workflows. Repo: https://github.com/comfyanonymous/ComfyUI
---

# ComfyUI

Node-based Stable Diffusion image generation with a REST API for automation.

**Repo**: https://github.com/comfyanonymous/ComfyUI

## Starting ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt
python main.py --listen 0.0.0.0   # UI + API at http://127.0.0.1:8188
```

## Workflow via Python API

ComfyUI accepts JSON workflow graphs via its `/prompt` endpoint.

```python
import json, urllib.request, urllib.parse, random, time

SERVER = "http://127.0.0.1:8188"

def queue_prompt(workflow: dict) -> str:
    """Queue a workflow and return the prompt_id."""
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{SERVER}/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())["prompt_id"]

def get_history(prompt_id: str) -> dict:
    url = f"{SERVER}/history/{prompt_id}"
    return json.loads(urllib.request.urlopen(url).read())

def wait_for_result(prompt_id: str, poll_interval=2.0):
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(poll_interval)

def download_output(filename: str, dest: str):
    url = f"{SERVER}/view?filename={urllib.parse.quote(filename)}"
    urllib.request.urlretrieve(url, dest)
```

## Minimal Text-to-Image Workflow

```python
WORKFLOW = {
    "4": {"class_type": "CheckpointLoaderSimple",
          "inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"}},
    "5": {"class_type": "EmptyLatentImage",
          "inputs": {"width": 512, "height": 512, "batch_size": 1}},
    "6": {"class_type": "CLIPTextEncode",
          "inputs": {"text": "a photo of a cat on the moon", "clip": ["4", 1]}},
    "7": {"class_type": "CLIPTextEncode",
          "inputs": {"text": "blurry, low quality", "clip": ["4", 1]}},
    "3": {"class_type": "KSampler",
          "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
                     "latent_image": ["5", 0], "seed": random.randint(0, 2**31),
                     "steps": 20, "cfg": 7.0, "sampler_name": "dpmpp_2m",
                     "scheduler": "karras", "denoise": 1.0}},
    "8": {"class_type": "VAEDecode",
          "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
    "9": {"class_type": "SaveImage",
          "inputs": {"images": ["8", 0], "filename_prefix": "output"}}
}

prompt_id = queue_prompt(WORKFLOW)
result = wait_for_result(prompt_id)
outputs = result["outputs"]["9"]["images"]
download_output(outputs[0]["filename"], "output.png")
print("Saved output.png")
```

## Loading Models and LoRAs

```python
# LoRA node
"lora": {
    "class_type": "LoraLoader",
    "inputs": {
        "model": ["4", 0], "clip": ["4", 1],
        "lora_name": "my_lora.safetensors",
        "strength_model": 0.8, "strength_clip": 0.8
    }
}
```

## Workflow

1. Check that ComfyUI is running at `http://127.0.0.1:8188`
2. Identify the desired checkpoint from `GET /object_info/CheckpointLoaderSimple`
3. Build or adapt a workflow JSON graph
4. Queue via `POST /prompt`
5. Poll history until complete
6. Download and save output images
7. Show the user the saved file path

## Guardrails

- List available checkpoints before generating if the user hasn't specified a model
- Default to 512×512 unless the user specifies resolution
- Save outputs in the current working directory
- See `references/nodes.md` for common node types and their inputs
