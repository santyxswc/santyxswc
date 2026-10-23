#!/usr/bin/env python3
"""Genera la tarjeta `$ whoami` del perfil (assets/whoami-dark.svg y whoami-light.svg).

Sólo usa la librería estándar:
    python scripts/whoami.py
"""

from __future__ import annotations

import html
from pathlib import Path

SALIDA = Path(__file__).resolve().parents[1] / "assets"
W, H = 960, 400
FUENTE = "ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,monospace"

VENTAJAS = [
    ("devops/", "Docker · Terraform · GitHub Actions · CI/CD"),
    ("fullstack/", "React · Next.js · Go · Spring Boot · NestJS"),
    ("ciberseguridad/", "Nmap · Wireshark · Burp Suite · Kali"),
]

# Porcentaje de líneas escritas por lenguaje en mis repos públicos y privados
# (git log --numstat en la rama principal, sin merges ni código generado).
LENGUAJES = [
    ("TypeScript", 21.6, "#3178c6"),
    ("Go", 18.6, "#00add8"),
    ("Kotlin", 16.1, "#a97bff"),
    ("Java", 14.5, "#b07219"),
    ("Python", 11.7, "#3572a5"),
    ("JavaScript", 8.1, "#f1e05a"),
]

TEMAS = {
    "dark": {
        "fondo": "#1a1b26", "panel": "#1f2335", "linea": "#292e42", "borde": "#7aa2f7",
        "tenue": "#565f89", "texto": "#c0caf5", "prompt": "#7dcfff", "rol": "#e0af68",
        "clave": "#bb9af7", "valor": "#9ece6a", "carpeta": "#f7768e", "barra": "#292e42",
    },
    "light": {
        "fondo": "#f2f3f7", "panel": "#e9e9ed", "linea": "#c4c8da", "borde": "#2e7de9",
        "tenue": "#8990b3", "texto": "#3760bf", "prompt": "#007197", "rol": "#8c6c3e",
        "clave": "#9854f1", "valor": "#587539", "carpeta": "#f52a65", "barra": "#d0d5e3",
    },
}


def texto(x: float, y: float, contenido: str, color: str, tam: int, extra: str = "") -> str:
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{FUENTE}" font-size="{tam}" {extra}>'
            f"{html.escape(contenido)}</text>")


def renderizar(tema: str) -> str:
    t = TEMAS[tema]
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'role="img" aria-labelledby="titulo desc">',
        '<title id="titulo">Santiago Caicedo — DevOps · Full Stack · Ciberseguridad</title>',
        '<desc id="desc">Tarjeta de terminal con mi contexto, mis principales áreas y los lenguajes que más uso.</desc>',
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["fondo"]}"/>',
        f'<rect x="9" y="9" width="{W - 18}" height="{H - 18}" rx="13" fill="none" stroke="{t["borde"]}" '
        'stroke-opacity=".6" stroke-width="1.5"/>',
        '<circle cx="35" cy="35" r="5" fill="#f7768e"/><circle cx="54" cy="35" r="5" fill="#e0af68"/>'
        '<circle cx="73" cy="35" r="5" fill="#9ece6a"/>',
        texto(98, 40, "santyxswc  ·  profile shell  ·  online", t["tenue"], 14),
        f'<path d="M29 58H{W - 29}" stroke="{t["linea"]}"/>',
        # Panel izquierdo.
        f'<rect x="29" y="78" width="626" height="292" rx="9" fill="{t["panel"]}" stroke="{t["linea"]}"/>',
        texto(48, 111, "❯ whoami", t["prompt"], 20, 'font-weight="700"'),
        f'<text x="48" y="143" font-family="{FUENTE}" font-size="17">'
        f'<tspan fill="{t["texto"]}">santiago_caicedo</tspan>'
        f'<tspan fill="{t["tenue"]}"> — </tspan>'
        f'<tspan fill="{t["rol"]}">DevOps · Full Stack · Ciberseguridad</tspan></text>',
        f'<path d="M48 162H636" stroke="{t["linea"]}"/>',
        texto(48, 191, "context:", t["tenue"], 16),
        texto(150, 191, "Colombia", t["clave"], 16),
        # Bandera de Colombia (amarillo el doble de alto que azul y rojo).
        '<rect x="242" y="179" width="22" height="7" fill="#fcd116"/>'
        '<rect x="242" y="186" width="22" height="3.5" fill="#003893"/>'
        '<rect x="242" y="189.5" width="22" height="3.5" fill="#ce1126"/>',
        texto(48, 218, "mission:", t["tenue"], 16),
        texto(150, 218, "software confiable, seguro y automatizado", t["valor"], 16),
        texto(48, 260, "❯ ls ventajas/", t["prompt"], 20, 'font-weight="700"'),
    ]
    for i, (carpeta, detalle) in enumerate(VENTAJAS):
        y = 292 + i * 27
        p.append(texto(48, y, carpeta, t["carpeta"], 15))
        p.append(texto(212, y, detalle, t["texto"], 15))

    # Panel derecho: lenguajes más usados.
    x0, ancho = 677, 254
    p += [
        f'<rect x="{x0}" y="78" width="{ancho}" height="292" rx="9" fill="{t["panel"]}" stroke="{t["linea"]}"/>',
        texto(x0 + 18, 111, "❯ lenguajes --top", t["prompt"], 16, 'font-weight="700"'),
    ]
    maximo = max(pct for _, pct, _ in LENGUAJES)
    largo = ancho - 36
    for i, (nombre, pct, color) in enumerate(LENGUAJES):
        y = 142 + i * 36
        p.append(texto(x0 + 18, y, nombre, t["texto"], 14))
        p.append(texto(x0 + ancho - 18, y, f"{pct:.0f}%", t["tenue"], 13, 'text-anchor="end"'))
        p.append(f'<rect x="{x0 + 18}" y="{y + 7}" width="{largo}" height="6" rx="3" fill="{t["barra"]}"/>')
        p.append(f'<rect x="{x0 + 18}" y="{y + 7}" width="{largo * pct / maximo:.1f}" height="6" rx="3" '
                 f'fill="{color}"/>')
    p.append(texto(x0 + 18, 360, "% líneas escritas · todos mis repos", t["tenue"], 10))
    p.append("</svg>")
    return "".join(p)


def main() -> None:
    SALIDA.mkdir(exist_ok=True)
    for tema in TEMAS:
        destino = SALIDA / f"whoami-{tema}.svg"
        destino.write_text(renderizar(tema), encoding="utf-8")
        print(destino.relative_to(SALIDA.parent))


if __name__ == "__main__":
    main()
