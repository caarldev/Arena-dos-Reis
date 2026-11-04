"""Arena Real - jogo de batalha de cartas em tempo real (Python + Kivy)."""
import math
import os
import random
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.utils import platform

try:
    from kivy.core.audio import SoundLoader
except Exception:  # sem audio disponivel
    SoundLoader = None

VW, VH, AY = 360, 760, 120   # tela virtual; arena começa em y=120
RIO = 320                    # y do rio dentro da arena (640 de altura)
PONTES = (90, 270)
DURACAO = 180
AGGRO = 100
BASE = os.path.dirname(os.path.abspath(__file__))
AZUL, VERM = (.25, .5, 1), (1, .3, .3)

CARTAS = {
    'cavaleiro': dict(nome='Cavaleiro', custo=3, hp=700, dano=85, alc=16, vel=42, raio=11, n=1, cor=(.35, .55, 1)),
    'arqueiras': dict(nome='Arqueiras', custo=3, hp=180, dano=38, alc=95, vel=48, raio=8, n=2, cor=(1, .5, .8), proj='flecha'),
    'gigante': dict(nome='Gigante', custo=5, hp=1900, dano=110, alc=18, vel=26, raio=16, n=1, cor=(.9, .7, .2), torre=True),
    'goblins': dict(nome='Goblins', custo=2, hp=120, dano=45, alc=14, vel=75, raio=7, n=3, cor=(.3, .9, .3)),
    'mago': dict(nome='Mago', custo=4, hp=320, dano=130, alc=80, vel=36, raio=10, n=1, cor=(1, .4, .2), proj='magia'),
    'barbaros': dict(nome='Bárbaros', custo=4, hp=450, dano=65, alc=14, vel=45, raio=9, n=2, cor=(1, .8, .4)),
    'esqueletos': dict(nome='Esqueletos', custo=1, hp=60, dano=30, alc=12, vel=70, raio=6, n=4, cor=(.9, .9, .9)),
    'fogo': dict(nome='Bola de Fogo', custo=4, feitico=True, dano=260, raio_fx=55, cor=(1, .3, .1)),
}
# cor de fundo (topo, base) de cada carta
FUNDO = {
    'cavaleiro': ((.30, .45, .85), (.12, .20, .50)), 'arqueiras': ((.85, .45, .70), (.45, .15, .35)),
    'gigante': ((.85, .60, .25), (.45, .28, .10)), 'goblins': ((.40, .75, .30), (.14, .35, .12)),
    'mago': ((.95, .50, .25), (.50, .20, .08)), 'barbaros': ((.90, .75, .35), (.50, .35, .12)),
    'esqueletos': ((.65, .65, .75), (.28, .28, .40)), 'fogo': ((.95, .35, .15), (.45, .08, .05)),
}
SONS = ('clique', 'escolher', 'invocar', 'golpe', 'flecha', 'magia', 'torre', 'explosao', 'queda',
        'morte', 'negado', 'vitoria', 'derrota', 'batalha')


class Sons:
    def __init__(self):
        self.on = True
        self.sons, self.last, self.musica = {}, {}, None
        if SoundLoader is None:
            return
        for n in SONS:
            try:
                self.sons[n] = SoundLoader.load(os.path.join(BASE, 'assets', n + '.wav'))
            except Exception:
                self.sons[n] = None
        try:
            self.musica = SoundLoader.load(os.path.join(BASE, 'assets', 'musica.ogg'))
            if self.musica:
                self.musica.loop = True
                self.musica.volume = .35
        except Exception:
            self.musica = None

    def tocar(self, nome, vol=1.0, gap=.05):
        s = self.sons.get(nome)
        agora = time.monotonic()
        if not self.on or not s or agora - self.last.get(nome, 0) < gap:
            return
        self.last[nome] = agora
        try:
            s.volume = vol
            s.stop()
            s.play()
        except Exception:
            pass

    def iniciar_musica(self):
        if self.on and self.musica:
            try:
                if self.musica.state != 'play':
                    self.musica.play()
            except Exception:
                pass

    def parar_musica(self):
        if self.musica:
            try:
                self.musica.stop()
            except Exception:
                pass

    def alternar(self):
        self.on = not self.on
        if self.on:
            self.iniciar_musica()
        else:
            self.parar_musica()


class Ent:
    def __init__(self, x, y, team, hp, raio):
        self.x, self.y, self.team = x, y, team
        self.hp = self.maxhp = hp
        self.raio = raio
        self.flash = 0.0
        self.morto = False


class Unidade(Ent):
    def __init__(self, c, key, x, y, team):
        Ent.__init__(self, x, y, team, c['hp'], c['raio'])
        self.key = key
        self.dano, self.alc, self.vel = c['dano'], c['alc'], c['vel']
        self.cor, self.torre, self.nome = c['cor'], c.get('torre', False), c['nome']
        self.proj = c.get('proj')
        self.cd = random.uniform(0, .4)
        self.age = 0.0
        self.anim = random.uniform(0, 6)
        self.mov = False
        self.dir = 1
        self.lunge = 0.0
        self.lx = self.ly = 0.0


class Torre(Ent):
    def __init__(self, x, y, team, rei):
        Ent.__init__(self, x, y, team, 2400 if rei else 1400, 24 if rei else 19)
        self.rei = rei
        self.alc = 120 if rei else 110
        self.dano = 70 if rei else 55
        self.cd = 0.0
        self.rec = 0.0


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


