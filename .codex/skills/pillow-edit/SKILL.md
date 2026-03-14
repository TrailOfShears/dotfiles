---
name: pillow-edit
description: Edit, transform, and manipulate images using Pillow (PIL), Python's standard image processing library. Use for resizing, cropping, rotating, flipping, color adjustments, adding text, drawing shapes, applying filters, converting formats, compositing layers, and general image editing tasks that don't require AI. Also handles EXIF data reading and thumbnail generation. Triggers on "resize image", "crop image", "rotate", "add text to image", "convert image format", "apply filter", "adjust brightness/contrast", "composite images", "edit image". Repo: https://github.com/python-pillow/Pillow
---

# Pillow (PIL)

Python Image Library for programmatic image editing and manipulation.

**Repo**: https://github.com/python-pillow/Pillow

## Installation

```bash
pip install Pillow
```

## Common Operations

### Open, Resize, Save

```python
from PIL import Image

img = Image.open("input.png")
print(img.size, img.mode)   # (width, height), color mode

# Resize
img_resized = img.resize((800, 600), Image.LANCZOS)
img_resized.save("output.png")

# Thumbnail (preserves aspect ratio)
img.thumbnail((512, 512), Image.LANCZOS)
img.save("thumb.png")
```

### Crop and Rotate

```python
# Crop: (left, upper, right, lower)
cropped = img.crop((100, 100, 400, 400))

# Rotate (counter-clockwise)
rotated = img.rotate(90, expand=True)

# Flip
flipped_h = img.transpose(Image.FLIP_LEFT_RIGHT)
flipped_v = img.transpose(Image.FLIP_TOP_BOTTOM)
```

### Color and Filters

```python
from PIL import ImageEnhance, ImageFilter

# Brightness / Contrast / Sharpness / Color
img = ImageEnhance.Brightness(img).enhance(1.3)   # 1.0=original
img = ImageEnhance.Contrast(img).enhance(1.5)
img = ImageEnhance.Sharpness(img).enhance(2.0)

# Filters
img_blur = img.filter(ImageFilter.BLUR)
img_sharp = img.filter(ImageFilter.SHARPEN)
img_edge = img.filter(ImageFilter.FIND_EDGES)
img_smooth = img.filter(ImageFilter.SMOOTH_MORE)
img_emboss = img.filter(ImageFilter.EMBOSS)
```

### Drawing Text and Shapes

```python
from PIL import ImageDraw, ImageFont

draw = ImageDraw.Draw(img)

# Text
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
draw.text((50, 50), "Hello World", fill=(255, 255, 255), font=font)

# Rectangle
draw.rectangle([10, 10, 200, 100], outline=(255, 0, 0), width=3)

# Circle / Ellipse
draw.ellipse([50, 50, 150, 150], fill=(0, 128, 255), outline=(0, 0, 0))

# Line
draw.line([(0, 0), (img.width, img.height)], fill=(255, 0, 0), width=2)
```

### Format Conversion

```python
# Convert to RGB before saving as JPEG (no alpha)
img.convert("RGB").save("output.jpg", quality=95)

# PNG with transparency
img.save("output.png")   # keeps RGBA

# WebP
img.save("output.webp", quality=85, method=6)
```

### Compositing / Layering

```python
bg = Image.open("background.png").convert("RGBA")
fg = Image.open("foreground.png").convert("RGBA")
fg = fg.resize(bg.size, Image.LANCZOS)

# Paste with alpha mask
bg.paste(fg, (0, 0), fg)   # 3rd arg = mask (uses fg's alpha)
bg.save("composited.png")
```

### EXIF Data

```python
from PIL.ExifTags import TAGS

exif = img._getexif()
if exif:
    for tag_id, value in exif.items():
        tag = TAGS.get(tag_id, tag_id)
        print(f"{tag}: {value}")
```

## Workflow

1. Open the input image with `Image.open()`
2. Apply the requested transformations
3. Save to the output path (preserve format unless conversion requested)
4. Print the output path and new dimensions to the user

## Guardrails

- Always preserve the original file; save to a new path unless explicitly asked to overwrite
- For JPEG output, use quality 85–95 to balance size and quality
- When converting from RGBA to JPEG, call `.convert("RGB")` first to avoid errors
- If a font file is unavailable, fall back to `ImageFont.load_default()`
