"""Generate a synthetic plant icon for Skill demos; no source content is copied."""
from pathlib import Path
from PIL import Image, ImageDraw
p = Path(__file__).resolve().parent.parent / "examples" / "assets" / "demo_plant.png"
p.parent.mkdir(parents=True, exist_ok=True)
if p.exists():
    raise FileExistsError(p)
im = Image.new("RGBA", (600, 800), (255, 255, 255, 0))
d = ImageDraw.Draw(im)
# Stylized illustrative plant, including roots, stem, foliage and flower.
d.line([(300, 630), (300, 220)], fill="#407E45", width=14, joint="curve")
for root in [
    [(300, 630),(260,690),(245,752)], [(300,630),(300,718),(289,777)],
    [(300,630),(350,708),(380,758)], [(300,675),(215,728)], [(300,680),(415,735)]
]:
    d.line(root, fill="#A77B53", width=9, joint="curve")
for cx, cy, rx, ry, col in [
    (225,395,75,36,"#5BA754"),(379,360,75,36,"#4A9550"),
    (220,275,64,32,"#68B15C"),(382,260,68,35,"#5EA656"),
    (241,515,65,32,"#69B260"),(370,515,65,32,"#4D9852")
]:
    d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry), fill=col)
    d.line((300, cy+5, cx, cy), fill="#407E45", width=8)
flower_x,flower_y=300,170
for cx,cy in [(flower_x-39,flower_y),(flower_x+39,flower_y),
              (flower_x,flower_y-39),(flower_x,flower_y+39)]:
    d.ellipse((cx-29,cy-29,cx+29,cy+29),fill="#F5C553")
d.ellipse((flower_x-22,flower_y-22,flower_x+22,flower_y+22), fill="#8C5A29")
im.save(p)
print(f"DEMO_ASSET={p} DIM={im.size} BYTES={p.stat().st_size}")
