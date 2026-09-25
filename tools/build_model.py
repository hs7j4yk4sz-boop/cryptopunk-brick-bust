import json
from collections import Counter, defaultdict
A = json.load(open('ascii.json'))
D = 20  # depth in studs

def fill_color(r, c):
    ch = A[r][c]
    if ch in 'CL': return 'C'
    if ch in 'SB': return ch
    for d in range(1, 24):
        for cc in ((c + d, c - d) if c < 12 else (c - d, c + d)):
            if 0 <= cc < 24 and A[r][cc] in 'SBCL':
                return 'C' if A[r][cc] in 'CL' else A[r][cc]
    return 'S'

# ---- per-row stud occupancy: rowcells[r][(X,Z)] = colour ----
rowcells = {}
for r in range(4, 24):
    cells = {}
    for c in range(24):
        ch = A[r][c]
        if ch == '.': continue
        z0, z1 = 0, D - 1
        if r == 4: z0, z1 = 4, 15
        elif r == 5: z0, z1 = 2, 17
        if r in (7, 8) and c >= 17: z0, z1 = 4, 15      # sideways brim
        if c == 5 and r in (12, 13, 14): z0, z1 = 6, 13  # ear
        for Z in range(z0, z1 + 1):
            if c == 5 and r in (12, 13, 14): col = 'S'
            elif Z <= z0 + 1: col = ch
            else:
                col = fill_color(r, c)
                if col == 'B' and Z >= 10: col = 'S'
            for dx in (0, 1): cells[(2 * c + dx, Z)] = col
    rowcells[r] = cells
# support pillars under beard sides (scaled from v1)
for (c, rows) in ((17, (22, 23)), (5, (21, 22, 23))):
    for r in rows:
        for Z in range(D):
            for dx in (0, 1): rowcells[r].setdefault((2 * c + dx, Z), 'K')
# chamfer the two back corners of every row (rounder head)
for r, cells in rowcells.items():
    for Z in (D - 2, D - 1):
        xs = [x for (x, z) in cells if z == Z]
        if not xs: continue
        lo, hi = min(xs), max(xs)
        for x in xs:
            if x < lo + 2 or x > hi - 2: del cells[(x, Z)]
# base footprint
BASE = {(x, z) for x in range(8, 38) for z in range(-4, 22)}
# hollow: interior if a 5x5 neighbourhood exists in rows above, same, below
def present(r, p):
    if r == 24: return p in BASE
    return r in rowcells and p in rowcells[r]
hollow = {}
for r, cells in rowcells.items():
    if r <= 5: hollow[r] = set(); continue
    hollow[r] = {p for p in cells if all(present(rr, (p[0] + dx, p[1] + dz)) for rr in (r - 1, r, r + 1) for dx in range(-2, 3) for dz in range(-2, 3))}

# ---- layers (y in plates) ----
layers = []  # (y, h, cells dict, kind)
layers.append((-6, 3, {p: 'K' for p in BASE}, 'brick'))
layers.append((-3, 3, {p: 'K' for p in BASE}, 'brick'))
for k, r in enumerate(range(23, 3, -1)):
    cells = {p: c for p, c in rowcells[r].items() if p not in hollow[r]}
    layers.append((5 * k, 3, cells, 'brick'))
    layers.append((5 * k + 3, 1, dict(cells), 'plate'))
    layers.append((5 * k + 4, 1, dict(cells), 'plate'))

SIZES = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 6), (1, 8), (2, 2), (2, 3), (2, 4), (2, 6), (2, 8)]
TSIZES = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 6), (1, 8), (2, 2), (2, 3), (2, 4)]
PART = {'brick': {(1,1):'3005',(1,2):'3004',(1,3):'3622',(1,4):'3010',(1,6):'3009',(1,8):'3008',(2,2):'3003',(2,3):'3002',(2,4):'3001',(2,6):'2456',(2,8):'3007'},
        'plate': {(1,1):'3024',(1,2):'3023',(1,3):'3623',(1,4):'3710',(1,6):'3666',(1,8):'3460',(2,2):'3022',(2,3):'3021',(2,4):'3020',(2,6):'3795',(2,8):'3034'},
        'tile':  {(1,1):'3070',(1,2):'3069',(1,3):'63864',(1,4):'2431',(1,6):'6636',(1,8):'4162',(2,2):'3068',(2,3):'26603',(2,4):'87079',(2,6):'69729'},
        'slope': {(2,2):'15068'}}
