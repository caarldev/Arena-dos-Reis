"""Arena Real - jogo de batalha de cartas em tempo real (Python + Kivy)."""
import math
import os
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.utils import platform

VW, VH, AY = 360, 760, 120   # tela virtual; arena começa em y=120
RIO = 320                    # y do rio dentro da arena (640 de altura)
PONTES = (90, 270)
DURACAO = 180
AGGRO = 100

CARTAS = {
    'cavaleiro': dict(nome='Cavaleiro', custo=3, hp=700, dano=85, alc=16, vel=42, raio=11, n=1, cor=(.35, .55, 1)),
    'arqueiras': dict(nome='Arqueiras', custo=3, hp=180, dano=38, alc=95, vel=48, raio=8, n=2, cor=(1, .5, .8)),
    'gigante': dict(nome='Gigante', custo=5, hp=1900, dano=110, alc=18, vel=26, raio=16, n=1, cor=(.9, .7, .2), torre=True),
    'goblins': dict(nome='Goblins', custo=2, hp=120, dano=45, alc=14, vel=75, raio=7, n=3, cor=(.3, .9, .3)),
    'mago': dict(nome='Mago', custo=4, hp=320, dano=130, alc=80, vel=36, raio=10, n=1, cor=(1, .4, .2)),
    'barbaros': dict(nome='Bárbaros', custo=4, hp=450, dano=65, alc=14, vel=45, raio=9, n=2, cor=(1, .8, .4)),
    'esqueletos': dict(nome='Esqueletos', custo=1, hp=60, dano=30, alc=12, vel=70, raio=6, n=4, cor=(.9, .9, .9)),
    'fogo': dict(nome='Bola de Fogo', custo=4, feitico=True, dano=260, raio_fx=55, cor=(1, .3, .1)),
}


class Ent:
    def __init__(self, x, y, team, hp, raio):
        self.x, self.y, self.team = x, y, team
        self.hp = self.maxhp = hp
        self.raio = raio


class Unidade(Ent):
    def __init__(self, c, x, y, team):
        Ent.__init__(self, x, y, team, c['hp'], c['raio'])
        self.dano, self.alc, self.vel = c['dano'], c['alc'], c['vel']
        self.cor, self.torre, self.nome = c['cor'], c.get('torre', False), c['nome']
        self.cd = 0.0


class Torre(Ent):
    def __init__(self, x, y, team, rei):
        Ent.__init__(self, x, y, team, 2400 if rei else 1400, 24 if rei else 19)
        self.rei = rei
        self.alc = 120 if rei else 110
        self.dano = 70 if rei else 55
        self.cd = 0.0


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


