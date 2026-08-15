#!/usr/bin/env python3
"""Tarjeta de lenguajes del README: suma los bytes de todos tus repos.

A diferencia de las tarjetas de terceros, esta si ve los repos privados: el
workflow le pasa un token con scope repo. Lo unico que se publica es el
resumen; ni el codigo ni los nombres de los repos salen del SVG.

Sin token cae a lo publico, asi que nunca rompe el workflow.

CSS embebido -> se adapta al tema claro/oscuro dentro de un <img>, igual
que header.svg.

    GH_TOKEN=ghp_xxx python3 assets/gen_langs.py [salida.svg]
"""
import json
import os
import sys
import urllib.error
import urllib.request

USER = "jorgemg1414"
API = "https://api.github.com"

TOP_N = 6                 # lenguajes con nombre propio; el resto va a "otros"
EXCLUDE_REPOS = set()     # repos que no cuentan: {"taskbar-debian"}
EXCLUDE_LANGS = set()     # lenguajes a ignorar: {"Batchfile"}

W = 500
PAD = 22
BAR_Y, BAR_H = 68, 12
LEG_Y, ROW_H = 104, 22

# rampa azul del perfil, de mayor a menor peso (los mismos tonos del snake)
RAMP = ["#0066FF", "#3d8bff", "#66a3ff", "#89b8ff", "#a8ccff", "#c6dcff"]
OTHERS = "#8b949e"

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": USER}


def api(path, auth):
    """auth=False va sin credencial: un token invalido tumba hasta lo publico."""
    headers = dict(HEADERS)
    if auth:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)


def paginar(base, auth):
    found, page = [], 1
    while True:
        chunk = api(base + str(page), auth)
        found += chunk
        if len(chunk) < 100:
            break
        page += 1
    return found


def repos():
    """(repos, autenticado). Con token valido incluye privados; si no, publico.

    /user/repos necesita un token de usuario: el GITHUB_TOKEN de Actions no
    tiene contexto de usuario y responde 401, igual que un PAT revocado.
    """
    if TOKEN:
        try:
            found = paginar("/user/repos?affiliation=owner&per_page=100&page=", True)
            privados = sum(1 for r in found if r.get("private"))
            print(f"  {len(found)} repos ({privados} privados) con token")
            return found, True
        except urllib.error.HTTPError as err:
            print(f"  token rechazado (HTTP {err.code}): "
                  f"revisa que PROFILE_TOKEN siga vigente")
    else:
        print("  sin token en el entorno")

    found = paginar(f"/users/{USER}/repos?per_page=100&page=", False)
    print(f"  {len(found)} repos publicos, sigo sin token")
    return found, False


def totales():
    """(bytes por lenguaje, autenticado), sumando repos propios que no sean fork."""
    lista, autenticado = repos()
    acc = {}
    for repo in lista:
        if repo.get("fork") or repo["name"] in EXCLUDE_REPOS:
            continue
        try:
            langs = api(f"/repos/{repo['full_name']}/languages", autenticado)
        except urllib.error.HTTPError as err:
            print(f"  {repo['name']}: HTTP {err.code}, lo salto")
            continue
        for lang, size in langs.items():
            if lang not in EXCLUDE_LANGS:
                acc[lang] = acc.get(lang, 0) + size
    return acc, autenticado


def reparto(acc):
    """Top N con porcentaje; lo que sobra se agrupa en 'otros'."""
    total = sum(acc.values())
    if not total:
        raise SystemExit("no encontre lenguajes que contar")
    orden = sorted(acc.items(), key=lambda kv: -kv[1])
    filas = [(lang, size / total * 100, RAMP[n])
             for n, (lang, size) in enumerate(orden[:TOP_N])]
    resto = sum(size for _, size in orden[TOP_N:])
    if resto:
        filas.append((f"otros ({len(orden) - TOP_N})", resto / total * 100, OTHERS))
    return filas


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(filas, privados):
    ancho = W - 2 * PAD
    col_w = (ancho - 12) / 2
    n_rows = (len(filas) + 1) // 2
    h = LEG_Y + n_rows * ROW_H + 6
    fuente = "incluye repos privados" if privados else "solo repos publicos"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" role="img" aria-label="Lenguajes mas usados">',
        '<style>',
        '.mono { font-family: "Fira Code","JetBrains Mono","SF Mono",Consolas,monospace; }',
        '.cmd  { fill: #0066FF; }',
        '.name { fill: #1f2328; }',
        '.mut  { fill: #57606a; }',
        '.track{ fill: #ebedf0; }',
        '@media (prefers-color-scheme: dark) {',
        '  .name { fill: #e6edf3; }',
        '  .mut  { fill: #8b949e; }',
        '  .track{ fill: #21262d; }',
        '}',
        '</style>',
        '<defs><clipPath id="bar">',
        f'<rect x="{PAD}" y="{BAR_Y}" width="{ancho}" height="{BAR_H}" rx="{BAR_H / 2}"/>',
        '</clipPath></defs>',
        f'<text class="mono cmd" x="{PAD}" y="34" font-size="15">'
        f'$ tokei ~/proyectos</text>',
        f'<text class="mono mut" x="{PAD}" y="52" font-size="11">{fuente}</text>',
        f'<g clip-path="url(#bar)">',
        f'<rect class="track" x="{PAD}" y="{BAR_Y}" width="{ancho}" height="{BAR_H}"/>',
    ]

    x = float(PAD)
    for _lang, pct, color in filas:
        seg = ancho * pct / 100
        parts.append(f'<rect x="{x:.1f}" y="{BAR_Y}" width="{seg:.1f}" '
                     f'height="{BAR_H}" fill="{color}"/>')
        x += seg
    parts.append('</g>')

    for n, (lang, pct, color) in enumerate(filas):
        col, row = n % 2, n // 2
        x0 = PAD + col * (col_w + 12)
        y = LEG_Y + row * ROW_H
        parts.append(f'<circle cx="{x0 + 5:.1f}" cy="{y - 4}" r="5" fill="{color}"/>')
        parts.append(f'<text class="mono name" x="{x0 + 18:.1f}" y="{y}" '
                     f'font-size="12">{esc(lang)}</text>')
        parts.append(f'<text class="mono mut" x="{x0 + col_w:.1f}" y="{y}" '
                     f'font-size="12" text-anchor="end">{pct:.1f}%</text>')

    parts.append('</svg>')
    return "\n".join(parts), h


if __name__ == "__main__":
    acc, autenticado = totales()
    filas = reparto(acc)
    svg, h = render(filas, autenticado)

    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "langs.svg")
    os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    with open(destino, "w") as fh:
        fh.write(svg)

    for lang, pct, _ in filas:
        print(f"  {lang:<16} {pct:5.1f}%")
    print(f"{destino}  ({len(svg) / 1024:.1f} KB, {W}x{h})")
