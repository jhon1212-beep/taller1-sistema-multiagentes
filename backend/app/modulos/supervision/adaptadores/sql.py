"""TA-018: historial por fecha de corte en PostgreSQL.

Implementa el puerto RepositorioSupervision (puertos.py) con las tablas
fuente, evidencia, indicador, alerta y validacion de TA-004. Reemplaza a
RepositorioSupervisionMemoria cuando hay base de datos.

Reglas del corte:
- Un corte es único por proyecto y día (UNIQUE proyecto_id + fecha_corte en
  la tabla indicador). Guardar otra vez el mismo día reemplaza el corte.
- Todo el corte se guarda en una sola transacción: o queda completo o no
  queda nada.
- Cada alerta apunta a la fila de su evidencia de origen (RN-003).
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.compartido import modelos_orm as orm
from app.modulos.evidencias.dominio import Evidencia, EvidenciaDrive, EvidenciaNotion
from app.modulos.supervision.grafo.estado import EstadoSupervision

SOURCES = ("github", "notion", "drive")


def cutoff_day(cutoff: str | date) -> date:
    """Día calendario del corte en su propia zona horaria.

    "2026-10-12T23:59:59-05:00" es el 12 de octubre en Lima aunque en UTC ya
    sea 13; el docente piensa en el día local.
    """
    if isinstance(cutoff, date) and not isinstance(cutoff, datetime):
        return cutoff
    text = str(cutoff).strip()
    if len(text) == 10:  # solo "YYYY-MM-DD"
        return date.fromisoformat(text)
    return datetime.fromisoformat(text.replace("Z", "+00:00")).date()


def _to_datetime(value: str | None, fallback: datetime) -> datetime:
    """La columna evidencia.fecha es NOT NULL: sin fecha se usa el corte."""
    if not value:
        return fallback
    moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _to_float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


class SqlSupervisionRepository:
    """Guarda y consulta cortes de supervisión (TA-018)."""

    def __init__(self, session: Session) -> None:
        self._s = session

    # -- escritura ---------------------------------------------------------
    def guardar(self, estado: EstadoSupervision) -> dict[str, int]:
        """Persiste evidencias, indicadores y alertas de un corte.

        Devuelve un resumen con lo guardado; las alertas sin evidencia no se
        pueden guardar (alerta.evidencia_id es NOT NULL) y se cuentan aparte.
        """
        project_id = estado["proyecto_id"]
        day = cutoff_day(estado["fecha_corte"])
        cutoff_moment = datetime.combine(day, time(23, 59, 59), tzinfo=timezone.utc)

        try:
            source_ids = self._source_ids(project_id)
            self._update_source_status(source_ids, estado)

            # 1) Evidencias: upsert por lotes y sin duplicados.
            evidence_ids = self._upsert_evidences(
                estado.get("evidencias") or [],
                source_ids,
                cutoff_moment,
            )

            # 2) Indicadores: una fila por proyecto y día (reemplaza si ya existía).
            indicators = estado["indicadores"]
            row = insert(orm.Indicador).values(
                proyecto_id=project_id,
                fecha_corte=day,
                i1_pct_completadas=indicators.get("I1"),
                i2_pct_pendientes=indicators.get("I2"),
                i3_tareas_vencidas=indicators.get("I3") or 0,
                i4_dias_sin_actividad=indicators.get("I4"),
            )
            self._s.execute(
                row.on_conflict_do_update(
                    index_elements=["proyecto_id", "fecha_corte"],
                    set_={
                        "i1_pct_completadas": row.excluded.i1_pct_completadas,
                        "i2_pct_pendientes": row.excluded.i2_pct_pendientes,
                        "i3_tareas_vencidas": row.excluded.i3_tareas_vencidas,
                        "i4_dias_sin_actividad": row.excluded.i4_dias_sin_actividad,
                        "calculado_en": func.now(),
                    },
                )
            )

            # 3) Alertas: se reemplazan las del mismo día para no mezclar ejecuciones.
            self._s.execute(
                delete(orm.Alerta).where(
                    orm.Alerta.proyecto_id == project_id, orm.Alerta.fecha_corte == day
                )
            )

            # Preparar inserción de alertas por lotes (RN-003).
            alert_rows = []
            without_evidence = 0

            for alert in estado.get("alertas") or []:
                ids = [
                    evidence_ids[(alert["fuente"], external_id)]
                    for external_id in alert.get("evidencia_ids") or []
                    if (alert["fuente"], external_id) in evidence_ids
                ]

                if not ids:
                    without_evidence += 1
                    continue

                for evidence_id in ids:
                    alert_rows.append({
                        "proyecto_id": project_id,
                        "evidencia_id": evidence_id,
                        "regla": alert["regla"],
                        "fecha_corte": day,
                        "explicacion": alert.get("explicacion") or "",
                        "origen_explicacion": (
                            alert.get("origen_explicacion") or "plantilla"
                        ),
                    })

            if alert_rows:
                self._s.execute(
                    insert(orm.Alerta).values(alert_rows)
                )

            saved = len(alert_rows)

            self._s.commit()
        except Exception:
            self._s.rollback()  # el corte queda completo o no queda
            raise

        return {
            "evidencias": len(evidence_ids),
            "alertas": saved,
            "alertas_sin_evidencia": without_evidence,
        }

    def _source_ids(self, project_id: int) -> dict[str, int]:
        rows = self._s.execute(
            select(orm.Fuente.tipo, orm.Fuente.id).where(orm.Fuente.proyecto_id == project_id)
        ).all()
        if not rows:
            raise LookupError(f"El proyecto {project_id} no tiene fuentes registradas.")
        return {kind: source_id for kind, source_id in rows}


    def _update_source_status(
        self,
        source_ids: dict[str, int],
        estado: EstadoSupervision,
    ) -> None:
        """Actualiza todas las fuentes mediante un único UPDATE SQL."""
        statuses = {
            kind: status
            for kind, status in (estado.get("estado_fuentes") or {}).items()
            if kind in source_ids and status in ("ok", "fallo")
        }
        if not statuses:
            return

        status_by_id = {source_ids[kind]: status for kind, status in statuses.items()}
        ok_ids = [source_id for source_id, status in status_by_id.items() if status == "ok"]
        now = datetime.now(timezone.utc)

        # Para estados de fallo, conservar la última sincronización válida.
        new_sync = (
            case(
                (orm.Fuente.id.in_(ok_ids), now),
                else_=orm.Fuente.ultima_sincronizacion,
            )
            if ok_ids
            else orm.Fuente.ultima_sincronizacion
        )
        stmt = (
            update(orm.Fuente)
            .where(orm.Fuente.id.in_(list(status_by_id)))
            .values(
                estado=case(status_by_id, value=orm.Fuente.id, else_=orm.Fuente.estado),
                ultima_sincronizacion=new_sync,
            )
        )
        self._s.execute(stmt.execution_options(synchronize_session=False))

    def _upsert_evidences(
        self,
        evidences: list[Evidencia],
        source_ids: dict[str, int],
        fallback: datetime,
    ) -> dict[tuple[str, str], int]:
        """Guarda evidencias por lotes y recupera sus IDs."""

        rows_by_key: dict[tuple[int, str], dict[str, Any]] = {}

        for evidence in evidences:
            if evidence.fuente not in source_ids:
                continue

            source_id = source_ids[evidence.fuente]
            key = (source_id, evidence.id_externo)

            # La última evidencia repetida prevalece.
            rows_by_key[key] = {
                "proyecto_id": evidence.proyecto_id,
                "fuente_id": source_id,
                "id_externo": evidence.id_externo,
                "autor": evidence.autor,
                "fecha": _to_datetime(evidence.fecha, fallback),
                "descripcion": evidence.descripcion or "",
                "estado": getattr(evidence, "estado", None),
                "fecha_limite": getattr(evidence, "fecha_limite", None) or None,
                "tipo_archivo": getattr(evidence, "tipo_archivo", None),
            }

        if not rows_by_key:
            return {}

        source_names = {
            source_id: name
            for name, source_id in source_ids.items()
        }

        evidence_ids: dict[tuple[str, str], int] = {}
        rows = list(rows_by_key.values())
        batch_size = 100

        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]

            statement = insert(orm.Evidencia).values(batch)

            statement = statement.on_conflict_do_update(
                index_elements=["fuente_id", "id_externo"],
                set_={
                    column: statement.excluded[column]
                    for column in (
                        "autor",
                        "fecha",
                        "descripcion",
                        "estado",
                        "fecha_limite",
                        "tipo_archivo",
                    )
                },
            ).returning(
                orm.Evidencia.fuente_id,
                orm.Evidencia.id_externo,
                orm.Evidencia.id,
            )

            for source_id, external_id, row_id in self._s.execute(statement):
                evidence_ids[(source_names[source_id], external_id)] = row_id

        return evidence_ids

    def _upsert_evidence(self, evidence: Evidencia, source_id: int, fallback: datetime) -> int:
        row = insert(orm.Evidencia).values(
            proyecto_id=evidence.proyecto_id,
            fuente_id=source_id,
            id_externo=evidence.id_externo,
            autor=evidence.autor,
            fecha=_to_datetime(evidence.fecha, fallback),
            descripcion=evidence.descripcion or "",
            estado=getattr(evidence, "estado", None),
            fecha_limite=getattr(evidence, "fecha_limite", None) or None,
            tipo_archivo=getattr(evidence, "tipo_archivo", None),
        )
        row = row.on_conflict_do_update(
            index_elements=["fuente_id", "id_externo"],
            set_={column: row.excluded[column] for column in (
                "autor", "fecha", "descripcion", "estado", "fecha_limite", "tipo_archivo")},
        ).returning(orm.Evidencia.id)
        return self._s.execute(row).scalar_one()

    # -- lectura -----------------------------------------------------------
    def obtener(self, proyecto_id: int, fecha_corte: str) -> EstadoSupervision | None:
        """Reconstruye un corte guardado (None si ese día no hubo corte)."""
        day = cutoff_day(fecha_corte)
        indicator = self._s.scalars(
            select(orm.Indicador).where(
                orm.Indicador.proyecto_id == proyecto_id, orm.Indicador.fecha_corte == day
            )
        ).first()
        if indicator is None:
            return None
        return self._build_state(indicator)

    def listar(self, proyecto_id: int) -> list[EstadoSupervision]:
        """Todos los cortes del proyecto, del más antiguo al más reciente."""
        indicators = self._s.scalars(
            select(orm.Indicador)
            .where(orm.Indicador.proyecto_id == proyecto_id)
            .order_by(orm.Indicador.fecha_corte)
        ).all()
        return [self._build_state(row) for row in indicators]

    def history(self, project_id: int) -> list[dict[str, Any]]:
        """Resumen por corte para la ruta /historial: I1–I4, alertas y validación."""
        summary = []
        for state in self.listar(project_id):
            by_rule: dict[str, int] = {}
            for alert in state["alertas"]:
                by_rule[alert["regla"]] = by_rule.get(alert["regla"], 0) + 1
            summary.append({
                "fecha_corte": state["fecha_corte"],
                "indicadores": state["indicadores"],
                "total_alertas": len(state["alertas"]),
                "alertas_por_regla": dict(sorted(by_rule.items())),
                "validacion": self._validation_of_day(project_id, cutoff_day(state["fecha_corte"])),
            })
        return summary

    def _build_state(self, indicator: orm.Indicador) -> EstadoSupervision:
        project_id, day = indicator.proyecto_id, indicator.fecha_corte
        rows = self._s.execute(
            select(orm.Alerta, orm.Evidencia, orm.Fuente.tipo)
            .join(orm.Evidencia, orm.Evidencia.id == orm.Alerta.evidencia_id)
            .join(orm.Fuente, orm.Fuente.id == orm.Evidencia.fuente_id)
            .where(orm.Alerta.proyecto_id == project_id, orm.Alerta.fecha_corte == day)
            .order_by(orm.Alerta.id)
        ).all()
        alerts, evidences = [], {}
        for alert, evidence, kind in rows:
            alerts.append({
                "regla": alert.regla,
                "fuente": kind,
                "evidencia_ids": [evidence.id_externo],
                "explicacion": alert.explicacion,
                "origen_explicacion": alert.origen_explicacion,
            })
            evidences[(kind, evidence.id_externo)] = self._to_domain(evidence, kind)
        sources = dict(self._s.execute(
            select(orm.Fuente.tipo, orm.Fuente.estado).where(orm.Fuente.proyecto_id == project_id)
        ).all())
        return {
            "proyecto_id": project_id,
            "fecha_corte": day.isoformat(),
            # Solo las evidencias que respaldan alertas: el resto puede haber
            # cambiado después del corte (la tabla evidencia guarda la última versión).
            "evidencias": list(evidences.values()),
            # Estado actual de cada fuente: el modelo de TA-004 no lo guarda por corte.
            "estado_fuentes": {
                kind: ("pendiente" if sources.get(kind, "sin_verificar") == "sin_verificar"
                       else sources[kind])
                for kind in SOURCES
            },
            "errores_fuentes": {kind: None for kind in SOURCES},
            "indicadores": {
                "I1": _to_float(indicator.i1_pct_completadas),
                "I2": _to_float(indicator.i2_pct_pendientes),
                "I3": indicator.i3_tareas_vencidas,
                "I4": indicator.i4_dias_sin_actividad,
            },
            "alertas": alerts,
        }

    @staticmethod
    def _to_domain(row: orm.Evidencia, kind: str) -> Evidencia:
        common = dict(
            fuente=kind, id_externo=row.id_externo, autor=row.autor,
            fecha=row.fecha.isoformat(), descripcion=row.descripcion, proyecto_id=row.proyecto_id,
        )
        if kind == "notion":
            return EvidenciaNotion(**common, estado=row.estado,
                                   fecha_limite=row.fecha_limite.isoformat() if row.fecha_limite else None)
        if kind == "drive":
            return EvidenciaDrive(**common, tipo_archivo=row.tipo_archivo)
        return Evidencia(**common)

    def _validation_of_day(self, project_id: int, day: date) -> dict[str, Any] | None:
        """Última validación E2E (TA-021) registrada ese día, si la hubo."""
        row = self._s.scalars(
            select(orm.Validacion)
            .where(
                orm.Validacion.proyecto_id == project_id,
                func.date(func.timezone("America/Lima", orm.Validacion.ejecutada_en)) == day,
            )
            .order_by(orm.Validacion.ejecutada_en.desc())
        ).first()
        if row is None:
            return None
        return {"resultado": row.resultado, "duracion_ms": row.duracion_ms,
                "ejecutada_en": row.ejecutada_en.isoformat()}