class Jogo(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.cache, self.imgs = {}, {}
        self.s, self.ox, self.oy = 1, 0, 0
        self.sons = Sons()
        self.estado = 'menu'
        self.units, self.fx, self.torres = [], [], []
        self.projs, self.parts, self.nums = [], [], []
        self.mao, self.fila, self.sel = [], [], None
        self.drag = None
        self.elixir, self.tempo, self.ia_cd, self.resultado = [5, 5], DURACAO, 3, ''
        self.t = 0.0
        self.shake = 0.0
        self.shx = self.shy = 0.0
        self.banner = None
        self.fim_t = 0.0
        self.nope = 0.0
        self.dobro = False
        Clock.schedule_interval(self.update, 1 / 30.)

    # ------------------------------------------------------------ recursos
    def img(self, nome):
        if nome not in self.imgs:
            try:
                self.imgs[nome] = CoreImage(os.path.join(BASE, 'assets', nome + '.png')).texture
            except Exception:
                self.imgs[nome] = None
        return self.imgs[nome]

    # ------------------------------------------------------------ lógica
    def novo(self):
        self.estado = 'jogo'
        self.tempo = DURACAO
        self.elixir = [5.0, 5.0]
        self.ia_cd = 4.0
        self.dobro = False
        ordem = list(CARTAS)
        random.shuffle(ordem)
        self.mao, self.fila, self.sel, self.drag = ordem[:4], ordem[4:], None, None
        self.units, self.fx, self.resultado = [], [], ''
        self.projs, self.parts, self.nums = [], [], []
        self.torres = [
            Torre(90, 120, 0, False), Torre(270, 120, 0, False), Torre(180, 60, 0, True),
            Torre(90, 520, 1, False), Torre(270, 520, 1, False), Torre(180, 580, 1, True)]
        self.banner = ('BATALHA!', (1, .85, .2), 1.6, 1.6)
        self.sons.tocar('batalha')
        self.sons.iniciar_musica()

    def pode_jogar(self, key, x, y):
        c = CARTAS[key]
        return self.elixir[0] >= c['custo'] and 0 <= x <= 360 and (c.get('feitico') or 8 < y < RIO - 12)

    def jogar(self, team, key, x, y):
        c = CARTAS[key]
        self.elixir[team] -= c['custo']
        if c.get('feitico'):
            for e in self.units + self.torres:
                if e.team != team and e.hp > 0 and math.hypot(e.x - x, e.y - y) <= c['raio_fx'] + e.raio:
                    self.dar_dano(e, c['dano'] if isinstance(e, Unidade) else c['dano'] * 0.4)
            self.fx.append(dict(t='boom', x=x, y=y, ttl=.45, tot=.45, r=c['raio_fx']))
            self.explosao(x, y, c['raio_fx'])
            self.shake = max(self.shake, .25)
            self.sons.tocar('explosao')
        else:
            for i in range(c['n']):
                off = (i - (c['n'] - 1) / 2.) * 16
                u = Unidade(c, key, x + off, y + random.uniform(-4, 4), team)
                u.dir = 1 if random.random() < .5 else -1
                self.units.append(u)
                self.fx.append(dict(t='anel', x=u.x, y=u.y, ttl=.4, tot=.4, r=u.raio * 2.4, team=team))
            self.sons.tocar('invocar')

    def explosao(self, x, y, r):
        for _ in range(26):
            a = random.uniform(0, 6.283)
            v = random.uniform(40, 170)
            self.parts.append(dict(x=x, y=y, vx=math.cos(a) * v, vy=math.sin(a) * v, ttl=.6, tot=.6,
                                   cor=random.choice([(1, .55, .1), (1, .85, .2), (1, .3, .1), (.35, .3, .3)]),
                                   r=random.uniform(3, 7), g=0))

    def poeira(self, x, y, cor, n=8, g=-60):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            v = random.uniform(15, 70)
            self.parts.append(dict(x=x, y=y, vx=math.cos(a) * v, vy=math.sin(a) * v + 20, ttl=.5, tot=.5,
                                   cor=cor, r=random.uniform(2, 4.5), g=g))

    def dar_dano(self, alvo, valor, mostrar=True):
        if alvo.hp <= 0:
            return
        alvo.hp -= valor
        alvo.flash = .12
        if mostrar:
            self.nums.append(dict(x=alvo.x + random.uniform(-6, 6), y=alvo.y + alvo.raio + 6, txt=str(int(valor)),
                                  ttl=.7, tot=.7, cor=(1, .95, .6) if alvo.team == 1 else (1, .5, .5)))
        if alvo.hp <= 0 and isinstance(alvo, Torre) and not alvo.morto:
            alvo.morto = True
            self.shake = max(self.shake, .5)
            self.explosao(alvo.x, alvo.y, 30)
            for _ in range(14):
                self.poeira(alvo.x + random.uniform(-14, 14), alvo.y + random.uniform(-10, 10), (.6, .58, .6), 2, -30)
            self.sons.tocar('queda', 1.0, .2)
            self.banner = ('TORRE DERRUBADA!', (1, .5, .3) if alvo.team == 0 else (.5, .85, 1), 1.2, 1.2)

    def atacar(self, atk, alvo, dano, proj):
        if proj:
            self.projs.append(dict(x=atk.x, y=atk.y, alvo=alvo, dano=dano, kind=proj, team=atk.team, ang=0))
            self.sons.tocar('magia' if proj == 'magia' else 'flecha', .7)
        else:
            self.dar_dano(alvo, dano)
            if isinstance(atk, Unidade):
                atk.lunge = .18
                atk.lx, atk.ly = alvo.x - atk.x, alvo.y - atk.y
            self.fx.append(dict(t='faisca', x=alvo.x, y=alvo.y + alvo.raio * .4, ttl=.18, tot=.18))
            self.sons.tocar('torre' if isinstance(alvo, Torre) else 'golpe', .8)

    def alvo(self, u):
        melhor, bd = None, 1e9
        if not u.torre:
            for e in self.units:
                if e.team != u.team and e.hp > 0:
                    d = dist(u, e)
                    if d < AGGRO and d < bd:
                        melhor, bd = e, d
            if melhor:
                return melhor
        for t in self.torres:
            if t.team != u.team and t.hp > 0:
                d = dist(u, t)
                if d < bd:
                    melhor, bd = t, d
        return melhor

    def coroas(self, team):
        mortas = [t for t in self.torres if t.team != team and t.hp <= 0]
        if any(t.rei for t in mortas):
            return 3
        return len(mortas)

    def update(self, dt):
        dt = min(dt, .1)
        self.t += dt
        if self.estado == 'jogo':
            self.passo(dt)
        elif self.estado == 'fim':
            self.fim_t += dt
            if self.resultado == 'VITÓRIA!' and random.random() < .5:
                self.parts.append(dict(x=random.uniform(10, 350), y=640, vx=random.uniform(-20, 20), vy=random.uniform(-90, -40),
                                       ttl=2.5, tot=2.5, g=-10, r=random.uniform(2.5, 4.5), conf=True,
                                       cor=random.choice([(1, .85, .2), (1, .4, .5), (.4, .8, 1), (.5, 1, .5)])))
        for f in self.fx:
            f['ttl'] -= dt
        self.fx = [f for f in self.fx if f['ttl'] > 0]
        for p in self.parts:
            p['ttl'] -= dt
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += p['g'] * dt
        self.parts = [p for p in self.parts if p['ttl'] > 0][-300:]
        for n in self.nums:
            n['ttl'] -= dt
            n['y'] += 28 * dt
        self.nums = [n for n in self.nums if n['ttl'] > 0][-40:]
        if self.banner:
            self.banner = (self.banner[0], self.banner[1], self.banner[2] - dt, self.banner[3])
            if self.banner[2] <= 0:
                self.banner = None
        self.nope = max(0, self.nope - dt)
        if self.shake > 0:
            self.shake -= dt
            m = min(1, self.shake * 4) * 5
            self.shx, self.shy = random.uniform(-m, m), random.uniform(-m, m)
        else:
            self.shx = self.shy = 0
        self.draw()

    def passo(self, dt):
        self.tempo -= dt
        if self.tempo <= 60 and not self.dobro:
            self.dobro = True
            self.banner = ('ELIXIR EM DOBRO!', (.85, .45, 1), 1.6, 1.6)
        reg = 2.8 if self.tempo > 60 else 1.4
        for t in (0, 1):
            self.elixir[t] = min(10.0, self.elixir[t] + dt / reg)

        # IA inimiga
        self.ia_cd -= dt
        if self.ia_cd <= 0:
            op = [k for k, c in CARTAS.items() if c['custo'] <= self.elixir[1]]
            if op and (self.elixir[1] >= 6 or random.random() < .5):
                k = random.choice(op)
                if CARTAS[k].get('feitico'):
                    alvos = [u for u in self.units if u.team == 0 and u.hp > 0]
                    if alvos:
                        a = random.choice(alvos)
                        self.jogar(1, k, a.x, a.y)
                else:
                    self.jogar(1, k, random.choice(PONTES) + random.uniform(-25, 25), random.uniform(380, 500))
                self.ia_cd = random.uniform(2, 4)
            else:
                self.ia_cd = 1.0

        vivos = [u for u in self.units if u.hp > 0]
        for u in vivos:
            if u.hp <= 0:
                continue
            u.cd -= dt
            u.age += dt
            u.flash = max(0, u.flash - dt)
            u.lunge = max(0, u.lunge - dt)
            u.mov = False
            if u.age < .3:
                continue
            a = self.alvo(u)
            if not a:
                continue
            d = dist(u, a)
            if d - a.raio <= u.alc:
                if u.cd <= 0:
                    u.cd = 1.0
                    self.atacar(u, a, u.dano, u.proj)
                if abs(a.x - u.x) > 3:
                    u.dir = 1 if a.x > u.x else -1
            else:
                tx, ty = a.x, a.y
                if (u.y > RIO) != (a.y > RIO):
                    tx = min(PONTES, key=lambda b: abs(b - u.x))
                    ty = RIO + (12 if a.y > RIO else -12)
                dx, dy = tx - u.x, ty - u.y
                dd = math.hypot(dx, dy) or 1
                u.x += dx / dd * u.vel * dt
                u.y += dy / dd * u.vel * dt
                u.mov = True
                u.anim += dt * u.vel * .2
                if abs(dx) > 2:
                    u.dir = 1 if dx > 0 else -1
        # separação simples
        for i in range(len(vivos)):
            for j in range(i + 1, len(vivos)):
                a, b = vivos[i], vivos[j]
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy) or .01
                m = (a.raio + b.raio) * .9
                if d < m:
                    p = (m - d) / 2 / d
                    a.x -= dx * p; a.y -= dy * p
                    b.x += dx * p; b.y += dy * p
        for u in vivos:
            u.x = max(8, min(352, u.x))
            u.y = max(0, min(640, u.y))

        # torres atiram
        for t in self.torres:
            t.flash = max(0, t.flash - dt)
            t.rec = max(0, t.rec - dt)
            if t.hp <= 0:
                continue
            t.cd -= dt
            if t.cd > 0:
                continue
            alvos = [e for e in vivos if e.team != t.team and e.hp > 0 and dist(t, e) <= t.alc + e.raio]
            if alvos:
                a = min(alvos, key=lambda e: dist(t, e))
                t.cd = .8
                t.rec = .15
                self.atacar(t, a, t.dano, 'flecha')

        # projéteis
        for p in self.projs:
            a = p['alvo']
            if a.hp <= 0:
                p['dano'] = 0
                p['x'] = p['y'] = -999
                continue
            dx, dy = a.x - p['x'], a.y - p['y']
            d = math.hypot(dx, dy) or 1
            passo = 260 * dt
            p['ang'] = math.atan2(dy, dx)
            if d <= passo + a.raio * .5:
                self.dar_dano(a, p['dano'])
                self.fx.append(dict(t='faisca', x=a.x, y=a.y + a.raio * .4, ttl=.18, tot=.18))
                self.sons.tocar('torre' if isinstance(a, Torre) else 'golpe', .6)
                p['dano'] = 0
                p['x'] = p['y'] = -999
            else:
                p['x'] += dx / d * passo
                p['y'] += dy / d * passo
                if p['kind'] == 'magia' and random.random() < .6:
                    self.parts.append(dict(x=p['x'], y=p['y'], vx=0, vy=0, ttl=.3, tot=.3, g=0, r=3,
                                           cor=(.5, .85, 1)))
        self.projs = [p for p in self.projs if p['x'] > -900]

        # mortes
        for u in self.units:
            if u.hp <= 0 and not u.morto:
                u.morto = True
                self.poeira(u.x, u.y + u.raio, tuple(min(1, c + .1) for c in u.cor), 9)
                self.sons.tocar('morte', .7, .08)
        self.units = [u for u in self.units if u.hp > 0]

        # fim de jogo
        rei0 = next(t for t in self.torres if t.team == 0 and t.rei)
        rei1 = next(t for t in self.torres if t.team == 1 and t.rei)
        if rei1.hp <= 0 or rei0.hp <= 0 or self.tempo <= 0:
            a, b = self.coroas(0), self.coroas(1)
            self.resultado = 'VITÓRIA!' if a > b else 'DERROTA' if b > a else 'EMPATE'
            self.estado = 'fim'
            self.fim_t = 0.0
            self.sel = self.drag = None
            self.sons.tocar({'VITÓRIA!': 'vitoria', 'DERROTA': 'derrota'}.get(self.resultado, 'batalha'))

    # ------------------------------------------------------------ entrada
    def lay(self):
        self.s = min(self.width / VW, self.height / VH) or 1
        self.ox = self.x + (self.width - VW * self.s) / 2
        self.oy = self.y + (self.height - VH * self.s) / 2

    def virt(self, touch):
        return (touch.x - self.ox) / self.s, (touch.y - self.oy) / self.s

    def som_btn(self, vx, vy):
        if self.estado == 'menu':
            return 296 <= vx <= 352 and 722 <= vy <= 744
        return 300 <= vx <= 352 and AY + 592 <= vy <= AY + 610

    def carta_em(self, vx, vy):
        if vy < AY:
            for i in range(4):
                x0 = 11 + i * 86
                if x0 <= vx <= x0 + 80 and 28 <= vy <= 112:
                    return i
        return None

    def on_touch_down(self, touch):
        self.lay()
        vx, vy = self.virt(touch)
        if self.som_btn(vx, vy):
            self.sons.alternar()
            self.sons.tocar('clique')
            return True
        if self.estado == 'menu':
            self.sons.tocar('clique')
            self.novo()
            return True
        if self.estado == 'fim':
            if self.fim_t > 1.2:
                self.sons.tocar('clique')
                self.novo()
            return True
        i = self.carta_em(vx, vy)
        if i is not None:
            self.sel = None if self.sel == i else i
            if self.sel is not None:
                self.sons.tocar('escolher')
                self.drag = dict(i=i, x=vx, y=vy - AY, moveu=False)
            return True
        if vy < AY:
            return True
        if self.sel is not None:
            self.tentar_jogar(vx, vy - AY)
        return True

    def tentar_jogar(self, ax, ay):
        key = self.mao[self.sel]
        if self.pode_jogar(key, ax, ay):
            self.jogar(0, key, ax, ay)
            self.fila.append(key)
            self.mao[self.sel] = self.fila.pop(0)
            self.sel = None
            return True
        if self.elixir[0] < CARTAS[key]['custo']:
            self.nope = .5
            self.sons.tocar('negado', .8, .2)
        return False

    def on_touch_move(self, touch):
        if self.drag and self.estado == 'jogo':
            self.lay()
            vx, vy = self.virt(touch)
            self.drag['x'], self.drag['y'] = vx, vy - AY
            if vy > AY + 10:
                self.drag['moveu'] = True
        return True

    def on_touch_up(self, touch):
        d, self.drag = self.drag, None
        if d and d['moveu'] and self.estado == 'jogo' and self.sel is not None:
            if not self.tentar_jogar(d['x'], d['y']):
                pass
        return True

    # ------------------------------------------------------------ desenho
    def X(self, x):
        return self.ox + x * self.s + self.shx

    def Y(self, y):
        return self.oy + (y + AY) * self.s + self.shy

    def hx(self, x):
        return self.ox + x * self.s

    def hy(self, y):
        return self.oy + y * self.s

    def txt(self, texto, x, y, size, cor=(1, 1, 1, 1), sombra=True):
        px = max(8, int(size * self.s))
        key = (texto, px)
        t = self.cache.get(key)
        if t is None:
            if len(self.cache) > 500:
                self.cache.clear()
            lab = CoreLabel(text=texto, font_size=px, bold=True)
            lab.refresh()
            t = self.cache[key] = lab.texture
        if sombra:
            Color(0, 0, 0, .55 * (cor[3] if len(cor) > 3 else 1))
            Rectangle(texture=t, pos=(x - t.width / 2 + max(1, px * .07), y - t.height / 2 - max(1, px * .07)), size=t.size)
        Color(*cor)
        Rectangle(texture=t, pos=(x - t.width / 2, y - t.height / 2), size=t.size)

    def sprite(self, nome, cx, cy, w, h=None, cor=(1, 1, 1, 1), flip=False):
        tx = self.img(nome)
        if tx is None:
            return
        h = h or w
        Color(*cor)
        if flip:
            c = tx.tex_coords
            Rectangle(texture=tx, pos=(cx - w / 2, cy - h / 2), size=(w, h),
                      tex_coords=(c[2], c[3], c[0], c[1], c[6], c[7], c[4], c[5]))
        else:
            Rectangle(texture=tx, pos=(cx - w / 2, cy - h / 2), size=(w, h))

    def barra(self, x, y, w, h, frac, cor):
        Color(0, 0, 0, .7)
        RoundedRectangle(pos=(x - w / 2 - 1.5, y - 1), size=(w + 3, h + 3), radius=[h / 2 + 1])
        Color(.15, .15, .2, 1)
        RoundedRectangle(pos=(x - w / 2, y), size=(w, h + 1), radius=[h / 2])
        if frac > 0:
            Color(*cor)
            RoundedRectangle(pos=(x - w / 2, y), size=(max(h, w * frac), h + 1), radius=[h / 2])
            Color(1, 1, 1, .3)
            Rectangle(pos=(x - w / 2 + h / 2, y + h * .55), size=(max(0, w * frac - h), h * .35))

    def draw(self):
        self.lay()
        c = self.canvas
        c.clear()
        with c:
            Color(.05, .06, .12)
            Rectangle(pos=self.pos, size=self.size)
            if self.estado == 'menu':
                self.draw_menu()
                return
            self.draw_arena()
            self.draw_hud()
            if self.estado == 'fim':
                self.draw_fim()

    def draw_arena(self):
        s = self.s
        self.sprite('arena', self.X(180), self.Y(320), 360 * s, 640 * s)
        if self.sel is not None and not CARTAS[self.mao[self.sel]].get('feitico'):
            Color(1, 1, 1, .10 + .04 * math.sin(self.t * 5))
            Rectangle(pos=(self.X(0), self.Y(0)), size=(360 * s, (RIO - 12) * s))
            Color(1, 1, 1, .5)
            Line(points=[self.X(0), self.Y(RIO - 12), self.X(360), self.Y(RIO - 12)], width=1.2, dash_length=6, dash_offset=4)

        # torres
        for t in sorted(self.torres, key=lambda e: -e.y):
            sz = (112 if t.rei else 88) * s
            if t.hp <= 0:
                self.sprite('ruinas', self.X(t.x), self.Y(t.y) + sz * .05, sz)
                continue
            cor = (1, .55, .55, 1) if t.flash > 0 else (1, 1, 1, 1)
            Color(0, 0, 0, .25)
            Ellipse(pos=(self.X(t.x) - sz * .36, self.Y(t.y) - sz * .30), size=(sz * .72, sz * .2))
            rec = 2 * s * (t.rec / .15)
            self.sprite(('rei_' if t.rei else 'torre_') + ('b' if t.team == 0 else 'r'),
                        self.X(t.x), self.Y(t.y) + sz * .16 - rec, sz, cor=cor)
        # torres: barras (abaixo da base, para nao sumir sob o HUD)
        for t in self.torres:
            if t.hp <= 0:
                continue
            szv = 112 if t.rei else 88
            by = self.Y(t.y) - (.27 * szv + 10) * s
            col = (.3, .85, 1) if t.team == 0 else (1, .35, .35)
            self.barra(self.X(t.x), by, 44 * s, 5 * s, t.hp / t.maxhp, col)
            self.txt(str(int(max(0, t.hp))), self.X(t.x), by - 8 * s, 9)

        # unidades (de cima para baixo)
        for u in sorted(self.units, key=lambda e: -e.y):
            r = u.raio * s
            tam = u.raio * 2.5 * s
            esc = 1.0
            if u.age < .3:
                k = u.age / .3
                esc = .35 + .65 * k + .25 * math.sin(k * 3.14)
            bob = abs(math.sin(u.anim)) * 3 * s if u.mov else math.sin(self.t * 4 + u.anim) * .8 * s
            lx = ly = 0
            if u.lunge > 0:
                dd = math.hypot(u.lx, u.ly) or 1
                f = math.sin(u.lunge / .18 * 3.14) * 5 * s
                lx, ly = u.lx / dd * f, u.ly / dd * f
            px, py = self.X(u.x), self.Y(u.y)
            Color(0, 0, 0, .3)
            Ellipse(pos=(px - r * 1.1, py - r * .5), size=(r * 2.2, r * 1.0))
            Color(*(AZUL if u.team == 0 else VERM), .95)
            Line(ellipse=(px - r * 1.15, py - r * .55, r * 2.3, r * 1.1), width=max(1.5, 2 * s))
            cor = (1, .5, .5, 1) if u.flash > 0 else (1, 1, 1, 1)
            self.sprite(u.key, px + lx, py + tam * .32 * esc + bob + ly, tam * esc, cor=cor, flip=u.dir < 0)
            if u.hp < u.maxhp:
                self.barra(px, py + tam * .85, max(22, r * 2.4), 3 * s, u.hp / u.maxhp,
                           (.3, .9, 1) if u.team == 0 else (1, .35, .35))

        # projéteis
        for p in self.projs:
            px, py = self.X(p['x']), self.Y(p['y'])
            if p['kind'] == 'flecha':
                ca, sa = math.cos(p['ang']), math.sin(p['ang'])
                Color(.95, .9, .75, 1)
                Line(points=[px - ca * 9 * s, py - sa * 9 * s, px, py], width=max(1.5, 1.8 * s))
                Color(1, 1, 1, 1)
                Ellipse(pos=(px - 2 * s, py - 2 * s), size=(4 * s, 4 * s))
            else:
                for rr, col in ((7, (.4, .8, 1, .35)), (4.5, (.6, .9, 1, .9)), (2.2, (1, 1, 1, 1))):
                    Color(*col)
                    Ellipse(pos=(px - rr * s, py - rr * s), size=(2 * rr * s, 2 * rr * s))

        # efeitos
        for f in self.fx:
            k = f['ttl'] / f['tot']
            if f['t'] == 'boom':
                rr = f['r'] * s * (1.25 - .25 * k)
                self.sprite('fogo', self.X(f['x']), self.Y(f['y']), rr * 2.3, cor=(1, 1, 1, min(1, k * 1.5)))
                Color(1, .6, .15, .35 * k)
                Ellipse(pos=(self.X(f['x']) - rr, self.Y(f['y']) - rr), size=(2 * rr, 2 * rr))
                Color(1, .9, .5, .9 * k)
                Line(circle=(self.X(f['x']), self.Y(f['y']), rr * (1.3 - .3 * k)), width=2.5 * s)
            elif f['t'] == 'anel':
                rr = f['r'] * s * (1.6 - .6 * k)
                Color(*(AZUL if f['team'] == 0 else VERM), .8 * k)
                Line(ellipse=(self.X(f['x']) - rr, self.Y(f['y']) - rr * .5, rr * 2, rr), width=2 * s)
            elif f['t'] == 'faisca':
                rr = (6 + 10 * (1 - k)) * s
                Color(1, .95, .6, k)
                for a in range(0, 360, 60):
                    ca, sa = math.cos(math.radians(a + 15)), math.sin(math.radians(a + 15))
                    Line(points=[self.X(f['x']) + ca * rr * .3, self.Y(f['y']) + sa * rr * .3,
                                 self.X(f['x']) + ca * rr, self.Y(f['y']) + sa * rr], width=1.6 * s)
        # partículas
        for p in self.parts:
            k = p['ttl'] / p['tot']
            Color(p['cor'][0], p['cor'][1], p['cor'][2], min(1, k * 1.5))
            rr = p['r'] * s * (.5 + .5 * k)
            if p.get('conf'):
                Rectangle(pos=(self.hx(p['x']), self.hy(p['y'] + AY)), size=(rr * 1.6, rr * .9))
            else:
                Ellipse(pos=(self.X(p['x']) - rr, self.Y(p['y']) - rr), size=(2 * rr, 2 * rr))
        # números de dano
        for n in self.nums:
            k = n['ttl'] / n['tot']
            self.txt(n['txt'], self.X(n['x']), self.Y(n['y']), 11, (n['cor'][0], n['cor'][1], n['cor'][2], min(1, k * 2)))

        # fantasma ao arrastar a carta
        if self.drag and self.drag['moveu'] and self.sel is not None and self.estado == 'jogo':
            key = self.mao[self.sel]
            cd = CARTAS[key]
            gx, gy = self.drag['x'], self.drag['y']
            ok = self.pode_jogar(key, gx, gy)
            if cd.get('feitico'):
                rr = cd['raio_fx'] * s
                Color(1, .4, .1, .25)
                Ellipse(pos=(self.X(gx) - rr, self.Y(gy) - rr), size=(2 * rr, 2 * rr))
                Color(1, .8, .3, .9)
                Line(circle=(self.X(gx), self.Y(gy), rr), width=2 * s)
            else:
                Color(1, 1, 1, .35 if ok else .15)
                rr = cd['raio'] * 1.6 * s
                Ellipse(pos=(self.X(gx) - rr, self.Y(gy) - rr * .5), size=(2 * rr, rr))
                self.sprite(key, self.X(gx), self.Y(gy) + cd['raio'] * 2.5 * s * .32, cd['raio'] * 2.5 * s,
                            cor=(1, 1, 1, .75 if ok else .3))
                if not ok:
                    Color(1, .2, .2, .9)
                    Line(circle=(self.X(gx), self.Y(gy), rr), width=1.5 * s)

    def draw_hud(self):
        s = self.s
        # topo
        self.sprite('topbar', self.hx(180), self.hy(AY + 627), 360 * s, 26 * s)
        m, sg = divmod(max(0, int(self.tempo)), 60)
        cor_t = (1, .9, .3, 1) if self.tempo <= 60 else (1, 1, 1, 1)
        if self.tempo <= 10 and int(self.t * 3) % 2:
            cor_t = (1, .3, .3, 1)
        self.txt('%d:%02d' % (m, sg), self.hx(180), self.hy(AY + 627), 17, cor_t)
        if self.dobro:
            Color(.7, .3, .95, 1)
            RoundedRectangle(pos=(self.hx(212), self.hy(AY + 620)), size=(26 * s, 14 * s), radius=[7 * s])
            self.txt('x2', self.hx(225), self.hy(AY + 627), 10)
        self.sprite('coroa', self.hx(24), self.hy(AY + 627), 20 * s)
        self.txt('%d' % self.coroas(0), self.hx(46), self.hy(AY + 627), 15, (.55, .75, 1, 1))
        self.txt('Você', self.hx(82), self.hy(AY + 627), 11, (.7, .85, 1, 1))
        self.txt('Inimigo', self.hx(274), self.hy(AY + 627), 11, (1, .65, .65, 1))
        self.txt('%d' % self.coroas(1), self.hx(314), self.hy(AY + 627), 15, (1, .5, .5, 1))
        self.sprite('coroa', self.hx(336), self.hy(AY + 627), 20 * s)
        # botão de som
        on = self.sons.on
        Color(*((.15, .55, .25, .9) if on else (.6, .15, .15, .9)))
        RoundedRectangle(pos=(self.hx(300), self.hy(AY + 592)), size=(52 * s, 18 * s), radius=[9 * s])
        self.txt('SOM' if on else 'MUDO', self.hx(326), self.hy(AY + 601), 9)

        # painel de cartas
        self.sprite('painel', self.hx(180), self.hy(AY / 2), 360 * s, AY * s)
        for i, key in enumerate(self.mao):
            cd = CARTAS[key]
            x0 = 11 + i * 86
            ok = self.elixir[0] >= cd['custo']
            sel = self.sel == i
            up = 7 if sel else 0
            bx, by = self.hx(x0), self.hy(28 + up)
            w, h = 80 * s, 84 * s
            if sel:
                Color(1, .9, .3, .35 + .15 * math.sin(self.t * 8))
                RoundedRectangle(pos=(bx - 5 * s, by - 5 * s), size=(w + 10 * s, h + 10 * s), radius=[12 * s])
            Color(*((.98, .8, .25) if sel else (.72, .6, .3)))
            RoundedRectangle(pos=(bx - 2.5 * s, by - 2.5 * s), size=(w + 5 * s, h + 5 * s), radius=[10 * s])
            top, bot = FUNDO[key]
            Color(*bot)
            RoundedRectangle(pos=(bx, by), size=(w, h), radius=[8 * s])
            Color(*top, .85)
            RoundedRectangle(pos=(bx, by + h * .45), size=(w, h * .55), radius=[8 * s])
            Color(1, 1, 1, .12)
            Ellipse(pos=(bx + w * .12, by + h * .22), size=(w * .76, h * .6))
            self.sprite(key, bx + w / 2, by + h * .56, 66 * s)
            Color(0, 0, 0, .65)
            RoundedRectangle(pos=(bx + 3 * s, by + 3 * s), size=(w - 6 * s, 16 * s), radius=[6 * s])
            self.txt(cd['nome'], bx + w / 2, by + 11 * s, 9.5)
            self.sprite('gota', bx + 15 * s, by + h - 14 * s, 30 * s)
            self.txt(str(cd['custo']), bx + 15 * s, by + h - 15 * s, 13)
            if not ok:
                Color(0, 0, 0, .5)
                RoundedRectangle(pos=(bx - 2.5 * s, by - 2.5 * s), size=(w + 5 * s, h + 5 * s), radius=[10 * s])
        # próxima carta
        if self.fila and self.estado == 'jogo':
            Color(0, 0, 0, .45)
            RoundedRectangle(pos=(self.hx(6), self.hy(AY + 6)), size=(38 * s, 44 * s), radius=[7 * s])
            self.sprite(self.fila[0], self.hx(25), self.hy(AY + 30), 32 * s, cor=(1, 1, 1, .9))
            self.txt('PRÓX.', self.hx(25), self.hy(AY + 11), 8)
        # elixir
        bx, bw = self.hx(32), 318 * s
        Color(0, 0, 0, .7)
        RoundedRectangle(pos=(bx - 1.5, self.hy(4) - 1.5), size=(bw + 3, 18 * s + 3), radius=[9 * s])
        cheio = self.elixir[0] / 10
        Color(.16, .08, .25, 1)
        RoundedRectangle(pos=(bx, self.hy(5)), size=(bw, 16 * s), radius=[8 * s])
        if cheio > 0:
            Color(*((1, .3, .3) if self.nope > 0 else (.8, .25, 1)))
            RoundedRectangle(pos=(bx, self.hy(5)), size=(max(14 * s, bw * cheio), 16 * s), radius=[8 * s])
            Color(1, .8, 1, .35)
            Rectangle(pos=(bx + 6 * s, self.hy(5) + 10 * s), size=(max(0, bw * cheio - 12 * s), 4 * s))
        Color(0, 0, 0, .45)
        for k in range(1, 10):
            Rectangle(pos=(bx + bw * k / 10, self.hy(5)), size=(1.5, 16 * s))
        self.sprite('gota', self.hx(17), self.hy(13), 30 * s)
        self.txt('%d' % int(self.elixir[0]), self.hx(17), self.hy(12), 12)

        if self.banner:
            txt, cor, ttl, tot = self.banner
            k = ttl / tot
            esc = 1 + .5 * max(0, k - .8) * 5
            a = min(1, ttl * 3, (tot - ttl) * 6 + .2)
            Color(0, 0, 0, .35 * a)
            Rectangle(pos=(self.hx(0), self.hy(AY + 300)), size=(360 * s, 46 * s))
            self.txt(txt, self.hx(180), self.hy(AY + 323), 30 * esc, (cor[0], cor[1], cor[2], a))

    def draw_fim(self):
        s = self.s
        a = min(1, self.fim_t * 2)
        Color(0, 0, 0, .6 * a)
        Rectangle(pos=self.pos, size=self.size)
        cor = {'VITÓRIA!': (1, .88, .25), 'DERROTA': (1, .35, .35)}.get(self.resultado, (1, 1, 1))
        sl = min(1, self.fim_t * 3)
        Color(*[v * .55 for v in cor], .95 * a)
        RoundedRectangle(pos=(self.hx(20), self.hy(AY + 330)), size=(320 * s * sl, 90 * s), radius=[14 * s])
        Color(*cor, a)
        Line(rounded_rectangle=(self.hx(20), self.hy(AY + 330), 320 * s * sl, 90 * s, 14 * s), width=2.5 * s)
        if sl >= 1:
            self.txt(self.resultado, self.hx(180), self.hy(AY + 375), 44, (cor[0], cor[1], cor[2], 1))
            ganhas = self.coroas(0)
            for i in range(3):
                self.sprite('coroa' if i < ganhas else 'coroa_off', self.hx(120 + i * 60), self.hy(AY + 290), 50 * s,
                            cor=(1, 1, 1, 1 if i < ganhas else .5))
            self.txt('Você %d  x  %d Inimigo' % (ganhas, self.coroas(1)), self.hx(180), self.hy(AY + 245), 15)
            if self.fim_t > 1.2 and int(self.t * 2) % 2 == 0:
                self.txt('Toque para jogar de novo', self.hx(180), self.hy(AY + 190), 17)

    def draw_menu(self):
        s = self.s
        self.sprite('menu_bg', self.hx(180), self.hy(VH / 2), VH * s * 720 / 1280., VH * s)
        pulso = 1 + .04 * math.sin(self.t * 3)
        self.sprite('logo', self.hx(180), self.hy(560) + math.sin(self.t * 2) * 4 * s, 250 * s * pulso)
        self.txt('ARENA REAL', self.hx(180), self.hy(420), 38, (1, .88, .25, 1))
        self.txt('Derrube a torre do Rei inimigo!', self.hx(180), self.hy(385), 13, (1, 1, 1, 1))
        # botão jogar
        k = 1 + .05 * math.sin(self.t * 4)
        w, h = 210 * s * k, 54 * s * k
        Color(.45, .28, .05, 1)
        RoundedRectangle(pos=(self.hx(180) - w / 2, self.hy(270) - h / 2 - 4 * s), size=(w, h), radius=[16 * s])
        Color(1, .78, .2, 1)
        RoundedRectangle(pos=(self.hx(180) - w / 2, self.hy(270) - h / 2), size=(w, h), radius=[16 * s])
        Color(1, .92, .5, .6)
        RoundedRectangle(pos=(self.hx(180) - w / 2 + 6 * s, self.hy(270) + h * .12), size=(w - 12 * s, h * .3), radius=[10 * s])
        self.txt('JOGAR', self.hx(180), self.hy(270), 28, (.3, .15, .02, 1), sombra=False)
        self.txt('1) toque numa carta   2) toque na sua metade da arena', self.hx(180), self.hy(215), 9.5, (1, 1, 1, .9))
        self.txt('Dica: dá para arrastar a carta até a arena!', self.hx(180), self.hy(198), 9.5, (1, .9, .6, .9))
        # desfile de personagens
        for i, key in enumerate(('cavaleiro', 'arqueiras', 'gigante', 'goblins', 'mago', 'barbaros', 'esqueletos')):
            x = 30 + i * 50
            bob = abs(math.sin(self.t * 4 + i)) * 6 * s
            tam = (84 if key == 'gigante' else 62) * s
            self.sprite(key, self.hx(x), self.hy(78) + bob, tam, flip=i % 2 == 1)
        on = self.sons.on
        Color(*((.15, .55, .25, .9) if on else (.6, .15, .15, .9)))
        RoundedRectangle(pos=(self.hx(296), self.hy(722)), size=(56 * s, 22 * s), radius=[11 * s])
        self.txt('SOM' if on else 'MUDO', self.hx(324), self.hy(733), 10)


class ArenaRealApp(App):
    title = 'Arena Real'

    def build(self):
        if platform not in ('android', 'ios'):
            from kivy.core.window import Window
            Window.size = (405, 760)
        self.jogo = Jogo()
        Clock.schedule_once(lambda dt: self.jogo.sons.iniciar_musica(), .5)
        return self.jogo

    def on_pause(self):
        self.jogo.sons.parar_musica()
        return True

    def on_resume(self):
        self.jogo.sons.iniciar_musica()


if __name__ == '__main__':
    ArenaRealApp().run()
