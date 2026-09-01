#!/usr/bin/env python3
"""Header animado del README: sesion de terminal que teclea comandos reales.

SMIL + CSS embebido -> funciona dentro de un <img> en GitHub y se adapta
al tema claro/oscuro del visitante.

Para cambiar los comandos, edita SCRIPT: cada entrada es (comando, salida).
Las posiciones verticales y el timeline se recalculan solos.

Abajo patrulla el monito de Claude Code, calcado pixel a pixel del sticker
original (rejilla de 11x8). Su recorrido va aparte del ciclo de la terminal.

    python3 assets/gen_header.py
"""
import os

W = 780
PROMPT = "jorge@github:~$ "
NAME = "Jorge Martín"

CHAR_W = 9.6          # ancho de caracter mono a 16px (comandos)
CHAR_W_SM = 8.4       # a 14px (salidas)
X0 = 40

SCRIPT = [
    ("whoami", NAME),
    ("id -Gn", "sysadmin  developer  security"),
    ("systemctl status jorge", "● active (running) since 2007"),
    ("ls ~/proyectos", "rustblood  chicks  yohohielo  bao-textil"),
    ("pwd", "/home/jorge/cualtos/icom"),
    ("sudo make coffee", "error: recurso no disponible"),
]

ERRORS = {"sudo make coffee"}     # su salida va en rojo
HIGHLIGHT = {"whoami"}            # su salida es el nombre: negrita y con glitch

# --- reparto vertical -----------------------------------------------------
FIRST_Y, OUT_DROP, OUT_GAP = 46, 26, 60

LAYOUT, _y = [], FIRST_Y
for _cmd, _out in SCRIPT:
    LAYOUT.append((_y, _y + OUT_DROP))
    _y += OUT_GAP

# --- el monito: sprite 11x8 calcado del pixel art, patrulla el borde -----
BOT_PX = 4                # lado de cada pixel del sprite
BOT_STEP = 0.30           # segundos por zancada (cambio de frame)
BOT_LOOP = 24.0           # segundos en ir de un extremo al otro y volver

# '#' cuerpo, 'o' ojo, '.' vacio. Los dos frames alternan pares de patas.
BOT_BODY = (
    ".#########.",
    ".#########.",
    "##o#####o##",
    "###########",
    ".#########.",
    ".#########.",
    ".#.#...#.#.",
)

BOT_FRAMES = (
    BOT_BODY + ("...#.....#.",),   # levanta las patas 1 y 3
    BOT_BODY + (".#.....#...",),   # levanta las patas 2 y 4
)

BOT_W = len(BOT_FRAMES[0][0]) * BOT_PX
BOT_H = len(BOT_FRAMES[0]) * BOT_PX

H = LAYOUT[-1][1] + 26 + BOT_H + 10
BOT_Y = H - BOT_H - 6

TYPE_PER_CHAR = 0.07
HOLD_AFTER_CMD = 0.28
HOLD_END = 2.6


def build_timeline():
    """Eventos con sus tiempos y la duracion total del ciclo."""
    t = 0.5
    steps = []
    for (cmd, out), (y_cmd, y_out) in zip(SCRIPT, LAYOUT):
        start = t
        end = start + len(cmd) * TYPE_PER_CHAR
        t = end + HOLD_AFTER_CMD
        reveal = t
        t += 0.4
        steps.append(dict(cmd=cmd, out=out, y_cmd=y_cmd, y_out=y_out,
                          start=start, end=end, reveal=reveal,
                          err=cmd in ERRORS, hi=cmd in HIGHLIGHT))
    return steps, t + HOLD_END


STEPS, LOOP = build_timeline()
NAME_AT = STEPS[0]["reveal"]
FADE = LOOP - 0.25


def pct(t):
    return max(0.0, min(1.0, t / LOOP))


def anim(attr, pairs, calc="discrete"):
    pairs = sorted(pairs)
    vals = ";".join(str(v) for _, v in pairs)
    times = ";".join(f"{pct(t):.4f}" for t, _ in pairs)
    return (f'<animate attributeName="{attr}" dur="{LOOP}s" repeatCount="indefinite" '
            f'calcMode="{calc}" values="{vals}" keyTimes="{times}"/>')


