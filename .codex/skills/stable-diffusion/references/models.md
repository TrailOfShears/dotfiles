# Popular Stable Diffusion Models

| Model | Best For | Source |
|-------|----------|--------|
| SD 1.5 (runwayml/stable-diffusion-v1-5) | General purpose, fast | Hugging Face |
| SDXL (stabilityai/stable-diffusion-xl-base-1.0) | High resolution, detail | Hugging Face |
| Realistic Vision | Photorealistic portraits | CivitAI |
| DreamShaper | Artistic, fantasy | CivitAI |
| OpenJourney | Midjourney-like style | Hugging Face |
| Deliberate | Detailed realism | CivitAI |

## Download via diffusers

```python
# SDXL
from diffusers import StableDiffusionXLPipeline
pipe = StableDiffusionXLPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0")
```

## Samplers (AUTOMATIC1111)

- `DPM++ 2M Karras` — balanced quality/speed (recommended)
- `Euler a` — creative, good for artistic
- `DDIM` — fast, predictable
- `LMS` — smooth gradients
