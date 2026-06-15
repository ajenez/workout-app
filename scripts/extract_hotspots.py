#!/usr/bin/env python3
"""
Regenerate the body-map HOTSPOTS in index.html from the assets/ muscle images.

WHY: the clickable muscle regions are traced from the line art, not hand-drawn. If
you replace a body image, re-normalize it to 500x900 (transparent bg) and run this.

HOW IT WORKS: for each muscle we flood-fill inside its drawn region (the dark outline
strokes are walls, the light fill is passable) from a seed point — or a dense grid of
seeds (a "box") for thin/split muscles like forearms and the two-headed calves — then
trace the filled mask with cv2.findContours + approxPolyDP into a clean polygon.

RUN (needs numpy + opencv in the project venv):
    /Users/antonio/Desktop/testbuilds/testbuilds-virtual-environment/bin/python \
        scripts/extract_hotspots.py

It rewrites the `const HOTSPOTS = {...};` block in index.html and writes verification
overlays to scripts/_checks/ so you can eyeball the alignment.
"""
import os, json
from PIL import Image
import cv2, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
CHECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_checks")
DIM = (52, 60, 72)  # dark slate for non-clickable body fill (so only muscles read as light/tappable)

# seed points (or bounding boxes, is_box=1) per muscle, in the 500x900 image space.
# Bilateral muscles get two entries (L/R). `core` lists several ab-segment seeds (unioned).
SPECS = {
 'female-front':[("shoulders",[(161,192)],0),("shoulders",[(337,192)],0),
   ("chest",[(211,207)],0),("chest",[(287,207)],0),
   ("core",[(249,326)],0),
   ("biceps",[(137,256)],0),("biceps",[(361,256)],0),("forearms",[(80,326)],0),("forearms",[(418,326)],0),
   ("quads",[(192,497)],0),("quads",[(306,497)],0)],
 'female-back':[("traps",[(249,197),(249,149)],0),("shoulders",[(168,177)],0),("shoulders",[(330,177)],0),
   ("back",[(205,251)],0),("back",[(292,251)],0),("triceps",[(135,241)],0),("triceps",[(363,241)],0),
   ("forearms",[(77,322)],0),("forearms",[(421,322)],0),("lowerback",[(249,321)],0),
   ("glutes",[(212,406)],0),("glutes",[(286,406)],0),("hamstrings",[(189,514)],0),("hamstrings",[(309,514)],0),
   ("calves",[(168,702)],0),("calves",[(330,702)],0)],
 'male-front':[("shoulders",[(158,190)],0),("shoulders",[(342,190)],0),("chest",[(215,190)],0),("chest",[(285,190)],0),
   ("core",[(250,260),(250,300),(250,340),(235,280),(265,280),(235,330),(265,330),(250,380)],0),
   ("biceps",[(130,270)],0),("biceps",[(370,270)],0),("forearms",(40,330,130,430),1),("forearms",(370,330,460,430),1),
   ("quads",[(205,520)],0),("quads",[(295,520)],0)],
 'male-back':[("traps",[(250,185)],0),("shoulders",[(158,190)],0),("shoulders",[(342,190)],0),
   ("back",[(215,290)],0),("back",[(285,290)],0),("triceps",[(130,270)],0),("triceps",[(370,270)],0),
   ("forearms",(40,330,130,430),1),("forearms",(370,330,460,430),1),("lowerback",[(250,395)],0),
   ("glutes",[(212,455)],0),("glutes",[(288,455)],0),("hamstrings",[(205,560)],0),("hamstrings",[(295,560)],0),
   ("calves",(175,665,250,815),1),("calves",(250,665,325,815),1)],
}

def passable_mask(im):
    a = np.array(im)
    lum = 0.299*a[:,:,0] + 0.587*a[:,:,1] + 0.114*a[:,:,2]
    return ((a[:,:,3] >= 120) & (lum > 162)).astype(np.uint8)

def nudge(pm, x, y):
    h, w = pm.shape
    if 0 <= x < w and 0 <= y < h and pm[y, x]: return (x, y)
    for rad in range(1, 20):
        for dx in range(-rad, rad+1):
            for dy in (-rad, rad):
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and pm[ny, nx]: return (nx, ny)
        for dy in range(-rad, rad+1):
            for dx in (-rad, rad):
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and pm[ny, nx]: return (nx, ny)
    return None

