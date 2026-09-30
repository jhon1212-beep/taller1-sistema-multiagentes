# -*- coding: utf-8 -*-
"""Pruebas de los indicadores y del manejo de fallos (CP-01 / CP-02)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from github_client import GitHubClient, GitHubError  # noqa: E402
from sync_github import gini, gini_normalizado, metricas  # noqa: E402

fallos = 0


def check(nombre, obtenido, esperado):
    global fallos
    ok = abs(obtenido - esperado) < 0.01 if isinstance(esperado, float) else obtenido == esperado
    print(f"{'✔' if ok else '✖'} {nombre}: obtenido={obtenido} esperado={esperado}")
    if not ok:
        fallos += 1


print("— Coeficiente de Gini —")
check("reparto equitativo [5,5,5,5]", gini([5, 5, 5, 5]), 0.0)
check("una sola persona [20,0,0,0]", gini([20, 0, 0, 0]), 0.75)   # máximo teórico n=4
check("normalizado de [20,0,0,0]", gini_normalizado([20, 0, 0, 0]), 1.0)
check("equipo unipersonal n=3 [9,0,0]", gini_normalizado([9, 0, 0]), 1.0)
# Comprobado a mano: ordenado [3,9,14,74]; acumulado=1*3+2*9+3*14+4*74=359
# gini = (2*359)/(4*100) - 5/4 = 1.795 - 1.25 = 0.545
check("caso Beta [74,14,9,3]", gini([74, 14, 9, 3]), 0.545)
check("normalizado caso Beta", gini_normalizado([74, 14, 9, 3]), 0.727)
check("sin commits []", gini([]), 0.0)

print("\n— Métricas sobre commits —")
commits = [
    {"autor": "luis",  "fecha": "2026-09-28T10:00:00Z"},
    {"autor": "luis",  "fecha": "2026-09-28T18:00:00Z"},
    {"autor": "marta", "fecha": "2026-09-27T09:00:00Z"},
]
m = metricas(commits, deadline=None, dias_ventana=3650)
check("commits totales", m["commits_total"], 3)
check("días con commit", m["dias_con_commit"], 2)
check("integrantes detectados", m["integrantes_detectados"], 2)

print("\n— Manejo de fallos (CP-02) —")
cliente = GitHubClient(token="", org="", api_url="https://api.github.com")
try:
    cliente.commits("octocat/repositorio-que-no-existe-xyz123")
    print("✖ debía lanzar GitHubError")
    fallos += 1
except GitHubError as err:
    print(f"✔ repositorio inexistente lanza GitHubError controlado: {err}")

try:
    GitHubClient(api_url="https://api.github.invalido").rate_limit()
    print("✖ debía lanzar GitHubError")
    fallos += 1
except GitHubError:
    print("✔ host inalcanzable lanza GitHubError controlado (no rompe el agente)")

print(f"\n{'TODAS LAS PRUEBAS PASARON' if not fallos else str(fallos) + ' PRUEBA(S) FALLARON'}")
sys.exit(1 if fallos else 0)
