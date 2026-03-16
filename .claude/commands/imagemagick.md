---
name: imagemagick
description: Perform advanced image processing, batch conversions, compositing, and effects using ImageMagick's `convert` and `magick` CLI tools. Use for format conversion, color space manipulation, watermarking, montage/contact sheets, animated GIF creation, PDF to image extraction, precise geometric transformations, complex compositing, or any image task that benefits from a battle-tested CLI pipeline. Triggers on "imagemagick", "convert image format in bulk", "watermark images", "create gif from images", "batch resize", "montage", "composite", "PDF to image", "image pipeline". Tool: https://imagemagick.org / https://github.com/ImageMagick/ImageMagick
---

# ImageMagick

Comprehensive command-line image processing and batch operations.

**Repo**: https://github.com/ImageMagick/ImageMagick
**Docs**: https://imagemagick.org/script/command-line-processing.php

## Installation

```bash
# Linux (Debian/Ubuntu)
apt install imagemagick

# macOS
brew install imagemagick

# Windows
choco install imagemagick
# or download from https://imagemagick.org/script/download.php

# Python bindings (optional)
pip install Wand
```

Verify: `magick --version` or `convert --version` (older installs)

## Format Conversion

```bash
# Single image
magick input.png output.jpg
magick input.jpg -quality 95 output.webp

# Batch convert a folder
for f in *.png; do magick "$f" "${f%.png}.jpg"; done

# HEIC to JPEG (requires libheif)
magick input.heic -quality 90 output.jpg
```

## Resize and Scale

```bash
# To exact dimensions
magick input.png -resize 800x600! output.png

# Proportional (fit within box)
magick input.png -resize 800x600 output.png

# By percentage
magick input.png -resize 50% output.png

# Batch resize preserving aspect ratio
magick mogrify -resize 1920x1080 -path resized/ *.jpg
```

## Crop, Rotate, Flip

```bash
# Crop: WxH+X+Y
magick input.png -crop 400x300+100+50 output.png

# Rotate
magick input.png -rotate 90 output.png
magick input.png -rotate -45 -background white output.png

# Flip / Flop
magick input.png -flip output.png    # vertical
magick input.png -flop output.png    # horizontal
```

## Brightness, Contrast, Color

```bash
# Brightness and contrast (-100 to +100)
magick input.png -brightness-contrast 10x20 output.png

# Grayscale
magick input.png -colorspace Gray output.png

# Sepia
magick input.png -sepia-tone 80% output.png

# Normalize (auto levels)
magick input.png -normalize output.png

# Sharpen
magick input.png -sharpen 0x1.5 output.png

# Blur
magick input.png -blur 0x3 output.png
```

## Watermark and Text Overlay

```bash
# Text watermark
magick input.png \
  -gravity SouthEast \
  -font DejaVu-Sans \
  -pointsize 36 \
  -fill "rgba(255,255,255,0.6)" \
  -annotate +20+20 "© 2025 My Brand" \
  output.png

# Image watermark (overlay logo)
magick input.png logo.png -gravity SouthEast -geometry +10+10 -composite output.png
```

## Compositing Modes

```bash
# Standard overlay
magick bg.png fg.png -composite output.png

# With blend mode
magick bg.png fg.png -compose Multiply -composite output.png
# Modes: Over, In, Out, Atop, Screen, Overlay, Multiply, Dissolve, etc.
```

## Animated GIF

```bash
# From individual frames
magick -delay 10 -loop 0 frame*.png animation.gif

# Resize GIF
magick animation.gif -resize 50% output.gif

# Optimize GIF
magick animation.gif -layers optimize optimized.gif
```

## Montage / Contact Sheet

```bash
# Create a montage grid
magick montage *.jpg -geometry 200x150+5+5 -tile 4x montage.jpg

# With labels
magick montage *.jpg -label '%f' -geometry 200x150+5+5 -tile 4x montage.jpg
```

## PDF / Multi-page

```bash
# PDF to PNG (requires Ghostscript)
magick -density 150 input.pdf output_%03d.png

# Specific page
magick -density 150 "input.pdf[0]" page1.png

# PNG to PDF
magick *.png output.pdf
```

## Python (Wand)

```python
from wand.image import Image

with Image(filename="input.png") as img:
    img.resize(800, 600)
    img.rotate(90)
    img.save(filename="output.png")
```

## Workflow

1. Identify the desired transformation(s)
2. Build the `magick` command with appropriate operators
3. Run and verify the output
4. For batch operations, use `mogrify` (in-place) or a loop with output directory

## Guardrails

- Use `mogrify` carefully — it overwrites originals in-place; always test with a copy first
- Policy limits may restrict PDF/PS processing on some installs (check `/etc/ImageMagick-7/policy.xml`)
- For very large batches, use `-limit memory 512MB` to avoid OOM errors