pieces = []

def place(cells, y, h, kind, prefx, below, sizes):
    used = set()
    order = sorted(cells, key=(lambda p: (p[1], p[0])) if prefx else (lambda p: (p[0], p[1])))
    def add(X, Z, w, d, c):
        for i in range(w):
            for j in range(d): used.add((X + i, Z + j))
        pieces.append(dict(x=X, z=Z, y=y, h=h, w=w, d=d, c=c, kind=kind, part=PART[kind][(min(w, d), max(w, d))]))
    # overhang cells first: bridge them to supported cells
    if below is not None:
        for (x, z) in [p for p in order if p not in below]:
            if (x, z) in used: continue
            c = cells[(x, z)]; best = None
            for (a, b) in sizes:
                for (w, d) in ((b, a), (a, b)):
                    for ox in range(w):
                        for oz in range(d):
                            X, Z = x - ox, z - oz
                            fp = [(X + i, Z + j) for i in range(w) for j in range(d)]
                            if all(q in cells and cells[q] == c and q not in used for q in fp):
                                sup = sum(1 for q in fp if q in below)
                                if sup and (best is None or (sup, w * d) > best[0]): best = ((sup, w * d), X, Z, w, d)
            if best:
                _, X, Z, w, d = best; add(X, Z, w, d, c)
    for (x, z) in order:
        if (x, z) in used: continue
        c = cells[(x, z)]; best = None
        cands = [(1, 1)] if c == 'G' and kind != 'tile' else sizes
        for a, b in cands:
            for (w, d) in ((b, a), (a, b)):
                if all((x + i, z + j) in cells and cells[(x + i, z + j)] == c and (x + i, z + j) not in used for i in range(w) for j in range(d)):
                    score = (w * d, (w >= d) if prefx else (d >= w))
                    if best is None or score > best[0]: best = (score, w, d)
        _, w, d = best; add(x, z, w, d, c)

prev = None
for li, (y, h, cells, kind) in enumerate(layers):
    place(cells, y, h, kind, li % 2 == 0, set(prev) if prev is not None else None, SIZES)
    prev = cells

