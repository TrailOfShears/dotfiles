# Stable Diffusion Setup

## Option A: AUTOMATIC1111 WebUI

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui
# Place a model checkpoint in models/Stable-diffusion/
./webui.sh --api           # Linux/macOS
webui-user.bat --api       # Windows
```

API available at http://127.0.0.1:7860

## Option B: diffusers (Python)

```bash
pip install diffusers transformers accelerate torch
```

GPU strongly recommended. With NVIDIA GPU:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

CPU-only (slow):
```bash
# Use pipe.to("cpu") and remove torch_dtype=torch.float16
```
