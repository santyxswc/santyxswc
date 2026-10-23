#!/usr/bin/env python3
"""Genera el banner animado del perfil (assets/banner-dark.svg y banner-light.svg).

El retrato se dibuja con puntos (difuminado 1-bit) y se transforma en cada logo de
scripts/logos/ (en orden alfabético) antes de volver al retrato. A la derecha va
un panel tipo editor con perfil.yml.

Uso, desde la raíz del repo:
    pip install -r scripts/requirements.txt
    python scripts/banner.py
"""

from __future__ import annotations

import html
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

RAIZ = Path(__file__).resolve().parents[1]
RETRATO = RAIZ / "assets/source/portrait.png"
LOGOS = RAIZ / "scripts/logos"
SALIDA = RAIZ / "assets"

W, H = 1180, 600
# Marco del retrato (zona donde viven los puntos).
MX, MY, MW, MH = 52, 128, 380, 416
SEMILLA = 2026
VIAJEROS = 900          # puntos que se mueven entre figuras
PUNTOS_LOGO = 2600      # nube densa que se muestra mientras el logo está quieto
MAX_PUNTOS_RETRATO = 40000
PAUSA, TRANSICION = 3.4, 1.3
FUENTE = "ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,monospace"

PERFIL_YML = [
    (0, "perfil", ""),
    (1, "nombre", "Santiago Caicedo"),
    (1, "rol", "DevOps · Full Stack · Ciberseguridad"),
    (1, "origen", "Colombia"),
    (1, "estudio", "Ing. de Sistemas · Unicauca"),
    (1, "enfoque", "CI/CD · Arquitectura · Linux"),
    (0, "stack", ""),
    (1, "lenguajes", "TypeScript · Go · Kotlin · Java · Python"),
    (1, "frontend", "React · Next.js · Tailwind"),
    (1, "backend", "Go (chi) · Spring Boot · NestJS · .NET"),
    (1, "devops", "Docker · Terraform · GitHub Actions"),
    (1, "seguridad", "Nmap · Wireshark · Burp Suite"),
    (1, "sistemas", "Arch Linux · Kali Linux"),
    (0, "contacto", ""),
    (1, "github", "santyxswc"),
    (1, "zona", "UTC-5 · Colombia"),
]

# Paleta Tokyo Night (noche y día).
TEMAS = {
    "dark": {
        "fondo": "#1a1b26", "panel": "#16161e", "panel2": "#1f2335",
        "linea": "#292e42", "tenue": "#565f89", "texto": "#c0caf5",
        "puntos": "#7aa2f7", "clave": "#bb9af7", "seccion": "#7dcfff",
        "verde": "#9ece6a", "sombra": "#000000",
        "pantalla": "#1f2335", "pantalla_linea": "#292e42", "pantalla_tenue": "#565f89",
        "luz": "#7aa2f7", "pantalla_titulo": "#bb9af7",
    },
    "light": {
        "fondo": "#e1e2e7", "panel": "#f2f3f7", "panel2": "#e9e9ed",
        "linea": "#c4c8da", "tenue": "#8990b3", "texto": "#3760bf",
        "puntos": "#2e7de9", "clave": "#9854f1", "seccion": "#007197",
        "verde": "#587539", "sombra": "#8990b3",
        # El marco del retrato sigue oscuro: el difuminado sólo se lee bien como luz sobre negro.
        "pantalla": "#1f2335", "pantalla_linea": "#3b4261", "pantalla_tenue": "#737aa2",
        "luz": "#7aa2f7", "pantalla_titulo": "#bb9af7",
    },
}


def fmt(v: float, dec: int = 1) -> str:
    return f"{v:.{dec}f}".rstrip("0").rstrip(".")


def difuminar(gris: np.ndarray) -> np.ndarray:
    """Floyd-Steinberg a 1 bit; True es un punto encendido."""
    img = Image.fromarray(gris.astype("uint8")).convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    return np.asarray(img, dtype=bool)


