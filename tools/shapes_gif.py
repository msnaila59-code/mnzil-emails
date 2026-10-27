"""Falling shapes GIF for the email footer.

Mirrors mnzil.com's «Falling Objects» Framer component (Matter.js 0.19):
gravity 1 (~1000 px/s^2), bounciness 0.5, friction 0.3, 200 ms spawn delay,
random start tilt. Email can't run code, so the motion is baked frame by frame;
each shape lands exactly where the Figma design puts it.
"""
import sys, re, math, random
from PIL import Image, ImageDraw

OUT = sys.argv[1]
SC = 2            # output scale (retina)
SS = 4            # supersampling for smooth edges
W1, H1 = 188, 1100 # CSS px; taller than the footer on laptops (~520) and phones (~780 at 150px wide), so the shapes always enter at the very top
E = H1 - 225      # pile (223px) sits on the bottom edge
CLIP_X = 48       # design clips 48px of the cluster at the card's left edge
BLUE = (48, 67, 227)
G = 1000.0        # px/s^2  (Matter gravity 1 at 60fps)
FRAME = 0.04      # 40 ms per frame (25 fps)

# Figma «Shapes» (235.5 x 223.1), drawn in this order (later = on top)
PATHS = [
 ("#E3F8FD","M60.5155 39.2879L60.129 0.740111L100.389 0.370067C122.617 0.165769 140.823 17.266 141.036 38.5479C141.25 59.8298 123.39 77.2614 101.162 77.4657C78.935 77.67 60.7289 60.5698 60.5155 39.2879Z"),
 ("#EB7238","M184.469 147.159C221.222 146.831 224.132 149.563 224.475 184.752C224.817 219.941 221.964 222.728 185.211 223.056C148.459 223.384 145.548 220.651 145.206 185.462C144.863 150.273 147.717 147.486 184.469 147.159Z"),
 ("#DADBF5","M144.728 184.529V223.079H37.2663C16.6929 223.079 0.000213623 207.096 0.000213623 187.398V184.556C0.000213623 164.858 16.6929 148.875 37.2663 148.875H107.433C128.006 148.875 144.699 164.858 144.699 184.556L144.728 184.529Z"),
 ("#F5B31F","M235.536 108.586V147.136H128.075C107.502 147.136 90.809 131.153 90.809 111.455V108.614C90.809 88.9153 107.502 72.9326 128.075 72.9326H198.27C218.844 72.9326 235.536 88.9153 235.536 108.614V108.586Z"),
 ("#97CFE2","M46.572 133.357C74.8895 157.641 90.0114 151.267 90.541 114.897L90.7482 100.612C91.1264 74.8877 87.7913 72.0245 61.1208 75.2092L46.3228 76.9747C8.60275 81.4609 3.69351 96.5798 31.9812 120.838L46.572 133.357Z"),
]

def parse(d):
    toks = re.findall(r'[MLCVHZ]|-?[\d.]+(?:e-?\d+)?', d)
    pts, i, cur, cmd = [], 0, (0.0, 0.0), None
    while i < len(toks):
        t = toks[i]
        if t in 'MLCVHZ': cmd = t; i += 1
        if cmd == 'Z': continue
        if cmd in 'ML':
            cur = (float(toks[i]), float(toks[i+1])); pts.append(cur); i += 2
        elif cmd == 'H':
            cur = (float(toks[i]), cur[1]); pts.append(cur); i += 1
        elif cmd == 'V':
            cur = (cur[0], float(toks[i])); pts.append(cur); i += 1
        elif cmd == 'C':
            p1 = (float(toks[i]), float(toks[i+1])); p2 = (float(toks[i+2]), float(toks[i+3])); p3 = (float(toks[i+4]), float(toks[i+5])); i += 6
            for k in range(1, 33):
                u = k / 32; a = (1-u)**3; b = 3*(1-u)**2*u; c = 3*(1-u)*u*u; e = u**3
                pts.append((a*cur[0]+b*p1[0]+c*p2[0]+e*p3[0], a*cur[1]+b*p1[1]+c*p2[1]+e*p3[1]))
            cur = p3
    return pts

