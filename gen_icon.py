from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math

SIZES = [256, 64, 48, 32, 16]
FP = "C:\\Windows\\Fonts\\segoeuib.ttf"
BG_COLOR = "#0f1b33"
GLOW_COLOR = "#1d4ed8"
GLOBE_COLOR = "#3b82f6"
NODE_COLOR = "#06b6d4"
ACCENT_COLOR = "#34d399"
TEXT_COLOR = "#ffffff"

def create_ico(sz):
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p = max(sz // 24, 3)
    d.rounded_rectangle([(p, p), (sz - p - 1, sz - p - 1)], radius=sz // 4, fill=BG_COLOR)
    o = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    od = ImageDraw.Draw(o)
    od.rounded_rectangle([(p, p), (sz - p - 1, sz - p - 1)], radius=sz // 4, fill=GLOW_COLOR)
    o = o.filter(ImageFilter.GaussianBlur(radius=sz // 6))
    img = Image.alpha_composite(img, o)
    d = ImageDraw.Draw(img)
    cx, cy = sz // 2, sz // 2
    gr = int(sz / 2 * 0.48)
    t = max(sz // 14, 3)
    d.arc([cx - gr, cy - gr, cx + gr, cy + gr], 0, 360, fill=GLOBE_COLOR, width=t)
    ir = gr - t - max(sz // 20, 2)
    if ir > t:
        d.arc([cx - ir, cy - ir, cx + ir, cy + ir], 0, 360, fill=NODE_COLOR, width=max(t - 2, 2))
    if sz >= 48:
        g2 = int(gr * 0.7)
        for angle in (0, 90):
            rad = math.radians(angle)
            x1 = cx + int(g2 * math.cos(rad))
            y1 = cy + int(g2 * math.sin(rad))
            d.ellipse([x1 - 2, y1 - 2, x1 + 2, y1 + 2], fill=NODE_COLOR)
    if sz >= 64:
        g3 = int(gr * 0.85)
        for angle in (45, 135, 225, 315):
            rad = math.radians(angle)
            x1 = cx + int(g3 * math.cos(rad))
            y1 = cy + int(g3 * math.sin(rad))
            d.line([(cx, cy), (x1, y1)], fill=(6, 182, 212, 80), width=max(t // 2, 1))
            d.ellipse([x1 - t, y1 - t, x1 + t, y1 + t], fill=ACCENT_COLOR)
    dr = max(sz // 12, 4)
    d.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=GLOBE_COLOR)
    d.ellipse([cx - dr // 2, cy - dr // 2, cx + dr // 2, cy + dr // 2], fill=NODE_COLOR)
    if sz >= 64:
        try:
            f = ImageFont.truetype(FP, max(sz // 6, 12))
        except Exception:
            f = ImageFont.load_default()
        tw = d.textbbox((0, 0), "CDN", font=f)[2]
        tx = (sz - tw) // 2
        ty = sz - max(sz // 7, 8) - max(sz // 10, 4)
        d.text((tx, ty + 1), "CDN", fill=BG_COLOR, font=f)
        d.text((tx, ty), "CDN", fill=TEXT_COLOR, font=f)
    return img

imgs = [create_ico(s) for s in SIZES]
out = os.path.join(os.path.dirname(__file__), "icon.ico")
imgs[0].save(out, format="ICO", sizes=[(s, s) for s in SIZES], append_images=imgs[1:])
print(f"OK: {out}")
