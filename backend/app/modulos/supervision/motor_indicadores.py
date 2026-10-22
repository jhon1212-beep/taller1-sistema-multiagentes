"""TA-019: motor determinista de indicadores I1-I4 y reglas R1-R4.

No usa LLM ni consulta fuentes: recibe las evidencias ya consolidadas y una
fecha de corte configurable, y devuelve indicadores y alertas (sin explicacion).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from app.modulos.supervision.dominio import Alerta, Indicadores

ESTADO_LISTO = "Listo"
ESTADO_EN_CURSO = "En curso"
VENTANA_R2_DIAS = 7   # tarea en curso sin ediciones
VENTANA_R3_DIAS = 7   # repositorio sin commits
VENTANA_R4_DIAS = 14  # carpeta sin documentos modificados


def _campo(evidencia: Any, nombre: str) -> Any:
    """Lee un campo de una Evidencia (dataclass) o de un dict."""
    if isinstance(evidencia, Mapping):
        return evidencia.get(nombre)
    return getattr(evidencia, nombre, None)


def parsear_fecha(valor: str | date | datetime | None, *, fin_de_dia: bool = False) -> datetime | None:
    """Convierte ISO 8601 (o date) a datetime UTC. Una fecha sin hora (p. ej.
    fecha_limite) se toma al inicio del dia, o al final si fin_de_dia=True."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        dt = valor
    elif isinstance(valor, date):
        dt = datetime(valor.year, valor.month, valor.day)
    else:
        texto = str(valor).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(texto)
        except ValueError:
            return None
        if len(texto) == 10 and fin_de_dia:  # solo "YYYY-MM-DD"
            dt = dt + timedelta(days=1) - timedelta(microseconds=1)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parsear_corte(fecha_corte: str) -> datetime:
    corte = parsear_fecha(fecha_corte)
    if corte is None or "T" not in str(fecha_corte):
        raise ValueError("fecha_corte debe ser ISO 8601 con zona horaria.")
    if datetime.fromisoformat(str(fecha_corte).replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("fecha_corte debe incluir zona horaria.")
    return corte


def _hasta_corte(evidencias: Iterable[Any], corte: datetime) -> list[Any]:
    """Descarta evidencias posteriores al corte (las sin fecha se conservan)."""
    resultado = []
    for ev in evidencias:
        fecha = parsear_fecha(_campo(ev, "fecha"))
        if fecha is None or fecha <= corte:
            resultado.append(ev)
    return resultado


def _porcentaje(parte: int, total: int) -> float | None:
    return None if total == 0 else round(parte * 100 / total, 2)


def _dia_de_corte(fecha_corte: str) -> date:
    """Dia calendario del corte en su propia zona horaria (la fecha limite es un dia, no un instante)."""
    return datetime.fromisoformat(str(fecha_corte).replace("Z", "+00:00")).date()


def _vencida(tarea: Any, dia_corte: date) -> bool:
    """No completada y con fecha limite anterior al dia del corte (R1 / I3)."""
    if _campo(tarea, "estado") == ESTADO_LISTO:
        return False
    limite = _campo(tarea, "fecha_limite")
    if not limite:
        return False
    try:
        dia = limite if isinstance(limite, date) and not isinstance(limite, datetime) else date.fromisoformat(str(limite)[:10])
    except ValueError:
        return False
    return dia < dia_corte


def _ids_recientes(evidencias: list[Any]) -> list[str]:
    """id_externo de la evidencia mas reciente (RN-003: toda alerta tiene evidencia)."""
    fechadas = [(parsear_fecha(_campo(e, "fecha")), e) for e in evidencias]
    fechadas = [(f, e) for f, e in fechadas if f is not None]
    if not fechadas:
        return []
    return [str(_campo(max(fechadas, key=lambda x: x[0])[1], "id_externo"))]


def calcular_indicadores(evidencias: Iterable[Any], fecha_corte: str) -> Indicadores:
    """I1 % completadas, I2 % pendientes, I3 tareas vencidas, I4 dias sin actividad."""
    corte = _parsear_corte(fecha_corte)
    todas = _hasta_corte(evidencias, corte)
    tareas = [e for e in todas if _campo(e, "fuente") == "notion"]

    listas = sum(1 for t in tareas if _campo(t, "estado") == ESTADO_LISTO)
    pendientes = len(tareas) - listas  # incluye "Sin empezar" y "En curso"

    fechas = [f for f in (parsear_fecha(_campo(e, "fecha")) for e in todas) if f is not None]
    i4 = None if not fechas else max(0, (corte - max(fechas)).days)

    return {
        "I1": _porcentaje(listas, len(tareas)),
        "I2": _porcentaje(pendientes, len(tareas)),
        "I3": sum(1 for t in tareas if _vencida(t, _dia_de_corte(fecha_corte))),
        "I4": i4,
    }


def evaluar_reglas(evidencias: Iterable[Any], fecha_corte: str) -> list[Alerta]:
    """Evalua R1-R4 y devuelve alertas sin explicacion (la agrega otro componente)."""
    corte = _parsear_corte(fecha_corte)
    todas = _hasta_corte(evidencias, corte)
    por_fuente = {f: [e for e in todas if _campo(e, "fuente") == f] for f in ("github", "notion", "drive")}
    alertas: list[Alerta] = []

    def alerta(regla: str, fuente: str, ids: list[str]) -> Alerta:
        return {"regla": regla, "fuente": fuente, "evidencia_ids": ids,
                "explicacion": None, "origen_explicacion": None}  # type: ignore[return-value]

    # R1: tarea no completada con fecha limite anterior al corte
    for t in por_fuente["notion"]:
        if _vencida(t, _dia_de_corte(fecha_corte)):
            alertas.append(alerta("R1", "notion", [str(_campo(t, "id_externo"))]))

    # R2: tarea en curso sin ediciones durante mas de 7 dias
    for t in por_fuente["notion"]:
        editada = parsear_fecha(_campo(t, "fecha"))
        if (_campo(t, "estado") == ESTADO_EN_CURSO and editada is not None
                and corte - editada > timedelta(days=VENTANA_R2_DIAS)):
            alertas.append(alerta("R2", "notion", [str(_campo(t, "id_externo"))]))

    # R3 / R4: ausencia de actividad en la ventana previa al corte
    for regla, fuente, dias in (("R3", "github", VENTANA_R3_DIAS), ("R4", "drive", VENTANA_R4_DIAS)):
        evs = por_fuente[fuente]
        desde = corte - timedelta(days=dias)
        if not any((f := parsear_fecha(_campo(e, "fecha"))) is not None and f >= desde for e in evs):
            alertas.append(alerta(regla, fuente, _ids_recientes(evs)))

    return alertas


def evaluar(evidencias: Iterable[Any], fecha_corte: str) -> dict:
    """Punto de entrada para TA-015: indicadores + alertas para la fecha de corte."""
    lista = list(evidencias)
    return {
        "indicadores": calcular_indicadores(lista, fecha_corte),
        "alertas": evaluar_reglas(lista, fecha_corte),
    }