# ---- exposed tops: tiles, curved slopes on the cap ----
occ_top = {}
for i, (y, h, cells, kind) in enumerate(layers):
    nxt = layers[i + 1][2] if i + 1 < len(layers) else {}
    top = y + h
    exposed = {p: c for p, c in cells.items() if p not in nxt}
    # nameplate spot on the base
    if i == 1:
        for x in range(20, 26):
            for z in (-3, -2): exposed.pop((x, z), None)
        pieces.append(dict(x=20, z=-3, y=top, h=1, w=6, d=2, c='T', kind='tile', part='69729', plate=True))
    if not exposed: continue
    # curved slopes on cap blocks (2x2 aligned) with exactly one open side
    slopes = set()
    blocks = defaultdict(list)
    for (x, z), c in exposed.items():
        if c in 'CL': blocks[(x // 2, z // 2)].append((x, z))
    for (bx, bz), ps in blocks.items():
        if len(ps) != 4: continue
        X, Z = 2 * bx, 2 * bz
        def filled(xx, zz): return (xx, zz) in cells
        opens = []
        if not filled(X - 1, Z) and not filled(X - 1, Z + 1): opens.append('W')
        if not filled(X + 2, Z) and not filled(X + 2, Z + 1): opens.append('E')
        if not filled(X, Z - 1) and not filled(X + 1, Z - 1): opens.append('N')   # front
        if not filled(X, Z + 2) and not filled(X + 1, Z + 2): opens.append('S')   # back
        if len(opens) == 1:
            pieces.append(dict(x=X, z=Z, y=top, h=2, w=2, d=2, c='C', kind='slope', part='15068', dir=opens[0]))
            slopes.update(ps)
    rest = {p: c for p, c in exposed.items() if p not in slopes}
    place(rest, top, 1, 'tile', i % 2 == 1, None, TSIZES)

# ---- checks ----
def fp(p): return {(p['x'] + i, p['z'] + j) for i in range(p['w']) for j in range(p['d'])}
F = [fp(p) for p in pieces]
bottoms = defaultdict(list)
for i, p in enumerate(pieces): bottoms[p['y']].append(i)
adj = defaultdict(set); conns = 0
for i, p in enumerate(pieces):
    if p['kind'] in ('tile', 'slope'): continue          # no studs on top
    for j in bottoms.get(p['y'] + p['h'], []):
        n = len(F[i] & F[j])
        if n: adj[i].add(j); adj[j].add(i); conns += n
start = [i for i, p in enumerate(pieces) if p['y'] == -6]
seen = set(start); st = list(start)
while st:
    k = st.pop()
    for n in adj[k]:
        if n not in seen: seen.add(n); st.append(n)
floating = [i for i in range(len(pieces)) if i not in seen]
occ = Counter()
for p, f in zip(pieces, F):
    for (x, z) in f:
        for yy in range(p['y'], p['y'] + p['h']): occ[(x, yy, z)] += 1
coll = sum(1 for v in occ.values() if v > 1)
weak = sum(1 for i, p in enumerate(pieces) if p['y'] > -6 and sum(len(F[i] & F[j]) for j in adj[i]) == 1)
vol = [(x, z) for p, f in zip(pieces, F) for (x, z) in f for _ in range(p['h'])]
cx = sum(x for x, _ in vol) / len(vol); cz = sum(z for _, z in vol) / len(vol)
kinds = Counter(p['kind'] for p in pieces)
print('pieces', len(pieces), dict(kinds), 'connections', conns, 'floating', len(floating), 'collisions', coll, 'weak', weak, 'CoM', round(cx, 1), round(cz, 1))
for i in floating[:10]: print('FLOAT', pieces[i])

# ---- steps: one per layer; tiles/slopes go with the layer they sit on ----
ys = sorted(set(y for (y, h, c, k) in layers))
stepkey = {}
for i, p in enumerate(pieces):
    if p['kind'] in ('tile', 'slope'): stepkey[i] = ('t', p['y'])
    else: stepkey[i] = ('b', p['y'])
# merge tiles sitting at height Y into the step of the layer starting at Y (if any) else own step
keys = sorted(set(stepkey.values()), key=lambda k: (k[1], 0 if k[0] == 'b' else 1))
steps = []
for k in keys:
    ids = [i for i in pieces and range(len(pieces)) if stepkey[i] == k]
    ids.sort(key=lambda i: (pieces[i]['z'], pieces[i]['x']))
    if k[0] == 't' and steps and pieces[steps[-1][0]]['y'] == k[1] and pieces[steps[-1][0]]['kind'] not in ('tile', 'slope'):
        steps[-1] += ids
    else:
        steps.append(ids)
COL = {'K': (11, 'Black', '#161616'), 'S': (69, 'Dark Tan', '#9C8A6A'), 'B': (150, 'Medium Nougat', '#AA7D55'),
       'C': (89, 'Dark Purple', '#5A2E9C'), 'L': (157, 'Medium Lavender', '#A06EB9'), 'G': (15, 'Trans-Light Blue', '#AEEFEC'),
       'T': (85, 'Dark Bluish Gray', '#5B5E5E')}
json.dump(dict(pieces=pieces, steps=steps, colors={k: v[2] for k, v in COL.items()},
               stats=dict(parts=len(pieces), connections=conns, collisions=coll, floating=len(floating), steps=len(steps), weak=weak)),
          open('model2.json', 'w'))
NAMES = {'brick': 'Brick', 'plate': 'Plate', 'tile': 'Tile', 'slope': 'Slope, Curved'}
bom = Counter((p['part'], p['kind'], p['c'], min(p['w'], p['d']), max(p['w'], p['d'])) for p in pieces)
json.dump([dict(part=pt, kind=k, name=f"{NAMES[k]} {w}x{d}" + (' x 2/3' if k == 'slope' else ''), color=COL[c][1], blcolor=COL[c][0], hex=COL[c][2], w=w, d=d, qty=q)
           for (pt, k, c, w, d), q in sorted(bom.items(), key=lambda t: (t[0][2], t[0][1], t[0][3], t[0][4]))], open('bom2.json', 'w'), indent=1)
print(len(steps), 'steps', len(bom), 'lots')