def type_pairs(step):
    """Ancho del clip creciendo caracter por caracter."""
    pairs = [(0.0, 0)]
    for i in range(len(step["cmd"]) + 1):
        pairs.append((round(step["start"] + i * TYPE_PER_CHAR, 3),
                      round(i * CHAR_W, 1)))
    pairs.append((FADE, round(len(step["cmd"]) * CHAR_W, 1)))
    pairs.append((LOOP - 0.1, 0))
    return pairs


def fade_in(at):
    return [(0.0, 0), (at, 1), (FADE, 1), (LOOP - 0.1, 0)]


# --- cursor: sigue a la linea que se esta escribiendo ----------------------
base_x = X0 + len(PROMPT) * CHAR_W
cur_x, cur_y = [(0.0, base_x)], [(0.0, STEPS[0]["y_cmd"] - 13)]
for step in STEPS:
    cur_y.append((round(step["start"] - 0.15, 3), step["y_cmd"] - 13))
    for i in range(len(step["cmd"]) + 1):
        cur_x.append((round(step["start"] + i * TYPE_PER_CHAR, 3),
                      round(base_x + i * CHAR_W, 1)))

blink, t, on = [], 0.0, True
while t < LOOP:
    blink.append((round(t, 3), 1 if on else 0))
    on = not on
    t += 0.5

# --- glitch del nombre (sutil, va al tamano de la terminal) ---------------
GLITCH_AT = [NAME_AT, NAME_AT + 0.09, NAME_AT + 0.18,
             NAME_AT + 2.6, NAME_AT + 2.68, LOOP - 1.6, LOOP - 1.52]


def glitch_opacity():
    pairs = [(0.0, 0)]
    for g in GLITCH_AT:
        pairs.append((round(g, 3), 0.8))
        pairs.append((round(g + 0.06, 3), 0))
    return pairs


def glitch_shift(sign):
    pairs = [(0.0, 0)]
    for k, g in enumerate(GLITCH_AT):
        pairs.append((round(g, 3), sign * (1 if k % 2 == 0 else 2)))
        pairs.append((round(g + 0.06, 3), 0))
    return pairs



def bot_frame(cells):
    """Un frame del monito: '#' es cuerpo, 'o' es ojo. Une pixeles contiguos."""
    out = []
    for row, line in enumerate(cells):
        col = 0
        while col < len(line):
            ch = line[col]
            run = 0
            while col + run < len(line) and line[col + run] == ch:
                run += 1
            if ch in "#o":
                cls = ' class="bot-eye"' if ch == "o" else ""
                out.append(f'<rect{cls} x="{col * BOT_PX}" y="{row * BOT_PX}" '
                           f'width="{run * BOT_PX}" height="{BOT_PX}"/>')
            col += run
    return "".join(out)