def puntos_retrato(rng: np.random.Generator) -> np.ndarray:
    fuente = Image.open(RETRATO).convert("RGBA")
    # Recorte de cabeza y hombros con la proporción del marco.
    w, h = fuente.size
    ancho = int(w * 0.7)
    alto = int(ancho * MH / MW)
    izq = int(w * 0.16)
    sup = int(h * 0.04)
    recorte = fuente.crop((izq, sup, izq + ancho, sup + alto)).resize((MW, MH), Image.Resampling.LANCZOS)
    alfa = np.asarray(recorte.getchannel("A"), dtype=np.float32) / 255

    base = Image.new("RGBA", recorte.size, "black")
    base.alpha_composite(recorte)
    gris = ImageOps.autocontrast(ImageOps.grayscale(base.convert("RGB")), cutoff=1)
    gris = ImageEnhance.Contrast(gris).enhance(1.3)
    gris = gris.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=1))

    bits = difuminar(np.asarray(gris))
    activos = bits & (alfa > 0.1)
    ys, xs = np.nonzero(activos)
    pts = np.column_stack((MX + xs, MY + ys)).astype(np.float32)
    if len(pts) > MAX_PUNTOS_RETRATO:
        pts = pts[rng.choice(len(pts), MAX_PUNTOS_RETRATO, replace=False)]
    return pts


def puntos_logo(ruta: Path) -> np.ndarray:
    icono = Image.open(ruta).convert("RGBA")
    icono.thumbnail((300, 300), Image.Resampling.LANCZOS)
    ys, xs = np.nonzero(np.asarray(icono.getchannel("A")) > 127)
    ox = MX + (MW - icono.width) / 2
    oy = MY + (MH - icono.height) / 2
    return np.column_stack((ox + xs, oy + ys)).astype(np.float32)


def asignar(origen: np.ndarray, destino: np.ndarray) -> np.ndarray:
    """Reordena el destino para que cada punto recorra la menor distancia posible."""
    filas, cols = linear_sum_assignment(cdist(origen, destino, "sqeuclidean"))
    orden = np.empty_like(destino)
    orden[filas] = destino[cols]
    return orden


def trazo_puntos(pts: np.ndarray) -> str:
    """Une puntos vecinos de una misma fila en segmentos para que el SVG pese menos."""
    unicos = sorted({(int(x), int(y)) for x, y in np.rint(pts)}, key=lambda p: (p[1], p[0]))
    partes, i = [], 0
    while i < len(unicos):
        x0, y = unicos[i]
        x1 = x0
        i += 1
        while i < len(unicos) and unicos[i][1] == y and unicos[i][0] == x1 + 1:
            x1 = unicos[i][0]
            i += 1
        partes.append(f"M{x0} {y}h{x1 - x0 + 1}")
    return "".join(partes)


def texto(x: float, y: float, contenido: str, color: str, tam: int = 13, extra: str = "") -> str:
    return (f'<text x="{fmt(x)}" y="{fmt(y)}" fill="{color}" font-family="{FUENTE}" '
            f'font-size="{tam}" {extra}>{contenido}</text>')


