from fastapi import FastAPI

app = FastAPI(
    title="Agentes inteligentes para el seguimiento de proyectos de software",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
