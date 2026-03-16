---
name: svg-trace
description: Convert raster images (PNG, JPG) to scalable vector graphics (SVG) using tracing tools, and generate or edit SVG files programmatically. Use when the user wants to vectorize a bitmap image, create an SVG from a logo or sketch, trace a drawing into a clean vector, generate SVG shapes or icons with code, or manipulate SVG elements programmatically. Triggers on "vectorize", "trace image to SVG", "convert to SVG", "make vector", "SVG from image", "generate SVG", "create icon SVG". Tools: Potrace (https://potrace.sourceforge.net), svgwrite (https://github.com/mozman/svgwrite), cairosvg (https://github.com/Kozea/CairoSVG)
---

# SVG Trace & Generation

Convert raster images to SVG vectors and generate SVG files programmatically.

## Tools Overview

| Tool | Purpose | Install |
|------|---------|---------|
| Potrace / vtracer | Raster → SVG tracing | `pip install vtracer` or `apt install potrace` |
| svgwrite | Generate SVG from Python | `pip install svgwrite` |
| cairosvg | SVG → PNG/PDF render | `pip install cairosvg` |
| Inkscape (CLI) | Full SVG editing | `apt install inkscape` |

## Raster to SVG: vtracer (Python, recommended)

**Repo**: https://github.com/visioncortex/vtracer

```bash
pip install vtracer
```

```python
import vtracer

# Convert PNG to SVG
vtracer.convert_image_to_svg_py(
    "input.png",
    "output.svg",
    colormode="color",       # "color" or "binary"
    hierarchical="stacked",  # "stacked" or "cutout"
    mode="spline",           # "spline", "polygon", or "none"
    filter_speckle=4,        # remove small specks (px)
    color_precision=6,       # number of colors (2-256)
    layer_difference=16,     # color cluster threshold
    corner_threshold=60,     # corner sharpness (degrees)
    length_threshold=4.0,    # min path segment length
    max_iterations=10,
    splice_threshold=45,
    path_precision=3,        # SVG decimal places
)
print("Saved output.svg")
```

```bash
# CLI equivalent
vtracer --input input.png --output output.svg --colormode color
```

## Raster to SVG: Potrace (binary/line art)

```bash
# Convert PNG → PBM → SVG (two steps)
convert input.png input.pbm          # ImageMagick
potrace input.pbm -s -o output.svg   # -s = SVG output

# Or combined
convert input.png pgm:- | potrace - -s -o output.svg
```

## Raster to SVG: Inkscape CLI

```bash
# Inkscape's built-in tracer (Path > Trace Bitmap equivalent)
inkscape input.png --export-filename=output.svg --actions="select-all;org.inkscape.color.tracebitmap"

# Or call Inkscape trace from command line
inkscape --actions="FileImport:input.png;SelectAll;org.inkscape.color.tracebitmap" --export-filename=output.svg
```

## Generate SVG Programmatically (svgwrite)

```python
import svgwrite

dwg = svgwrite.Drawing("output.svg", profile="tiny", size=("800px", "600px"))

# Rectangle
dwg.add(dwg.rect(insert=(50, 50), size=(200, 100),
                 fill="steelblue", stroke="black", stroke_width=2))

# Circle
dwg.add(dwg.circle(center=(400, 300), r=80,
                   fill="none", stroke="tomato", stroke_width=4))

# Text
dwg.add(dwg.text("Hello SVG", insert=(300, 50),
                 fill="black", font_size="24px", font_family="Arial"))

# Path (bezier curve)
dwg.add(dwg.path(d="M 100 200 C 150 100 250 100 300 200",
                 fill="none", stroke="green", stroke_width=3))

# Group
g = dwg.g(id="icon", transform="translate(500,100)")
g.add(dwg.circle(center=(0, 0), r=40, fill="gold"))
dwg.add(g)

dwg.save()
print("Saved output.svg")
```

## Render SVG to PNG (cairosvg)

```python
import cairosvg

cairosvg.svg2png(url="output.svg", write_to="rendered.png", scale=2.0)
```

## Optimize SVG (scour)

```bash
pip install scour
scour -i input.svg -o output.min.svg --enable-viewboxing --enable-id-stripping --shorten-ids
```

## Workflow

1. If converting from raster: use vtracer for color images, potrace for binary/line art
2. If generating from scratch: use svgwrite to build SVG elements programmatically
3. Optimize output with scour for production use
4. Preview by rendering to PNG with cairosvg if needed

## Guardrails

- For photos/complex images, vtracer produces better results than potrace
- Potrace excels at logos, sketches, and black-and-white art
- Always check the SVG file size; complex traces can be very large — use `filter_speckle` to reduce noise
- SVGs are text files; show the user a short preview or open in browser for visual verification
