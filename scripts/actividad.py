#!/usr/bin/env python3
"""Genera la tarjeta `$ git log --stats` (assets/actividad-dark.svg y actividad-light.svg).

Cuenta también los repos privados, por eso se corre en local con la sesión de gh:
    gh auth login
    python scripts/actividad.py

Los repos se clonan (sin archivos de trabajo) en .cache/repos y se actualizan en cada corrida.
"""

from __future__ import annotations

import collections
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from terminal import TEMAS, barras, guardar, panel, texto, ventana

USUARIO = "santyxswc"
AUTORES = ("wsantyx", "santyxswc", "csantx")  # correos y nombres con los que firmo commits
CACHE = Path(__file__).resolve().parents[1] / ".cache/repos"

EXTENSIONES = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go", ".kt": "Kotlin", ".kts": "Kotlin",
    ".java": "Java", ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".cs": "C#", ".cpp": "C++", ".hpp": "C++", ".cc": "C++", ".ino": "C++", ".c": "C",
}
COLORES = {
    "TypeScript": "#3178c6", "Go": "#00add8", "Kotlin": "#a97bff", "Java": "#b07219",
    "Python": "#3572a5", "JavaScript": "#f1e05a", "C#": "#178600", "C++": "#f34b7d", "C": "#555555",
}
# Dependencias, compilados y código generado no cuentan como escrito por mí.
IGNORAR = re.compile(r"(node_modules|vendor/|dist/|build/|bin/|obj/|\.min\.|lock|generated|\.gen\.|_gen\.|"
                     r"\.pb\.|mock|/gen/)", re.I)


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def graphql(consulta: str) -> dict:
    return json.loads(gh("api", "graphql", "-f", f"query={consulta}"))["data"]["viewer"]


def sincronizar(repos: list[str]) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for nombre in repos:
        destino = CACHE / nombre
        if destino.exists():
            subprocess.run(["git", "-C", str(destino), "fetch", "-q", "origin", "+refs/heads/*:refs/heads/*"], check=False)
        else:
            subprocess.run(["gh", "repo", "clone", f"{USUARIO}/{nombre}", str(destino), "--", "--bare", "-q"],
                           check=True)


def commits_por_lenguaje(repos: list[str]) -> tuple[collections.Counter, int]:
    """Asigna cada commit al lenguaje con más líneas agregadas en él.

    Mira todas las ramas: con squash merge la rama principal esconde los commits reales.
    """
    conteo: collections.Counter = collections.Counter()
    total = 0
    autores = [f"--author={a}" for a in AUTORES]
    for nombre in repos:
        salida = subprocess.run(["git", "-C", str(CACHE / nombre), "log", "--branches", "--no-merges", *autores,
                                 "--numstat", "--format=format:@@"], capture_output=True, text=True).stdout
        for bloque in salida.split("@@")[1:]:
            total += 1
            lineas: collections.Counter = collections.Counter()
            for fila in bloque.strip().splitlines():
                partes = fila.split("\t")
                if len(partes) != 3 or partes[0] == "-" or IGNORAR.search(partes[2]):
                    continue
                lenguaje = EXTENSIONES.get(os.path.splitext(partes[2])[1].lower())
                if lenguaje:
                    lineas[lenguaje] += int(partes[0])
            if lineas:
                conteo[lineas.most_common(1)[0][0]] += 1
    return conteo, total


def contribuciones(desde: datetime) -> int:
    total = 0
    for anio in range(desde.year, datetime.now(timezone.utc).year + 1):
        datos = graphql(f'query{{viewer{{contributionsCollection(from:"{anio}-01-01T00:00:00Z",'
                        f'to:"{anio}-12-31T23:59:59Z"){{contributionCalendar{{totalContributions}}}}}}}}')
        total += datos["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    return total


def renderizar(tema: str, stats: list[tuple[str, str]], lenguajes: list[tuple[str, int, float]]) -> str:
    t = TEMAS[tema]
    p = ventana(t, 960, 372, "Actividad en GitHub",
                "Estadísticas de mi cuenta y commits por lenguaje, incluyendo repos privados.",
                "santyxswc  ·  ~/repos  ·  git")
    p += [panel(t, 29, 78, 400, 264), texto(48, 111, "❯ git stats --all", t["prompt"], 18, 'font-weight="700"')]
    for i, (clave, valor) in enumerate(stats):
        y = 150 + i * 34
        p.append(texto(48, y, f"{clave}:", t["clave"], 15))
        p.append(texto(410, y, valor, t["valor"], 15, 'text-anchor="end" font-weight="700"'))

    x0, ancho = 451, 480
    p += [panel(t, x0, 78, ancho, 264),
          texto(x0 + 18, 111, "❯ git log --by-language", t["prompt"], 18, 'font-weight="700"')]
    filas = [(n, f"{c} commits · {pct:.0f}%", c, COLORES.get(n, t["tenue"])) for n, c, pct in lenguajes]
    p += barras(t, x0 + 18, 146, ancho - 36, filas, paso=36)
    p.append("</svg>")
    return "".join(p)


def main() -> None:
    cuenta = graphql("query{viewer{createdAt pullRequests{totalCount} "
                     "repositories(ownerAffiliations:OWNER,first:100){nodes{name isPrivate isFork stargazerCount}} "
                     "repositoriesContributedTo(includeUserRepositories:true,"
                     "contributionTypes:[COMMIT,PULL_REQUEST,ISSUE]){totalCount}}}")
    repos = [r for r in cuenta["repositories"]["nodes"] if not r["isFork"]]
    nombres = [r["name"] for r in repos if r["name"] != USUARIO]
    privados = sum(r["isPrivate"] for r in repos)
    desde = datetime.fromisoformat(cuenta["createdAt"].replace("Z", "+00:00"))

    sincronizar(nombres)
    por_lenguaje, total_commits = commits_por_lenguaje(nombres)
    clasificados = sum(por_lenguaje.values())
    top = [(n, c, 100 * c / clasificados) for n, c in por_lenguaje.most_common(6)]

    stats = [
        ("contribuciones", f"{contribuciones(desde):,}".replace(",", ".")),
        ("commits", f"{total_commits:,}".replace(",", ".")),
        ("pull_requests", str(cuenta["pullRequests"]["totalCount"])),
        ("repos", f"{len(repos)} ({privados} privados)"),
        ("estrellas", str(sum(r["stargazerCount"] for r in repos))),
        ("activo_desde", desde.strftime("%Y-%m")),
    ]
    for tema in TEMAS:
        guardar(f"actividad-{tema}.svg", renderizar(tema, stats, top))
    for nombre, valor in stats:
        print(f"  {nombre}: {valor}")
    for n, c, pct in top:
        print(f"  {n}: {c} commits ({pct:.1f}%)")


if __name__ == "__main__":
    main()