class Jogo(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.cache = {}
        self.s, self.ox, self.oy = 1, 0, 0
        base = os.path.dirname(os.path.abspath(__file__))
        self.logo = CoreImage(os.path.join(base, 'assets', 'logo.png')).texture
        self.estado = 'menu'
        self.units, self.fx, self.torres = [], [], []
        self.mao, self.fila, self.sel = [], [], None
        self.elixir, self.tempo, self.ia_cd, self.resultado = [5, 5], DURACAO, 3, ''
        Clock.schedule_interval(self.update, 1 / 30.)

    # ------------------------------------------------------------ lógica
    def novo(self):
        self.estado = 'jogo'
        self.tempo = DURACAO
        self.elixir = [5.0, 5.0]
        self.ia_cd = 4.0
        ordem = list(CARTAS)
        random.shuffle(ordem)
        self.mao, self.fila, self.sel = ordem[:4], ordem[4:], None
        self.units, self.fx, self.resultado = [], [], ''
        self.torres = [
            Torre(90, 120, 0, False), Torre(270, 120, 0, False), Torre(180, 60, 0, True),
            Torre(90, 520, 1, False), Torre(270, 520, 1, False), Torre(180, 580, 1, True)]

    def jogar(self, team, key, x, y):
        c = CARTAS[key]
        self.elixir[team] -= c['custo']
        if c.get('feitico'):
            for e in self.units + self.torres:
                if e.team != team and e.hp > 0 and math.hypot(e.x - x, e.y - y) <= c['raio_fx'] + e.raio:
                    e.hp -= c['dano'] if isinstance(e, Unidade) else c['dano'] * 0.4
            self.fx.append(dict(t='boom', x=x, y=y, ttl=.35, r=c['raio_fx']))
        else:
            for i in range(c['n']):
                off = (i - (c['n'] - 1) / 2.) * 16
                self.units.append(Unidade(c, x + off, y + random.uniform(-4, 4), team))

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
        if self.estado == 'jogo':
            self.passo(dt)
        for f in self.fx:
            f['ttl'] -= dt
        self.fx = [f for f in self.fx if f['ttl'] > 0]
        self.draw()

    def passo(self, dt):
        self.tempo -= dt
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
            u.cd -= dt
            a = self.alvo(u)
            if not a:
                continue
            d = dist(u, a)
            if d - a.raio <= u.alc:
                if u.cd <= 0:
                    a.hp -= u.dano
                    u.cd = 1.0
                    self.fx.append(dict(t='linha', x1=u.x, y1=u.y, x2=a.x, y2=a.y, ttl=.12, team=u.team))
            else:
                tx, ty = a.x, a.y
                if (u.y > RIO) != (a.y > RIO):
                    tx = min(PONTES, key=lambda b: abs(b - u.x))
                    ty = RIO + (12 if a.y > RIO else -12)
                dx, dy = tx - u.x, ty - u.y
                dd = math.hypot(dx, dy) or 1
                u.x += dx / dd * u.vel * dt
                u.y += dy / dd * u.vel * dt
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
            if t.hp <= 0:
                continue
            t.cd -= dt
            if t.cd > 0:
                continue
            alvos = [e for e in vivos if e.team != t.team and e.hp > 0 and dist(t, e) <= t.alc + e.raio]
            if alvos:
                a = min(alvos, key=lambda e: dist(t, e))
                a.hp -= t.dano
                t.cd = .8
                self.fx.append(dict(t='linha', x1=t.x, y1=t.y, x2=a.x, y2=a.y, ttl=.12, team=t.team))
        self.units = [u for u in self.units if u.hp > 0]

        # fim de jogo
        rei0 = next(t for t in self.torres if t.team == 0 and t.rei)
        rei1 = next(t for t in self.torres if t.team == 1 and t.rei)
        if rei1.hp <= 0 or rei0.hp <= 0 or self.tempo <= 0:
            a, b = self.coroas(0), self.coroas(1)
            self.resultado = 'VITÓRIA!' if a > b else 'DERROTA' if b > a else 'EMPATE'
            self.estado = 'fim'

    # ------------------------------------------------------------ entrada
    def lay(self):
        self.s = min(self.width / VW, self.height / VH) or 1
        self.ox = self.x + (self.width - VW * self.s) / 2
        self.oy = self.y + (self.height - VH * self.s) / 2

    def on_touch_down(self, touch):
        self.lay()
        if self.estado in ('menu', 'fim'):
            self.novo()
            return True
        vx = (touch.x - self.ox) / self.s
        vy = (touch.y - self.oy) / self.s
        if vy < AY:
            for i in range(4):
                x0 = 11 + i * 86
                if x0 <= vx <= x0 + 80 and 28 <= vy <= 112:
                    self.sel = None if self.sel == i else i
            return True
        if self.sel is not None:
            key = self.mao[self.sel]
            c = CARTAS[key]
            ax, ay = vx, vy - AY
            if self.elixir[0] >= c['custo'] and 0 <= ax <= 360 and (c.get('feitico') or 8 < ay < RIO - 12):
                self.jogar(0, key, ax, ay)
                self.fila.append(key)
                self.mao[self.sel] = self.fila.pop(0)
                self.sel = None
        return True

    # ------------------------------------------------------------ desenho
    def X(self, x):
        return self.ox + x * self.s

    def Y(self, y):
        return self.oy + (y + AY) * self.s

    def txt(self, texto, x, y, size, cor=(1, 1, 1, 1)):
        px = max(8, int(size * self.s))
        key = (texto, px)
        t = self.cache.get(key)
        if t is None:
            if len(self.cache) > 400:
                self.cache.clear()
            lab = CoreLabel(text=texto, font_size=px, bold=True)
            lab.refresh()
            t = self.cache[key] = lab.texture
        Color(*cor)
        Rectangle(texture=t, pos=(x - t.width / 2, y - t.height / 2), size=t.size)

    def barra(self, x, y, w, h, frac, cor):
        Color(0, 0, 0, .6)
        Rectangle(pos=(x - w / 2 - 1, y), size=(w + 2, h + 2))
        Color(*cor)
        Rectangle(pos=(x - w / 2, y + 1), size=(w * max(0, frac), h))

    def draw(self):
        self.lay()
        s = self.s
        c = self.canvas
        c.clear()
        with c:
            Color(.05, .07, .13)
            Rectangle(pos=self.pos, size=self.size)
            if self.estado == 'menu':
                self.draw_menu()
                return
            # arena
            Color(.33, .62, .30)
            Rectangle(pos=(self.X(0), self.Y(0)), size=(360 * s, 640 * s))
            Color(.30, .57, .27)
            Rectangle(pos=(self.X(0), self.Y(RIO)), size=(360 * s, 320 * s))
            Color(.25, .5, .9)
            Rectangle(pos=(self.X(0), self.Y(RIO - 18)), size=(360 * s, 36 * s))
            Color(.62, .46, .26)
            for b in PONTES:
                Rectangle(pos=(self.X(b - 25), self.Y(RIO - 22)), size=(50 * s, 44 * s))
            if self.sel is not None and not CARTAS[self.mao[self.sel]].get('feitico'):
                Color(1, 1, 1, .12)
                Rectangle(pos=(self.X(0), self.Y(0)), size=(360 * s, (RIO - 12) * s))

            # torres
            for t in self.torres:
                r = t.raio * s
                if t.hp <= 0:
                    Color(.3, .3, .3)
                    Ellipse(pos=(self.X(t.x) - r * .6, self.Y(t.y) - r * .6), size=(r * 1.2, r * 1.2))
                    continue
                Color(*((.2, .4, .95) if t.team == 0 else (.95, .25, .25)))
                RoundedRectangle(pos=(self.X(t.x) - r, self.Y(t.y) - r), size=(2 * r, 2 * r), radius=[6 * s])
                if t.rei:
                    self.txt('R', self.X(t.x), self.Y(t.y), 16)
                self.barra(self.X(t.x), self.Y(t.y) + r + 3 * s, 40 * s, 4 * s, t.hp / t.maxhp,
                           (.3, .9, .3) if t.team == 0 else (1, .3, .3))
                self.txt(str(int(t.hp)), self.X(t.x), self.Y(t.y) + r + 14 * s, 9)

            # unidades
            for u in self.units:
                r = u.raio * s
                Color(*((.1, .3, 1) if u.team == 0 else (1, .15, .15)))
                Ellipse(pos=(self.X(u.x) - r - 2, self.Y(u.y) - r - 2), size=(2 * r + 4, 2 * r + 4))
                Color(*u.cor)
                Ellipse(pos=(self.X(u.x) - r, self.Y(u.y) - r), size=(2 * r, 2 * r))
                self.txt(u.nome[0], self.X(u.x), self.Y(u.y), max(8, u.raio))
                if u.hp < u.maxhp:
                    self.barra(self.X(u.x), self.Y(u.y) + r + 3, 22 * s, 3 * s, u.hp / u.maxhp, (.3, 1, .3))

            # efeitos
            for f in self.fx:
                if f['t'] == 'linha':
                    Color(*((.5, .8, 1, 1) if f['team'] == 0 else (1, .6, .4, 1)))
                    Line(points=[self.X(f['x1']), self.Y(f['y1']), self.X(f['x2']), self.Y(f['y2'])], width=2)
                else:
                    Color(1, .5, .1, .6)
                    rr = f['r'] * s
                    Ellipse(pos=(self.X(f['x']) - rr, self.Y(f['y']) - rr), size=(2 * rr, 2 * rr))

            # HUD topo
            Color(0, 0, 0, .55)
            Rectangle(pos=(self.X(0), self.Y(614)), size=(360 * s, 26 * s))
            m, sg = divmod(max(0, int(self.tempo)), 60)
            self.txt('%d:%02d' % (m, sg), self.X(180), self.Y(627), 16,
                     (1, .9, .3, 1) if self.tempo <= 60 else (1, 1, 1, 1))
            self.txt('Você %d' % self.coroas(0), self.X(55), self.Y(627), 13, (.5, .7, 1, 1))
            self.txt('%d Inimigo' % self.coroas(1), self.X(305), self.Y(627), 13, (1, .5, .5, 1))

            # painel de cartas
            Color(.1, .09, .16)
            Rectangle(pos=(self.X(0), self.oy), size=(360 * s, AY * s))
            for i, key in enumerate(self.mao):
                cd = CARTAS[key]
                x0 = 11 + i * 86
                ok = self.elixir[0] >= cd['custo']
                Color(1, .9, .3) if self.sel == i else Color(.25, .22, .35)
                RoundedRectangle(pos=(self.ox + (x0 - 3) * s, self.oy + 25 * s), size=(86 * s, 90 * s), radius=[8 * s])
                r_, g_, b_ = cd['cor']
                Color(r_, g_, b_, 1 if ok else .35)
                RoundedRectangle(pos=(self.ox + x0 * s, self.oy + 28 * s), size=(80 * s, 84 * s), radius=[8 * s])
                self.txt(cd['nome'], self.ox + (x0 + 40) * s, self.oy + 46 * s, 10, (0, 0, 0, 1))
                Color(.7, .2, .9)
                Ellipse(pos=(self.ox + (x0 + 24) * s, self.oy + 62 * s), size=(32 * s, 32 * s))
                self.txt(str(cd['custo']), self.ox + (x0 + 40) * s, self.oy + 78 * s, 18)
            # elixir
            Color(0, 0, 0, .6)
            Rectangle(pos=(self.ox + 10 * s, self.oy + 5 * s), size=(340 * s, 16 * s))
            Color(.8, .25, 1)
            Rectangle(pos=(self.ox + 10 * s, self.oy + 5 * s), size=(340 * s * self.elixir[0] / 10, 16 * s))
            Color(0, 0, 0, .5)
            for k in range(1, 10):
                Rectangle(pos=(self.ox + (10 + 34 * k) * s, self.oy + 5 * s), size=(1.5, 16 * s))
            self.txt('%d' % int(self.elixir[0]), self.ox + 180 * s, self.oy + 13 * s, 12)

            if self.estado == 'fim':
                Color(0, 0, 0, .65)
                Rectangle(pos=self.pos, size=self.size)
                cor = {'VITÓRIA!': (1, .9, .2, 1), 'DERROTA': (1, .3, .3, 1)}.get(self.resultado, (1, 1, 1, 1))
                self.txt(self.resultado, self.X(180), self.Y(380), 44, cor)
                self.txt('Toque para jogar de novo', self.X(180), self.Y(300), 18)

    def draw_menu(self):
        s = self.s
        Color(1, 1, 1)
        Rectangle(texture=self.logo, pos=(self.X(180) - 150 * s, self.oy + 380 * s), size=(300 * s, 300 * s))
        self.txt('ARENA REAL', self.X(180), self.oy + 340 * s, 34, (1, .85, .2, 1))
        self.txt('Derrube a torre do Rei inimigo!', self.X(180), self.oy + 290 * s, 14)
        self.txt('TOQUE PARA JOGAR', self.X(180), self.oy + 200 * s, 22)
        self.txt('1) toque numa carta  2) toque na sua metade da arena', self.X(180), self.oy + 140 * s, 10,
                 (.8, .8, .9, 1))


class ArenaRealApp(App):
    title = 'Arena Real'

    def build(self):
        if platform not in ('android', 'ios'):
            from kivy.core.window import Window
            Window.size = (405, 760)
        return Jogo()


if __name__ == '__main__':
    ArenaRealApp().run()
