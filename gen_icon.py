from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math

SIZES = [256, 64, 48, 32, 16]
FP = "C:\\Windows\\Fonts\\segoeuib.ttf"
C2, C3, C5, WH = "#1e3a5f", "#2563eb", "#34d399", "#ffffff"

def create_ico(sz):
    img = Image.new("RGBA", (sz, sz), (0,0,0,0))
    d = ImageDraw.Draw(img)
    p = max(sz//24,3)
    d.rounded_rectangle([(p,p),(sz-p-1,sz-p-1)], radius=sz//4, fill=C2)
    o = Image.new("RGBA", (sz,sz), (0,0,0,0))
    od = ImageDraw.Draw(o)
    od.rounded_rectangle([(p,p),(sz-p-1,sz-p-1)], radius=sz//4, fill=C3)
    o = o.filter(ImageFilter.GaussianBlur(radius=sz//6))
    img = Image.alpha_composite(img, o); d = ImageDraw.Draw(img)
    cx, cy, t = sz//2, sz//2, max(sz//16,3); gr = int(sz/2*0.55)
    d.arc([cx-gr,cy-gr,cx+gr,cy+gr], 135, 405, fill=C5, width=t)
    ir = gr-t-max(sz//24,2)
    if ir > t: d.arc([cx-ir,cy-ir,cx+ir,cy+ir], 150, 390, fill="#06b6d4", width=max(t-2,2))
    a = math.radians(220); nl = int(gr*1.1)
    d.line([(cx,cy),(cx+int(nl*math.cos(a)),cy-int(nl*math.sin(a)))], fill=WH, width=t+2)
    dr = max(sz//14,4)
    d.ellipse([cx-dr,cy-dr,cx+dr,cy+dr], fill=C5)
    d.ellipse([cx-dr//2,cy-dr//2,cx+dr//2,cy+dr//2], fill=WH)
    if sz >= 64:
        try: f = ImageFont.truetype(FP, max(sz//6,12))
        except: f = ImageFont.load_default()
        tw = d.textbbox((0,0),"CDN",font=f)[2]
        tx, ty = (sz-tw)//2, sz-max(sz//8,6)-max(sz//10,4)
        d.text((tx,ty+1),"CDN",fill=C2,font=f); d.text((tx,ty),"CDN",fill=WH,font=f)
    return img

imgs = [create_ico(s) for s in SIZES]
out = os.path.join(os.path.dirname(__file__),"icon.ico")
imgs[0].save(out, format="ICO", sizes=[(s,s) for s in SIZES], append_images=imgs[1:])
print(f"OK: {out}")