def bot_svg():
    """Va y viene de lado a lado del header, dando zancadas."""
    walk = (f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{BOT_LOOP}s" repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="0;0.5;1" '
            f'values="{-BOT_W - 10},{BOT_Y};{W + 10},{BOT_Y};{-BOT_W - 10},{BOT_Y}"/>')
    bob = (f'<animateTransform attributeName="transform" type="translate" '
           f'dur="{BOT_STEP * 2}s" repeatCount="indefinite" calcMode="discrete" '
           f'values="0,0;0,-{BOT_PX}"/>')
    frames = []
    for n, cells in enumerate(BOT_FRAMES):
        flip = "1;0" if n == 0 else "0;1"
        frames.append(
            f'<g class="bot">{bot_frame(cells)}'
            f'<animate attributeName="opacity" dur="{BOT_STEP * 2}s" '
            f'repeatCount="indefinite" calcMode="discrete" values="{flip}"/></g>')
    return f'<g>{walk}<g>{bob}{"".join(frames)}</g></g>'


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}" role="img" aria-label="{NAME} — Sysadmin y Developer">',
    '<style>',
    '.mono { font-family: "Fira Code","JetBrains Mono","SF Mono",Consolas,monospace; }',
    '.prompt { fill: #57606a; }',
    '.cmd    { fill: #0066FF; }',
    '.out    { fill: #1a7f37; }',
    '.err    { fill: #cf222e; }',
    '.name   { fill: #1f2328; }',
    '.bot     { fill: #D97757; }',
    '.bot-eye { fill: #1f2328; }',
    '@media (prefers-color-scheme: dark) {',
    '  .prompt { fill: #8b949e; }',
    '  .out    { fill: #3fb950; }',
    '  .err    { fill: #f85149; }',
    '  .name   { fill: #e6edf3; }',
    '  .bot     { fill: #E8916F; }',
    '  .bot-eye { fill: #0d1117; }',
    '}',
    '</style>',
    '<defs>',
    '<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">',
    '<stop offset="0%" stop-color="#0066FF" stop-opacity="0"/>',
    '<stop offset="55%" stop-color="#0066FF" stop-opacity="1"/>',
    '<stop offset="100%" stop-color="#0066FF" stop-opacity="0"/>',
    '</linearGradient>',
]

for n, step in enumerate(STEPS):
    parts.append(f'<clipPath id="clip{n}">')
    parts.append(f'<rect x="{base_x}" y="{step["y_cmd"] - 20}" height="26" width="0">'
                 + anim("width", type_pairs(step)) + '</rect>')
    parts.append('</clipPath>')

parts.append('</defs>')

for n, step in enumerate(STEPS):
    parts.append(f'<text class="mono prompt" x="{X0}" y="{step["y_cmd"]}" '
                 f'font-size="16">{PROMPT}</text>')
    parts.append(f'<g clip-path="url(#clip{n})">')
    parts.append(f'<text class="mono cmd" x="{base_x}" y="{step["y_cmd"]}" '
                 f'font-size="16">{step["cmd"]}</text>')
    parts.append('</g>')

    if step["hi"]:
        # el nombre: mismo tamano que el resto, en negrita y con glitch encima
        for color, sign in (("#00D4FF", -1), ("#FF3B6B", 1)):
            parts.append(
                f'<text class="mono" x="{X0}" y="{step["y_out"]}" font-size="14" '
                f'font-weight="700" fill="{color}" opacity="0">{step["out"]}'
                + anim("opacity", glitch_opacity())
                + anim("dx", glitch_shift(sign)) + '</text>')
        parts.append(
            f'<text class="mono name" x="{X0}" y="{step["y_out"]}" font-size="14" '
            f'font-weight="700" opacity="0">{step["out"]}'
            + anim("opacity", fade_in(step["reveal"])) + '</text>')
        bar_w = round(len(step["out"]) * CHAR_W_SM, 1)
        parts.append(
            f'<rect x="{X0}" y="{step["y_out"] + 7}" height="2" width="0" '
            f'fill="url(#sweep)">'
            + anim("width", [(0.0, 0), (step["reveal"], 0),
                             (step["reveal"] + 0.4, bar_w), (FADE, bar_w),
                             (LOOP - 0.1, 0)], calc="linear") + '</rect>')
    else:
        cls = "err" if step["err"] else "out"
        parts.append(
            f'<text class="mono {cls}" x="{X0}" y="{step["y_out"]}" font-size="14" '
            f'opacity="0">{step["out"]}'
            + anim("opacity", fade_in(step["reveal"])) + '</text>')

parts.append(f'<rect width="9" height="18" fill="#0066FF" x="{base_x}" '
             f'y="{STEPS[0]["y_cmd"] - 13}">'
             + anim("x", cur_x) + anim("y", cur_y) + anim("opacity", blink) + '</rect>')
parts.append(bot_svg())
parts.append('</svg>')

svg = "\n".join(parts)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "header.svg")
with open(out, "w") as fh:
    fh.write(svg)
print(f"{out}  ({len(svg) / 1024:.1f} KB, {W}x{H}, ciclo de {LOOP:.1f}s)")
