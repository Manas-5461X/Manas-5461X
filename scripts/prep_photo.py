"""
Prepare source-photo.png for clean monochrome ASCII conversion using PIL + NumPy:
  1. Flood-fill uniform background from corners so the subject is cleanly isolated
  2. Smooth subtle compression noise while preserving crisp drawn lines
  3. Tone-stretch subject luminance so skin lands near white and hair/glasses/suit stay dark
  4. Darken thin line work (glasses, eyes, lips, outlines) so ASCII resolution retains detail
  5. Composite onto pure white and crop square around the subject

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

    python scripts/prep_photo.py [input.png] [output.png]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

LINE_WEIGHT = 0.70


def corner_bg_mask(rgb: np.ndarray, tol: float = 28.0) -> np.ndarray:
    """Return boolean mask (True = foreground subject) via BFS flood-fill from image borders."""
    h, w, _ = rgb.shape
    corners = np.array([rgb[0, 0], rgb[0, w - 1], rgb[h - 1, 0], rgb[h - 1, w - 1]], dtype=np.float32)
    bg_color = np.median(corners, axis=0)
    dist = np.linalg.norm(rgb.astype(np.float32) - bg_color, axis=2)
    is_bg_candidate = dist < tol

    visited = np.zeros((h, w), dtype=bool)
    queue = []
    for x in range(w):
        if is_bg_candidate[0, x]:
            visited[0, x] = True
            queue.append((0, x))
        if is_bg_candidate[h - 1, x] and not visited[h - 1, x]:
            visited[h - 1, x] = True
            queue.append((h - 1, x))
    for y in range(h):
        if is_bg_candidate[y, 0] and not visited[y, 0]:
            visited[y, 0] = True
            queue.append((y, 0))
        if is_bg_candidate[y, w - 1] and not visited[y, w - 1]:
            visited[y, w - 1] = True
            queue.append((y, w - 1))

    idx = 0
    while idx < len(queue):
        cy, cx = queue[idx]
        idx += 1
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and is_bg_candidate[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))

    return ~visited


def main():
    im = Image.open(INP).convert("RGBA")
    rgba = np.array(im)
    rgb = rgba[:, :, :3]
    alpha_ch = rgba[:, :, 3]

    # Use existing alpha if present, otherwise flood-fill uniform background
    if np.min(alpha_ch) < 250:
        fg = alpha_ch > 20
        alpha = alpha_ch.astype(np.float32) / 255.0
    else:
        fg = corner_bg_mask(rgb)
        alpha = fg.astype(np.float32)

    gray_im = im.convert("L")
    smooth = np.array(gray_im.filter(ImageFilter.MedianFilter(size=3)), dtype=np.float32)

    # Tone stretch over subject pixels only
    fg_vals = smooth[fg] if np.any(fg) else smooth.ravel()
    lo, hi = np.percentile(fg_vals, [2, 90])
    denom = max(float(hi - lo), 1.0)
    tone = np.clip((smooth - lo) / denom, 0.0, 1.0)

    # Dark-on-light ridge enhancement (keeps glasses, eyes, mouth, outlines crisp)
    fine = np.array(gray_im.filter(ImageFilter.GaussianBlur(radius=1.5)), dtype=np.float32)
    coarse = np.array(gray_im.filter(ImageFilter.GaussianBlur(radius=6.0)), dtype=np.float32)
    lines = np.clip((coarse - fine) / 40.0, 0.0, 1.0)
    out = np.clip(tone - LINE_WEIGHT * lines, 0.0, 1.0) * 255.0

    # Feather mask lightly and composite onto pure white
    mask_im = Image.fromarray((alpha * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=1.0))
    mask = np.array(mask_im, dtype=np.float32) / 255.0
    out = out * mask + 255.0 * (1.0 - mask)

    ys, xs = np.where(fg)
    if len(xs) == 0 or len(ys) == 0:
        canvas = out.astype(np.uint8)
    else:
        side = max(int(xs.max() - xs.min()), int(ys.max() - ys.min())) + 60
        cx, cy = int(xs.min() + xs.max()) // 2, int(ys.min() + ys.max()) // 2
        canvas = np.full((side, side), 255, dtype=np.uint8)
        x0, y0 = cx - side // 2, cy - side // 2
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
        canvas[sy0 - y0 : sy1 - y0, sx0 - x0 : sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)

    Image.fromarray(canvas, mode="L").save(OUT)
    print("wrote", OUT, canvas.shape)


if __name__ == "__main__":
    main()

