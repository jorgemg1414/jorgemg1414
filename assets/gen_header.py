#!/usr/bin/env python3
"""Header animado del README: sesion de terminal que teclea comandos reales.

SMIL + CSS embebido -> funciona dentro de un <img> en GitHub y se adapta
al tema claro/oscuro del visitante.

Para cambiar los comandos, edita SCRIPT: cada entrada es
(comando, salida, y_del_prompt, y_de_la_salida). El timeline se recalcula solo.
"""
import os

W = 780
PROMPT = "jorge@github:~$ "
NAME = "Jorge Martín"

CHAR_W = 9.6          # ancho de caracter mono a 16px
X0 = 40

# (comando, salida). salida None = la imprime el nombre grande.
# El orden manda; las posiciones verticales se calculan solas.
SCRIPT = [
    ("whoami", None),
    ("id -Gn", "sysadmin  developer  security"),
    ("systemctl status jorge", "● active (running) since 2007"),
    ("ls ~/proyectos", "rustblood  yohohielo  bao-textil"),
    ("pwd", "/home/jorge/cualtos/icom"),
    ("sudo make coffee", "error: recurso no disponible"),
]

# comandos cuya salida es un error -> se pinta en rojo, no en verde
ERRORS = {"sudo make coffee"}

# --- reparto vertical -----------------------------------------------------
FIRST_Y = 46
NAME_DROP, BAR_DROP, NAME_GAP = 70, 90, 132   # separacion cuando toca el nombre
OUT_DROP, OUT_GAP = 28, 62                    # separacion de una salida normal

LAYOUT, _y = [], FIRST_Y
for _cmd, _out in SCRIPT:
    if _out is None:
        LAYOUT.append((_y, _y + NAME_DROP))
        _y += NAME_GAP
    else:
        LAYOUT.append((_y, _y + OUT_DROP))
        _y += OUT_GAP
H = LAYOUT[-1][1] + 28
NAME_Y = LAYOUT[0][1]
BAR_Y = FIRST_Y + BAR_DROP

TYPE_PER_CHAR = 0.07
HOLD_AFTER_CMD = 0.3
HOLD_END = 2.6


def build_timeline():
    """Devuelve los eventos con sus tiempos y la duracion total del ciclo."""
    t = 0.5
    steps = []
    for (cmd, out), (y_cmd, y_out) in zip(SCRIPT, LAYOUT):
        start = t
        end = start + len(cmd) * TYPE_PER_CHAR
        t = end + HOLD_AFTER_CMD
        reveal = t
        t += 0.55 if out is None else 0.35
        steps.append(dict(cmd=cmd, out=out, y_cmd=y_cmd, y_out=y_out,
                          start=start, end=end, reveal=reveal,
                          err=cmd in ERRORS))
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


def type_pairs(step, char_w):
    """Ancho del clip creciendo caracter por caracter."""
    pairs = [(0.0, 0)]
    for i in range(len(step["cmd"]) + 1):
        pairs.append((round(step["start"] + i * TYPE_PER_CHAR, 3),
                      round(i * char_w, 1)))
    pairs.append((FADE, round(len(step["cmd"]) * char_w, 1)))
    pairs.append((LOOP - 0.1, 0))
    return pairs


# --- cursor: sigue a la linea que se esta escribiendo ----------------------
cur_x, cur_y = [], []
base_x = X0 + len(PROMPT) * CHAR_W
for step in STEPS:
    cur_y.append((round(step["start"] - 0.15, 3), step["y_cmd"] - 13))
    for i in range(len(step["cmd"]) + 1):
        cur_x.append((round(step["start"] + i * TYPE_PER_CHAR, 3),
                      round(base_x + i * CHAR_W, 1)))
cur_x.insert(0, (0.0, base_x))
cur_y.insert(0, (0.0, STEPS[0]["y_cmd"] - 13))

blink, t, on = [], 0.0, True
while t < LOOP:
    blink.append((round(t, 3), 1 if on else 0))
    on = not on
    t += 0.5

