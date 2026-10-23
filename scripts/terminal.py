"""Estilo compartido de las tarjetas tipo terminal (paleta Tokyo Night y ventana)."""

from __future__ import annotations

import html
from pathlib import Path

SALIDA = Path(__file__).resolve().parents[1] / "assets"
FUENTE = "ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,monospace"

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


def ventana(t: dict, w: int, h: int, titulo: str, desc: str, barra: str) -> list[str]:
    """Abre el SVG con el marco de la ventana; quien llama agrega el contenido y cierra con </svg>."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        'role="img" aria-labelledby="titulo desc">',
        f'<title id="titulo">{html.escape(titulo)}</title>',
        f'<desc id="desc">{html.escape(desc)}</desc>',
        f'<rect width="{w}" height="{h}" rx="18" fill="{t["fondo"]}"/>',
        f'<rect x="9" y="9" width="{w - 18}" height="{h - 18}" rx="13" fill="none" stroke="{t["borde"]}" '
        'stroke-opacity=".6" stroke-width="1.5"/>',
        '<circle cx="35" cy="35" r="5" fill="#f7768e"/><circle cx="54" cy="35" r="5" fill="#e0af68"/>'
        '<circle cx="73" cy="35" r="5" fill="#9ece6a"/>',
        texto(98, 40, barra, t["tenue"], 14),
        f'<path d="M29 58H{w - 29}" stroke="{t["linea"]}"/>',
    ]


def panel(t: dict, x: float, y: float, w: float, h: float) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{t["panel"]}" stroke="{t["linea"]}"/>'


def barras(t: dict, x: float, y: float, largo: float, filas: list[tuple[str, str, float, str]],
           paso: int = 36) -> list[str]:
    """Filas de nombre + etiqueta a la derecha + barra proporcional al mayor valor."""
    maximo = max(valor for _, _, valor, _ in filas)
    partes = []
    for i, (nombre, etiqueta, valor, color) in enumerate(filas):
        fy = y + i * paso
        partes.append(texto(x, fy, nombre, t["texto"], 14))
        partes.append(texto(x + largo, fy, etiqueta, t["tenue"], 13, 'text-anchor="end"'))
        partes.append(f'<rect x="{x}" y="{fy + 7}" width="{largo}" height="6" rx="3" fill="{t["barra"]}"/>')
        partes.append(f'<rect x="{x}" y="{fy + 7}" width="{largo * valor / maximo:.1f}" height="6" rx="3" '
                      f'fill="{color}"/>')
    return partes


def guardar(nombre: str, svg: str) -> None:
    SALIDA.mkdir(exist_ok=True)
    destino = SALIDA / nombre
    destino.write_text(svg, encoding="utf-8")
    print(destino.relative_to(SALIDA.parent))
