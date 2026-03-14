---
name: color-palette
description: Extract color palettes from images, generate harmonious color schemes, and analyze or convert colors using open-source tools. Use when the user wants to extract the dominant colors from an image, generate a color palette for a design, find complementary or analogous colors, convert between color formats (HEX, RGB, HSL, CMYK), or create a swatch/palette file. Triggers on "color palette", "extract colors", "dominant colors", "color scheme", "color harmony", "swatch", "brand colors from image". Repos: https://github.com/fengsp/color-thief-py and https://github.com/vaab/colour
---

# Color Palette

Extract and generate color palettes from images using ColorThief and colour.

**Repos**:
- ColorThief: https://github.com/fengsp/color-thief-py
- colour: https://github.com/vaab/colour
- colorsys: Python stdlib (no install needed)

## Installation

```bash
pip install colorthief colour-science
```

## Extract Palette from Image (ColorThief)

```python
from colorthief import ColorThief

ct = ColorThief("input.png")

# Dominant color
dominant = ct.get_color(quality=1)
print(f"Dominant: RGB{dominant}  HEX #{dominant[0]:02x}{dominant[1]:02x}{dominant[2]:02x}")

# Palette of N colors
palette = ct.get_palette(color_count=8, quality=1)
for rgb in palette:
    hex_color = "#{:02x}{:02x}{:02x}".format(*rgb)
    print(f"RGB{rgb}  {hex_color}")
```

## Color Format Conversion

```python
import colorsys

def rgb_to_hex(r, g, b):
    return "#{:02x}{:02x}{:02x}".format(r, g, b)

def hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return round(h*360, 1), round(s*100, 1), round(l*100, 1)

def rgb_to_cmyk(r, g, b):
    r, g, b = r/255, g/255, b/255
    k = 1 - max(r, g, b)
    if k == 1:
        return 0, 0, 0, 100
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return round(c*100), round(m*100), round(y*100), round(k*100)
```

## Generate Color Harmonies

```python
def complementary(h, s, l):
    """Return complementary hue (opposite on the color wheel)."""
    return (h + 180) % 360, s, l

def analogous(h, s, l, angle=30):
    """Return 3 analogous colors."""
    return [(h + i) % 360 for i in [-angle, 0, angle]]

def triadic(h):
    return [h, (h + 120) % 360, (h + 240) % 360]

def split_complementary(h):
    return [h, (h + 150) % 360, (h + 210) % 360]
```

## Output a Visual Swatch (PNG)

```python
from PIL import Image, ImageDraw, ImageFont

def save_swatch(palette: list[tuple[int,int,int]], output="palette.png", swatch_w=120, swatch_h=80):
    img = Image.new("RGB", (swatch_w * len(palette), swatch_h + 30), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for i, rgb in enumerate(palette):
        x = i * swatch_w
        draw.rectangle([x, 0, x + swatch_w, swatch_h], fill=rgb)
        hex_str = "#{:02x}{:02x}{:02x}".format(*rgb)
        draw.text((x + 5, swatch_h + 5), hex_str, fill=(0, 0, 0))
    img.save(output)
    print(f"Palette saved to {output}")

# Usage
save_swatch(palette)
```

## Workflow

1. If extracting from an image: open the image with ColorThief and extract the palette
2. If generating a scheme: take a seed color and apply harmony rules
3. Output the palette as:
   - A printed list of HEX and RGB values
   - Optionally a visual swatch PNG (`palette.png`)
   - Optionally a CSS snippet with CSS custom properties
4. Ask the user if they want additional formats (HSL, CMYK, CSS variables)

## Output Formats

### CSS Custom Properties
```css
:root {
  --color-1: #<hex>;
  --color-2: #<hex>;
}
```

### Tailwind Config snippet
```js
colors: {
  brand: { primary: '#<hex>', secondary: '#<hex>' }
}
```

## Guardrails

- Default to 6–8 colors for palettes unless the user specifies
- Always show HEX values alongside RGB — they're more universally useful in design tools
- When generating harmony colors, preserve the original saturation/lightness unless asked to adjust