# --- glitch del nombre ----------------------------------------------------
GLITCH_AT = [NAME_AT, NAME_AT + 0.09, NAME_AT + 0.18,
             NAME_AT + 2.4, NAME_AT + 2.48, LOOP - 1.6, LOOP - 1.52]


def glitch_opacity():
    pairs = [(0.0, 0)]
    for g in GLITCH_AT:
        pairs.append((round(g, 3), 0.85))
        pairs.append((round(g + 0.06, 3), 0))
    return pairs


def glitch_shift(sign):
    pairs = [(0.0, 0)]
    for k, g in enumerate(GLITCH_AT):
        pairs.append((round(g, 3), sign * (3 if k % 2 == 0 else 5)))
        pairs.append((round(g + 0.06, 3), 0))
    return pairs


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
    '@media (prefers-color-scheme: dark) {',
    '  .prompt { fill: #8b949e; }',
    '  .out    { fill: #3fb950; }',
    '  .err    { fill: #f85149; }',
    '  .name   { fill: #e6edf3; }',
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
    parts.append(
        f'<rect x="{base_x}" y="{step["y_cmd"] - 20}" height="28" width="0">'
        + anim("width", type_pairs(step, CHAR_W)) + '</rect>')
    parts.append('</clipPath>')

parts.append('</defs>')

for n, step in enumerate(STEPS):
    parts.append(f'<text class="mono prompt" x="{X0}" y="{step["y_cmd"]}" '
                 f'font-size="16">{PROMPT}</text>')
    parts.append(f'<g clip-path="url(#clip{n})">')
    parts.append(f'<text class="mono cmd" x="{base_x}" y="{step["y_cmd"]}" '
                 f'font-size="16">{step["cmd"]}</text>')
    parts.append('</g>')

    if step["out"] is not None:
        cls = "err" if step["err"] else "out"
        parts.append(
            f'<text class="mono {cls}" x="{X0}" y="{step["y_out"]}" font-size="14" '
            f'opacity="0">{step["out"]}'
            + anim("opacity", [(0.0, 0), (step["reveal"], 1), (FADE, 1), (LOOP - 0.1, 0)])
            + '</text>')

# nombre: la "salida" del whoami, con glitch
parts.append('<g>')
for color, sign in (("#00D4FF", -1), ("#FF3B6B", 1)):
    parts.append(
        f'<text class="mono" x="{X0}" y="{NAME_Y}" font-size="52" font-weight="700" '
        f'fill="{color}" opacity="0">{NAME}'
        + anim("opacity", glitch_opacity())
        + anim("dx", glitch_shift(sign)) + '</text>')
parts.append(
    f'<text class="mono name" x="{X0}" y="{NAME_Y}" font-size="52" font-weight="700" '
    f'opacity="0">{NAME}'
    + anim("opacity", [(0.0, 0), (NAME_AT, 1), (FADE, 1), (LOOP - 0.1, 0)]) + '</text>')
parts.append('</g>')

# barra azul bajo el nombre
parts.append(
    f'<rect x="{X0}" y="{BAR_Y}" height="3" width="0" fill="url(#sweep)">'
    + anim("width", [(0.0, 0), (NAME_AT, 0), (NAME_AT + 0.5, 440),
                     (FADE, 440), (LOOP - 0.1, 0)], calc="linear") + '</rect>')

# cursor
parts.append(
    f'<rect width="9" height="18" fill="#0066FF" x="{base_x}" '
    f'y="{STEPS[0]["y_cmd"] - 13}">'
    + anim("x", cur_x) + anim("y", cur_y) + anim("opacity", blink) + '</rect>')

parts.append('</svg>')

svg = "\n".join(parts)
out = "/home/jorge/Documentos/jorgemg1414/assets/header.svg"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as fh:
    fh.write(svg)
print(f"{out}  ({len(svg) / 1024:.1f} KB, ciclo de {LOOP:.1f}s)")
