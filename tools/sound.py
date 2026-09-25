import json, numpy as np, wave
rng = np.random.default_rng(7)
SR = 48000; T = 24.0; n = int(SR*T)
out = np.zeros(n)
e = json.load(open('events.json'))
def add(sig, t, gain=1.0):
    i = int(t*SR)
    if i >= n: return
    j = min(n, i + len(sig)); out[i:j] += gain*sig[:j-i]
def bandnoise(dur, lo, hi):
    m = int(dur*SR); x = rng.standard_normal(m)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(m, 1/SR); X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, m)
def click(size):
    dur = 0.045; t = np.arange(int(dur*SR))/SR
    base = 2600/np.sqrt(max(1, size))**0.35 * rng.uniform(0.85, 1.2)
    s = sum(a*np.sin(2*np.pi*base*k*t + rng.uniform(0, 6)) for k, a in ((1, 1), (1.73, .6), (2.9, .35)))
    s *= np.exp(-t*170)
    nz = bandnoise(dur, 1500, 9000); nz /= np.abs(nz).max() + 1e-9
    s += 0.9*nz*np.exp(-t*420)
    # tiny double-hit (stud engaging)
    d = int(rng.uniform(0.006, 0.014)*SR); s2 = np.zeros_like(s); s2[d:] = 0.45*s[:-d]
    return (s + s2)/2.2
# brick landings, thinned to a readable rattle
land = sorted(e['land'], key=lambda r: r[0]); last = -1
for t, g, kind, area in land:
    if t - last < 0.05 + rng.uniform(0, 0.03): continue
    last = t
    add(click(area), t, rng.uniform(0.45, 0.9) * (0.7 if kind == 'tile' else 1.0))
# cap lands on the head: heavy clack
tc = e['capDown']
t_ = np.arange(int(0.25*SR))/SR
thud = (np.sin(2*np.pi*140*t_)*np.exp(-t_*28) + 0.5*np.sin(2*np.pi*310*t_)*np.exp(-t_*40))
nz = bandnoise(0.25, 300, 5000); thud += 0.6*nz/np.abs(nz).max()*np.exp(-t_*60)
add(thud, tc - 0.01, 1.3)
for k in range(7): add(click(4), tc + 0.004*k + rng.uniform(0, 0.03), 0.8)
# whoosh into the booklet
w = bandnoise(0.9, 400, 3500); w /= np.abs(w).max(); env = np.sin(np.linspace(0, np.pi, len(w)))**2
add(w*env, e['book'] - 0.25, 0.35)
# page flips: swish + soft slap on landing
for s, d in e['flips']:
    L = max(0.18, d*0.9); sw = bandnoise(L, 900, 7000); sw /= np.abs(sw).max()
    env = np.sin(np.linspace(0, np.pi, len(sw)))**1.5
    add(sw*env, s, 0.28 + 0.12*min(1, 0.4/d))
    slap = bandnoise(0.06, 200, 4000); slap /= np.abs(slap).max(); slap *= np.exp(-np.arange(len(slap))/SR*80)
    add(slap, s + d*0.95, 0.35)
# small room reverb
ir_len = int(0.35*SR); ir = rng.standard_normal(ir_len)*np.exp(-np.arange(ir_len)/SR*14); ir[0] = 0
wet = np.fft.irfft(np.fft.rfft(out, n + ir_len)*np.fft.rfft(ir, n + ir_len))[:n]
mix = out + 0.06*wet/np.abs(wet).max()*np.abs(out).max()
# fade in/out, normalize
fi = int(0.05*SR); mix[:fi] *= np.linspace(0, 1, fi); fo = int(0.4*SR); mix[-fo:] *= np.linspace(1, 0, fo)
mix = mix/np.abs(mix).max()*0.89
st = np.stack([mix, np.roll(mix, 30)], 1)
with wave.open('sfx.wav', 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((st*32767).astype('<i2').tobytes())
print('ok')
