#!/usr/bin/env python3
"""Genera las tarjetas `$ whoami` y `$ cat sobre-mi.md` del perfil (versiones dark y light).

Sólo usa la librería estándar:
    python scripts/whoami.py
"""

from __future__ import annotations

from terminal import FUENTE, TEMAS, barras, guardar, panel, texto, ventana

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

SOBRE_MI = [
    ("estudio", "Ingeniería de Sistemas · Universidad del Cauca"),
    ("arquitectura", "capas · MVC · microkernel · microservicios · hexagonal"),
    ("escritorio", ".NET + Avalonia · Electron · Tauri"),
    ("web", "Next.js · React · NestJS · Spring Boot · Go"),
    ("linux", "Arch y Kali a diario, desde la terminal"),
    ("calidad", "que compile, tenga pruebas y corra en CI"),
]


def whoami(tema: str) -> str:
    t = TEMAS[tema]
    p = ventana(t, 960, 400, "Santiago Caicedo — DevOps · Full Stack · Ciberseguridad",
                "Tarjeta de terminal con mi contexto, mis principales áreas y los lenguajes que más uso.",
                "santyxswc  ·  profile shell  ·  online")
    p += [
        panel(t, 29, 78, 626, 292),
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
    p += [panel(t, x0, 78, ancho, 292), texto(x0 + 18, 111, "❯ lenguajes --top", t["prompt"], 16, 'font-weight="700"')]
    p += barras(t, x0 + 18, 142, ancho - 36, [(n, f"{pct:.0f}%", pct, c) for n, pct, c in LENGUAJES])
    p.append(texto(x0 + 18, 360, "% líneas escritas · todos mis repos", t["tenue"], 10))
    p.append("</svg>")
    return "".join(p)


def sobre_mi(tema: str) -> str:
    t = TEMAS[tema]
    alto = 128 + len(SOBRE_MI) * 30 + 34
    p = ventana(t, 960, alto, "Sobre mí", "Estudios, intereses y forma de trabajar de Santiago Caicedo.",
                "santyxswc  ·  ~/  ·  sobre-mi.md")
    p += [panel(t, 29, 78, 902, alto - 108), texto(48, 111, "❯ cat sobre-mi.md", t["prompt"], 20, 'font-weight="700"')]
    for i, (clave, valor) in enumerate(SOBRE_MI):
        y = 148 + i * 30
        p.append(texto(48, y, f"{clave}:", t["clave"], 16))
        p.append(texto(200, y, valor, t["texto"], 16))
    p.append("</svg>")
    return "".join(p)


def main() -> None:
    for tema in TEMAS:
        guardar(f"whoami-{tema}.svg", whoami(tema))
        guardar(f"sobre-mi-{tema}.svg", sobre_mi(tema))


if __name__ == "__main__":
    main()
