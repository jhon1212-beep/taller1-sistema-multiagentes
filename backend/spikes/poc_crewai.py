"""SP-001: POC CrewAI equivalente para comparación con LangGraph."""
import os
from pathlib import Path

from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

commits = """
- 2026-09-28 Integrante 1: estructura del repositorio
- 2026-09-29 Integrante 2: modelo de datos inicial
"""

llm = LLM(
    model=f"gemini/{os.environ['GEMINI_MODEL']}",
    api_key=os.environ["GEMINI_API_KEY"],
    temperature=0,
)

supervisor = Agent(
    role="Agente Supervisor",
    goal="Resumir el avance de un proyecto de software sin juzgar a los integrantes.",
    backstory="Supervisas evidencias académicas de avance de proyectos de software.",
    llm=llm,
    verbose=True,
)

tarea = Task(
    description=(
        "Resume en exactamente 2 frases el avance del proyecto "
        "a partir de estos commits, sin juzgar a nadie:\n"
        + commits
    ),
    expected_output="Un resumen neutral de exactamente 2 frases.",
    agent=supervisor,
)

crew = Crew(
    agents=[supervisor],
    tasks=[tarea],
    process=Process.sequential,
    verbose=True,
)

resultado = crew.kickoff()

print("\n=== RESULTADO CREWAI ===")
print(resultado)