def renderizar(tema: str, retrato: np.ndarray, logos: list[np.ndarray], rng: np.random.Generator) -> str:
    t = TEMAS[tema]
    n = min(VIAJEROS, len(retrato))
    inicio = retrato[rng.choice(len(retrato), n, replace=False)]

    # Línea de tiempo: retrato, logo 1, logo 2, ... y de vuelta al retrato.
    tiempos, cuadros = [0.0, PAUSA], [inicio, inicio]
    actual = inicio
    for logo in logos:
        actual = asignar(actual, logo[rng.choice(len(logo), n, replace=len(logo) < n)])
        tiempos += [tiempos[-1] + TRANSICION, tiempos[-1] + TRANSICION + PAUSA]
        cuadros += [actual, actual]
    tiempos.append(tiempos[-1] + TRANSICION)
    cuadros.append(inicio)
    dur = tiempos[-1]
    claves = ";".join(fmt(v / dur, 4) for v in tiempos)

    def anim_opacidad(puntos_clave: list[tuple[float, float]]) -> str:
        kt = ";".join(fmt(s / dur, 4) for s, _ in puntos_clave)
        vals = ";".join(fmt(o, 2) for _, o in puntos_clave)
        return (f'<animate attributeName="opacity" dur="{fmt(dur, 2)}s" repeatCount="indefinite" '
                f'keyTimes="{kt}" values="{vals}"/>')

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        'role="img" aria-labelledby="titulo desc">',
        '<title id="titulo">Santiago Caicedo · DevOps · Full Stack · Ciberseguridad</title>',
        '<desc id="desc">Retrato hecho de puntos que se transforma en los logos de Linux y Arch Linux, '
        'junto a un editor con el archivo perfil.yml.</desc>',
        "<defs>",
        f'<filter id="sombra" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="10" '
        f'stdDeviation="14" flood-color="{t["sombra"]}" flood-opacity=".3"/></filter>',
        f'<clipPath id="marco"><rect x="{MX}" y="{MY}" width="{MW}" height="{MH}"/></clipPath>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["fondo"]}"/>',
        f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="12" fill="{t["panel"]}" '
        f'stroke="{t["linea"]}" filter="url(#sombra)"/>',
        f'<path d="M14 60H{W - 14}" stroke="{t["linea"]}"/>',
        '<circle cx="40" cy="37" r="6" fill="#f7768e"/><circle cx="61" cy="37" r="6" fill="#e0af68"/>'
        '<circle cx="82" cy="37" r="6" fill="#9ece6a"/>',
        texto(W / 2, 42, "santyxswc@arch: ~ — nvim perfil.yml", t["tenue"], 13, 'text-anchor="middle"'),
        # Marco izquierdo.
        f'<rect x="{MX - 16}" y="80" width="{MW + 32}" height="{H - 112}" rx="6" fill="{t["pantalla"]}" '
        f'stroke="{t["pantalla_linea"]}"/>',
        f'<path d="M{MX - 16} 114H{MX + MW + 16}" stroke="{t["pantalla_linea"]}"/>',
        texto(MX, 102, "RETRATO.MAP", t["pantalla_titulo"], 13, 'font-weight="700" letter-spacing="1.2"'),
        texto(MX + MW, 102, "1-bit · tux · arch", t["pantalla_tenue"], 11, 'text-anchor="end"'),
        f'<g clip-path="url(#marco)" shape-rendering="crispEdges">',
    ]

    # Retrato completo: aparece por grupos al inicio y se desvanece cuando arrancan los logos.
    fin_retrato = PAUSA + TRANSICION * 0.6
    p.append(f'<g>{anim_opacidad([(0, 1), (PAUSA, 1), (fin_retrato, 0), (dur - TRANSICION * 0.4, 0), (dur, 1)])}')
    # La opacidad base es la final, así los visores sin animación muestran el retrato.
    grupos = rng.integers(0, 40, size=len(retrato))
    for g in range(40):
        pts = retrato[grupos == g]
        if len(pts):
            espera = rng.uniform(0, 1.4)
            p.append(f'<path d="{trazo_puntos(pts)}" stroke="{t["luz"]}" stroke-width="1" opacity=".95">'
                     f'<animate attributeName="opacity" dur="{fmt(espera + .7, 2)}s" values="0;0;.95" '
                     f'keyTimes="0;{fmt(espera / (espera + .7), 3)};1" fill="freeze"/></path>')
    p.append("</g>")

    # Nube densa de cada logo mientras está quieto.
    for i, logo in enumerate(logos):
        llega = PAUSA + TRANSICION * (i + 1) + PAUSA * i
        sale = llega + PAUSA
        nube = logo[rng.choice(len(logo), min(PUNTOS_LOGO, len(logo)), replace=False)]
        p.append(f'<path d="{trazo_puntos(nube)}" stroke="{t["luz"]}" stroke-width="1" opacity="0">'
                 + anim_opacidad([(0, 0), (llega - 0.2, 0), (llega + 0.3, .9), (sale, .9),
                                  (sale + 0.4, 0), (dur, 0)])
                 + "</path>")

    # Viajeros: cada uno es un cuadrito que recorre todas las figuras.
    for i in range(n):
        valores = ";".join(f"{fmt(c[i, 0])} {fmt(c[i, 1])}" for c in cuadros)
        p.append(f'<rect width="1.6" height="1.6" fill="{t["luz"]}" '
                 f'transform="translate({fmt(inicio[i, 0])} {fmt(inicio[i, 1])})">'
                 f'<animateTransform attributeName="transform" type="translate" dur="{fmt(dur, 2)}s" '
                 f'repeatCount="indefinite" calcMode="spline" keyTimes="{claves}" values="{valores}" '
                 f'keySplines="{";".join([".45 0 .25 1"] * (len(cuadros) - 1))}"/></rect>')
    p.append("</g>")
    p.append(texto(MX + 4, MY + MH + 22, f"PTS {len(retrato):05d} · FLOYD-STEINBERG", t["pantalla_tenue"], 10))

    # Panel derecho: editor con perfil.yml.
    px = MX + MW + 36
    pw = W - 36 - px
    p += [
        f'<rect x="{px}" y="80" width="{pw}" height="{H - 112}" rx="6" fill="{t["panel2"]}" stroke="{t["linea"]}"/>',
        f'<path d="M{px} 114H{px + pw}" stroke="{t["linea"]}"/>',
        texto(px + 16, 102, "perfil.yml", t["clave"], 13, 'font-weight="700"'),
        texto(px + 104, 102, "[YAML]", t["tenue"], 11),
        f'<rect x="{px + pw - 132}" y="88" width="116" height="22" rx="11" fill="{t["puntos"]}" '
        f'fill-opacity=".14" stroke="{t["puntos"]}"/>',
        texto(px + pw - 74, 103, "@santyxswc", t["puntos"], 12, 'text-anchor="middle" font-weight="700"'),
    ]
    y = 142.0
    for num, (sangria, clave, valor) in enumerate(PERFIL_YML, 1):
        p.append(texto(px + 32, y, f"{num:2d}", t["tenue"], 13, 'text-anchor="end" opacity=".6"'))
        if sangria == 0:
            p.append(texto(px + 48, y, f"{html.escape(clave)}:", t["seccion"], 13, 'font-weight="700"'))
        else:
            p.append(texto(px + 66, y, f'<tspan fill="{t["clave"]}">{html.escape(clave)}:</tspan> '
                                       f'<tspan fill="{t["texto"]}">{html.escape(valor)}</tspan>', t["texto"], 13))
        y += 22.5
    # Cursor parpadeante en la última línea.
    p.append(f'<rect x="{px + 48}" y="{fmt(y - 13)}" width="8" height="15" fill="{t["texto"]}">'
             '<animate attributeName="opacity" dur="1.1s" repeatCount="indefinite" calcMode="discrete" '
             'values="1;0" keyTimes="0;.5"/></rect>')

    # Barra de estado al estilo de Neovim.
    by = H - 32 - 30
    total_bytes = sum(len(c) + len(v) + 4 for _, c, v in PERFIL_YML)
    p += [
        f'<path d="M{px} {by}H{px + pw}" stroke="{t["linea"]}"/>',
        f'<rect x="{px + 10}" y="{by + 6}" width="70" height="19" rx="3" fill="{t["puntos"]}"/>',
        texto(px + 45, by + 19, "NORMAL", t["panel"], 11, 'text-anchor="middle" font-weight="700"'),
        texto(px + 92, by + 19, "perfil.yml", t["texto"], 12),
        texto(px + 200, by + 19, "utf-8 · unix", t["tenue"], 11),
        texto(px + pw - 12, by + 19, f"{len(PERFIL_YML)}L, {total_bytes}B   100%", t["tenue"], 11,
              'text-anchor="end"'),
        "</svg>",
    ]
    return "".join(p)


def main() -> None:
    if not RETRATO.exists():
        raise SystemExit(f"Falta el retrato: {RETRATO.relative_to(RAIZ)}")
    rutas = sorted(r for r in LOGOS.iterdir() if r.suffix.lower() in {".png", ".webp"})
    if not rutas:
        raise SystemExit(f"No hay logos en {LOGOS.relative_to(RAIZ)}")
    logos = [puntos_logo(r) for r in rutas]
    for i, tema in enumerate(TEMAS):
        rng = np.random.default_rng(SEMILLA + i)
        svg = renderizar(tema, puntos_retrato(rng), logos, rng)
        destino = SALIDA / f"banner-{tema}.svg"
        destino.write_text(svg, encoding="utf-8")
        print(f"{destino.relative_to(RAIZ)}: {destino.stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