shapes = []
for col, d in PATHS:
    pts = [(x - CLIP_X, y + E) for x, y in parse(d)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    shapes.append(dict(col=tuple(int(col[i:i+2], 16) for i in (1, 3, 5)), rel=[(x-cx, y-cy) for x, y in pts],
                       fx=cx, fy=cy, h=max(ys)-min(ys)))

# landing order bottom-up (index into PATHS): lavender, orange, light-blue, yellow, ice
ORDER = [2, 1, 4, 3, 0]
SUPPORTS = {2: [], 1: [], 4: [2], 3: [2, 1], 0: [3, 4]}   # what each shape lands on
random.seed(7)
E1, E2 = 0.22, 0.18          # effective bounce after tilt/friction losses
for rank, idx in enumerate(ORDER):
    s = shapes[idx]
    y0 = -s['h']/2 - 12 - random.random()*s['h']*0.5
    D = s['fy'] - y0
    tf = math.sqrt(2*D/G)
    ready = max([shapes[j]['ready'] for j in SUPPORTS[idx]], default=0.0)
    spawn = max(rank*0.2, ready - tf)               # 200 ms spawn delay, land once the support has settled
    s.update(y0=y0, spawn=spawn, t1=spawn+tf, dx0=random.uniform(-9, 9),
             a0=math.radians(random.choice([-1, 1])*random.uniform(12, 26)), spin=math.radians(random.uniform(-25, 25)))
    v1 = G*tf; b1 = 2*E1*v1/G; b2 = 2*E2*E1*v1/G
    s.update(v1=v1, b1=b1, b2=b2)
    s['ready'] = s['t1'] + b1*0.9

def pose_fall(s, t):
    if t < s['spawn']: return None
    if t < s['t1']:
        tau = t - s['spawn']
        return (s['fx']+s['dx0'], s['y0']+0.5*G*tau*tau, s['a0']+s['spin']*tau)
    tau = t - s['t1']
    a_imp = s['a0'] + s['spin']*(s['t1']-s['spawn'])
    ang = a_imp*math.exp(-tau*9)*math.cos(tau*15)
    x = s['fx'] + s['dx0']*math.exp(-tau*10)
    vb = E1*s['v1']
    if tau < s['b1']:
        y = s['fy'] - (vb*tau - 0.5*G*tau*tau)
    elif tau < s['b1']+s['b2']:
        k = tau - s['b1']; vb2 = E2*vb; y = s['fy'] - (vb2*k - 0.5*G*k*k)
    else:
        y = s['fy']
    return (x, y, ang)

DROP_DELAY = {2: 0.0, 1: 0.02, 4: 0.06, 3: 0.08, 0: 0.14}
def pose_drop(i, s, t):
    tau = max(0.0, t - DROP_DELAY[i])
    return (s['fx'], s['fy']+0.5*G*tau*tau, (0.6 if i % 2 else -0.6)*tau*tau)

def draw(poses):
    big = Image.new('RGB', (W1*SC*SS, H1*SC*SS), BLUE)
    dr = ImageDraw.Draw(big)
    for s, p in zip(shapes, poses):
        if p is None: continue
        x, y, a = p; ca, sa = math.cos(a), math.sin(a); k = SC*SS
        dr.polygon([((x+rx*ca-ry*sa)*k, (y+rx*sa+ry*ca)*k) for rx, ry in s['rel']], fill=s['col'])
    return big.resize((W1*SC, H1*SC), Image.LANCZOS)

def snap(pal_img, exact):
    """Force exact brand colours into the palette so the GIF blends into the HTML background with no seam."""
    p = pal_img.getpalette()[:768]
    for c in exact:
        d = [sum((p[3*k+j]-c[j])**2 for j in range(3)) for k in range(len(p)//3)]
        for k, dist in enumerate(d):
            if dist <= 27 or dist == min(d): p[3*k:3*k+3] = list(c)   # near-duplicates too, or the mapper may pick them
    pal_img.putpalette(p)
    return pal_img

rest = draw([(s['fx'], s['fy'], 0.0) for s in shapes])
frames, durs = [rest], [3500]
t = 0.0
while True:                                   # drop out through the floor
    t += FRAME
    poses = [pose_drop(i, s, t) for i, s in enumerate(shapes)]
    if all(p[1]-s['h'] > H1 + 20 for p, s in zip(poses, shapes)): break
    frames.append(draw(poses)); durs.append(int(FRAME*1000))
frames.append(Image.new('RGB', rest.size, BLUE)); durs.append(450)
end = max(s['t1']+s['b1']+s['b2'] for s in shapes) + 0.25
t = 0.0
while t < end:                                # fall in, land in the designed pile
    t += FRAME
    frames.append(draw([pose_fall(s, t) for s in shapes])); durs.append(int(FRAME*1000))
frames[-1] = rest

# one shared palette, no dithering -> flat colours, no shimmer
probe = Image.new('RGB', (rest.width, rest.height*3))
for n, f in enumerate([rest, frames[len(frames)//3], frames[-12]]): probe.paste(f, (0, rest.height*n))
pal = snap(probe.quantize(colors=48, method=Image.Quantize.MEDIANCUT), [BLUE]+[s['col'] for s in shapes])
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
q[0].save(OUT+'/shapes-tall.gif', save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True, disposal=1)
