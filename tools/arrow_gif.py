"""Button arrow: white circle with the Figma arrow nudging forward (left, RTL) and back, looped.

usage: python3 arrow_gif.py <out_dir>   (needs Pillow)
"""
import sys, math
from PIL import Image, ImageDraw

OUT = sys.argv[1]
SIZE, SC, SS = 38, 4, 4               # CSS px, output scale, supersampling
ORANGE, WHITE = (235, 114, 56), (255, 255, 255)
SEGS = [((14.25, 9), (3.75, 9)), ((8.25, 4.5), (3.75, 9)), ((3.75, 9), (8.25, 13.5))]  # Figma icon/arrow (18x18)
STROKE = 2.1

def frame(dx):
    k = SC*SS
    im = Image.new('RGB', (SIZE*k, SIZE*k), ORANGE)
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, SIZE*k-1, SIZE*k-1), fill=WHITE)
    r = STROKE/2*k
    for (x1, y1), (x2, y2) in SEGS:
        p1 = ((10+x1+dx)*k, (10+y1)*k); p2 = ((10+x2+dx)*k, (10+y2)*k)
        d.line([p1, p2], fill=ORANGE, width=round(STROKE*k))
        for x, y in (p1, p2): d.ellipse((x-r, y-r, x+r, y+r), fill=ORANGE)
    return im.resize((SIZE*SC, SIZE*SC), Image.LANCZOS)

def snap(pal_img, exact):
    """Force exact brand colours into the palette so the GIF blends into the HTML background with no seam."""
    p = pal_img.getpalette()[:768]
    for c in exact:
        d = [sum((p[3*k+j]-c[j])**2 for j in range(3)) for k in range(len(p)//3)]
        for k, dist in enumerate(d):
            if dist <= 27 or dist == min(d): p[3*k:3*k+3] = list(c)   # near-duplicates too, or the mapper may pick them
    pal_img.putpalette(p)
    return pal_img

ease_out = lambda u: 1-(1-u)**3
ease_io = lambda u: 4*u**3 if u < .5 else 1-(-2*u+2)**3/2
frames, durs = [frame(0)], [600]
for i in range(1, 9): frames.append(frame(-4*ease_out(i/8))); durs.append(40)      # nudge forward
for i in range(1, 11): frames.append(frame(-4*(1-ease_io(i/10)))); durs.append(40)  # glide back
pal = snap(frames[4].quantize(colors=64, method=Image.Quantize.MEDIANCUT), [ORANGE, WHITE])
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
q[0].save(OUT+'/btn-arrow.gif', save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True, disposal=1)
