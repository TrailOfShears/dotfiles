---
name: backgroundremover
description: Remove backgrounds from images and videos using backgroundremover, an open-source tool that extends background removal to video files in addition to images. Use when the user wants to remove a background from a video clip, process a sequence of frames, needs a server endpoint for background removal, or wants a Docker-ready background removal pipeline. Prefer this over rembg when working with video files. Triggers on "remove background from video", "video background removal", "cut out video subject", "background remover video", "green screen effect". Repo: https://github.com/nadermx/backgroundremover
---

# backgroundremover

Background removal for images and video via U2Net and MODNet models.

**Repo**: https://github.com/nadermx/backgroundremover

## Installation

```bash
pip install backgroundremover

# For GPU acceleration
pip install backgroundremover[gpu]
```

## Image Background Removal

```bash
# Single image → transparent PNG
backgroundremover -i input.png -o output.png

# With alpha matting (cleaner edges, slower)
backgroundremover -i input.png -a -ae 15 -o output.png

# Use human segmentation model
backgroundremover -i portrait.jpg -m u2net_human_seg -o output.png
```

## Video Background Removal

```bash
# Remove background from video → transparent WebM
backgroundremover -i input.mp4 -tv -o output.webm

# With audio preserved
backgroundremover -i input.mp4 -tv -toa -o output.webm

# Specify framerate (default: match source)
backgroundremover -i input.mp4 -tv -fr 30 -o output.webm
```

## Replace with a New Background

```bash
# Composite over a solid color
backgroundremover -i input.mp4 -tv -toa -o no_bg.webm
# Then use FFmpeg to composite over a background:
ffmpeg -i background.mp4 -i no_bg.webm -filter_complex \
  "[0:v][1:v] overlay=0:0:shortest=1" -c:a copy output.mp4
```

## HTTP Server Mode

```bash
# Start server (default port 5000)
backgroundremover -s

# Then POST an image
curl -F "file=@input.png" http://localhost:5000/api/remove -o output.png
```

## Python API

```python
import backgroundremover.bg as bg
from PIL import Image
import io

with open("input.png", "rb") as f:
    data = f.read()

output = bg.remove(data, model_name="u2net",
                   alpha_matting=True,
                   alpha_matting_foreground_threshold=240,
                   alpha_matting_background_threshold=10,
                   alpha_matting_erode_structure_size=10)

Image.open(io.BytesIO(output)).save("output.png")
```

## Models

| Model | Best For |
|-------|---------|
| `u2net` | General purpose (default) |
| `u2net_human_seg` | Portraits and people |
| `u2netp` | Faster, slightly lower quality |

## Choosing Between rembg and backgroundremover

| Feature | rembg | backgroundremover |
|---------|-------|------------------|
| Image support | Yes | Yes |
| Video support | No | **Yes** |
| Models | u2net, BRIA, ISNet | u2net, u2netp |
| Server mode | Yes | Yes |
| Alpha matting | Yes | Yes |

Use **backgroundremover** when the input is a video file.
Use **rembg** for images (more model options, generally faster for stills).

## Workflow

1. Identify whether the input is an image or video
2. For video: use `-tv` flag; for image: use standard mode
3. Choose alpha matting (`-a`) for fine hair/edge detail
4. Run and save output as PNG (images) or WebM (video)
5. If compositing over a new background, use FFmpeg as a second pass

## Guardrails

- Video output is WebM with alpha channel by default; some players may not support it
- GPU processing is much faster for video; warn user if only CPU is available
- Large videos may take significant time to process frame by frame