def flood_region(pm, seeds, do_nudge=True):
    h, w = pm.shape
    region = np.zeros((h, w), np.uint8)
    for (sx, sy) in seeds:
        seed = nudge(pm, sx, sy) if do_nudge else ((sx, sy) if (0 <= sx < w and 0 <= sy < h and pm[sy, sx]) else None)
        if not seed: continue
        x, y = seed
        if region[y, x]: continue
        canvas = pm.copy()
        cv2.floodFill(canvas, np.zeros((h+2, w+2), np.uint8), (x, y), 2)
        region[canvas == 2] = 1
    return region

def contour_points(region, inset=2, eps_frac=0.009, close=0):
    if region.sum() == 0: return None
    m = (region * 255).astype(np.uint8)
    # close bridges thin internal gaps (e.g. the ab division lines) so a segmented
    # muscle like `core` becomes ONE shape; it preserves the outer silhouette.
    if close > 0:
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    if inset > 0:
        er = cv2.erode(m, np.ones((inset*2+1, inset*2+1), np.uint8))
        if er.sum() > 0: m = er
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs: return None
    c = max(cs, key=cv2.contourArea)
    ap = cv2.approxPolyDP(c, eps_frac * cv2.arcLength(c, True), True)
    return [[int(p[0][0]), int(p[0][1])] for p in ap]

def boxseeds(b, s=10):
    x0, y0, x1, y1 = b
    return [(x, y) for x in range(x0, x1+1, s) for y in range(y0, y1+1, s)]

def main():
    os.makedirs(CHECKS, exist_ok=True)
    result = {}
    for name, specs in SPECS.items():
        im = Image.open(os.path.join(ASSETS, f"{name}.png")).convert("RGBA")
        pm = passable_mask(im); h, w = pm.shape
        polys = []
        clickable = np.zeros((h, w), np.uint8)
        for g, seeds, is_box in specs:
            sds = boxseeds(seeds) if is_box else seeds
            reg = flood_region(pm, sds, do_nudge=(not is_box))
            clickable = np.maximum(clickable, reg)
            # `core` spans several drawn ab segments — close the gaps so it traces as one region
            pts = contour_points(reg, close=(19 if g == "core" else 0))
            if pts: polys.append((g, pts))
            else: print("  WARNING empty region:", name, g)
        result[name] = polys
        # Dim every light body-fill pixel that isn't part of a clickable muscle, so only
        # tappable muscles read as light. Idempotent: dimmed pixels are no longer "passable".
        arr = np.array(im)
        nonclick = (pm > 0) & (clickable == 0)
        arr[nonclick] = (DIM[0], DIM[1], DIM[2], 255)
        Image.fromarray(arr).save(os.path.join(ASSETS, f"{name}.png"))
        # verification overlay (from the dimmed image)
        base = arr; al = base[:, :, 3:4] / 255.0
        rgb = (base[:, :, :3] * al + 255 * (1 - al)).astype(np.uint8).copy()
        over = rgb.copy()
        for g, pts in polys:
            arr = np.array(pts, np.int32)
            cv2.fillPoly(over, [arr], (0, 0, 255)); cv2.polylines(rgb, [arr], True, (0, 0, 255), 2)
        rgb = cv2.addWeighted(over, 0.35, rgb, 0.65, 0)
        cv2.imwrite(os.path.join(CHECKS, f"{name}.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        print(f"{name}: {len(polys)} regions")

    def block_for(key):
        return "\n".join(f'        {{ g:"{g}", p:"{" ".join(f"{x},{y}" for x,y in pts)}" }},' for g, pts in result[key])
    block = ("  const HOTSPOTS = {\n    female: {\n      front: [\n" + block_for("female-front") +
             "\n      ],\n      back: [\n" + block_for("female-back") + "\n      ],\n    },\n    male: {\n      front: [\n" +
             block_for("male-front") + "\n      ],\n      back: [\n" + block_for("male-back") + "\n      ],\n    },\n  };")
    idx = os.path.join(ROOT, "index.html")
    html = open(idx).read()
    start = html.index("  const HOTSPOTS = {")
    end = html.index("\n  };", start) + len("\n  };")
    open(idx, "w").write(html[:start] + block + html[end:])
    print("Rewrote HOTSPOTS in index.html. Verification overlays in scripts/_checks/.")

if __name__ == "__main__":
    main()
