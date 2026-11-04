"""Sintetiza os efeitos sonoros e a musica do Arena Real. Rode: python tools/gerar_sons.py"""
import os, subprocess, wave
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
SR = 22050
rng = np.random.default_rng(5)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=.005, r=None, curva=4):
    e = np.ones(n)
    na = max(1, int(SR * a))
    e[:na] = np.linspace(0, 1, na)
    r = r or (n / SR - a)
    nr = n - na
    e[na:] = np.exp(-curva * np.linspace(0, 1, nr))
    return e


def sine(f, d):
    x = t(d)
    ph = 2 * np.pi * np.cumsum(f if np.ndim(f) else np.full(len(x), f)) / SR
    return np.sin(ph)


def sweep(f0, f1, d):
    return sine(np.linspace(f0, f1, int(SR * d)), d)


def square(f, d, duty=.5):
    return np.where((t(d) * f) % 1 < duty, 1.0, -1.0)


def tri(f, d):
    return 2 * np.abs(2 * ((t(d) * f) % 1) - 1) - 1


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')


def salvar(nome, x, vol=.9):
    x = x / (np.max(np.abs(x)) or 1) * vol
    with wave.open(os.path.join(OUT, nome + '.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def nota(m):
    return 440 * 2 ** ((m - 69) / 12)


def sfx():
    n = int(SR * .09); salvar('clique', (sine(1100, .09) + .5 * sine(1650, .09)) * env(n, .002, curva=6))
    d = .16; x = np.concatenate([sine(660, d / 2), sine(990, d / 2)]); salvar('escolher', x * env(len(x), .003, curva=5))
    d = .32
    x = sweep(190, 55, d) * env(int(SR * d), .004, curva=5) + .5 * lp(noise(d), 40) * env(int(SR * d), .03, curva=6)
    salvar('invocar', x)
    d = .09
    x = lp(noise(d), 6) * env(int(SR * d), .001, curva=7) + .6 * sweep(220, 90, d) * env(int(SR * d), .001, curva=7)
    salvar('golpe', x)
    d = .12
    x = sweep(1300, 380, d) * env(int(SR * d), .002, curva=6); salvar('flecha', x, .6)
    d = .22
    x = sweep(420, 1500, d) * (1 + .3 * np.sin(2 * np.pi * 30 * t(d))) * env(int(SR * d), .01, curva=4); salvar('magia', x, .6)
    d = .22
    x = lp(noise(d), 4) * env(int(SR * d), .001, curva=6) + sweep(140, 70, d) * env(int(SR * d), .001, curva=6)
    salvar('torre', x)
    d = .75
    x = lp(noise(d), 60) * env(int(SR * d), .004, curva=4.5) * 1.2 + sweep(85, 28, d) * env(int(SR * d), .004, curva=3.5)
    salvar('explosao', x)
    d = 1.4
    x = lp(noise(d), 90) * env(int(SR * d), .01, curva=3) + sweep(70, 24, d) * env(int(SR * d), .005, curva=2.5)
    for k in range(7):
        s0 = int(SR * (.12 + k * .13)); m = lp(noise(.12), 12) * env(int(SR * .12), .001, curva=7) * .6
        x[s0:s0 + len(m)] += m[:len(x) - s0]
    salvar('queda', x)
    d = .13
    x = sweep(750, 220, d) * env(int(SR * d), .002, curva=5); salvar('morte', square(1, d) * 0 + x, .55)
    d = .22
    x = np.concatenate([square(150, d / 2), np.zeros(int(SR * .02)), square(150, d / 2)]) * .5
    salvar('negado', x * env(len(x), .003, curva=2))
    ms = [(72, .14), (76, .14), (79, .14), (84, .5)]
    x = np.concatenate([(square(nota(m), d, .25) * .5 + tri(nota(m - 12), d)) * env(int(SR * d), .005, curva=3) for m, d in ms])
    salvar('vitoria', x)
    ms = [(67, .22), (63, .22), (60, .22), (55, .7)]
    x = np.concatenate([(tri(nota(m), d) + .4 * square(nota(m - 12), d)) * env(int(SR * d), .01, curva=2.5) for m, d in ms])
    salvar('derrota', x)
    d = .7
    x = (sawt(nota(55), d) + sawt(nota(62), d) * .7) * env(int(SR * d), .05, curva=2.2)
    salvar('batalha', lp(x, 3))


def sawt(f, d):
    return 2 * ((t(d) * f) % 1) - 1


def musica():
    bpm = 104; b = 60 / bpm; e = b / 2
    acordes = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62), (57, 60, 64), (53, 57, 60), (55, 59, 62), (52, 56, 59)]
    mel = [[69, 72, 76, 72, 74, 72, 69, 67], [69, 72, 77, 72, 74, 72, 69, 65],
           [67, 72, 76, 72, 79, 76, 72, 67], [71, 74, 79, 74, 77, 74, 71, 67],
           [69, 72, 76, 81, 79, 76, 72, 69], [65, 69, 72, 77, 76, 72, 69, 65],
           [67, 71, 74, 79, 77, 74, 71, 67], [68, 71, 76, 71, 68, 71, 76, 80]]
    total = int(SR * b * 4 * len(acordes))
    mix = np.zeros(total + SR)

    def add(x, tempo):
        i = int(SR * tempo); mix[i:i + len(x)] += x[:len(mix) - i]

    for c, (ac, me) in enumerate(zip(acordes, mel)):
        t0 = c * 4 * b
        for k in range(8):
            f = nota(ac[0] - 12); d = e * .92
            add(square(f, d, .4) * env(int(SR * d), .004, curva=4) * .28, t0 + k * e)
            m = me[k]; d = e * .95
            add((tri(nota(m), d) * .55 + square(nota(m), d, .25) * .12) * env(int(SR * d), .006, curva=3) * .5, t0 + k * e)
        for beat in (0, 2):
            d = .16
            add(sweep(150, 45, d) * env(int(SR * d), .002, curva=5) * .9, t0 + beat * b)
        for beat in range(4):
            d = .05
            add(lp(noise(d), 3) * env(int(SR * d), .001, curva=5) * .22, t0 + beat * b + e)
        for beat in (1, 3):
            d = .12
            add(lp(noise(d), 4) * env(int(SR * d), .001, curva=5) * .35, t0 + beat * b)
        d = b * 3.8
        for nn in ac:
            add(tri(nota(nn), d) * env(int(SR * d), .05, curva=1.2) * .1, t0)
    x = mix[:total]
    x = x / np.max(np.abs(x)) * .8
    tmp = os.path.join(OUT, 'musica_tmp.wav')
    with wave.open(tmp, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-c:a', 'libvorbis', '-q:a', '3',
                    os.path.join(OUT, 'musica.ogg')], check=True)
    os.remove(tmp)


if __name__ == '__main__':
    sfx(); musica(); print('ok')
