"""Modelo de datos (TA-004): 8 tablas del sistema en PostgreSQL 16.

docente -< proyecto -< integrante
                   -< fuente -< evidencia >- alerta
                   -< indicador
                   -< validacion
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nombres explícitos para todas las restricciones: la migración es reproducible.
CONVENCION_NOMBRES = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)


def _ahora() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Docente(Base):
    """Único usuario directo del MVP (HU-001)."""

    __tablename__ = "docente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # bcrypt
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    creado_en: Mapped[datetime] = _ahora()


class Proyecto(Base):
    """Proyecto académico supervisado (HU-002)."""

    __tablename__ = "proyecto"
    __table_args__ = (
        CheckConstraint("length(btrim(nombre)) > 0", name="nombre_no_vacio"),
        CheckConstraint("fecha_fin >= fecha_inicio", name="fechas_validas"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("docente.id"))
    nombre: Mapped[str] = mapped_column(String(150))
    curso: Mapped[str] = mapped_column(String(100))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    url_publica: Mapped[str] = mapped_column(String(500))
    elemento_verificar: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    creado_en: Mapped[datetime] = _ahora()


class Integrante(Base):
    """Estudiante del equipo. Al menos 1 por proyecto (lo valida la API)."""

    __tablename__ = "integrante"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyecto.id", ondelete="CASCADE")
    )
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str | None] = mapped_column(String(255))


class Fuente(Base):
    """Referencia de una de las 3 fuentes del proyecto (GitHub, Notion, Drive)."""

    __tablename__ = "fuente"
    __table_args__ = (
        UniqueConstraint("proyecto_id", "tipo"),
        CheckConstraint("tipo IN ('github', 'notion', 'drive')", name="tipo_valido"),
        CheckConstraint(
            "estado IN ('sin_verificar', 'ok', 'fallo')", name="estado_valido"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyecto.id", ondelete="CASCADE")
    )
    tipo: Mapped[str] = mapped_column(String(10))
    # URL del repositorio, ID de la base de Notion o ID de la carpeta de Drive
    referencia: Mapped[str] = mapped_column(String(500))
    estado: Mapped[str] = mapped_column(String(15), server_default=text("'sin_verificar'"))
    ultima_sincronizacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )


class Evidencia(Base):
    """Commit, tarea o documento normalizado (esquema común de TA-010).

    Campos comunes: fuente (via fuente_id), id_externo, autor, fecha,
    descripcion y proyecto. estado, fecha_limite y tipo_archivo son atributos
    propios de Notion y Drive; quedan NULL en las demás fuentes.
    """

    __tablename__ = "evidencia"
    __table_args__ = (
        UniqueConstraint("fuente_id", "id_externo"),
        CheckConstraint(
            "estado IS NULL OR estado IN ('Sin empezar', 'En curso', 'Listo')",
            name="estado_valido",
        ),
        Index("ix_evidencia_proyecto_id_fecha", "proyecto_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyecto.id", ondelete="CASCADE")
    )
    fuente_id: Mapped[int] = mapped_column(ForeignKey("fuente.id", ondelete="CASCADE"))
    id_externo: Mapped[str] = mapped_column(String(255))  # SHA, id de página o de archivo
    autor: Mapped[str | None] = mapped_column(String(255))  # NULL: tarea sin responsable
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    descripcion: Mapped[str] = mapped_column(Text)
    estado: Mapped[str | None] = mapped_column(String(12))  # Notion
    fecha_limite: Mapped[date | None] = mapped_column(Date)  # Notion
    tipo_archivo: Mapped[str | None] = mapped_column(String(150))  # Drive


class Indicador(Base):
    """Valores de I1–I4 de un proyecto para una fecha de corte (una fila por corte)."""

    __tablename__ = "indicador"
    __table_args__ = (
        UniqueConstraint("proyecto_id", "fecha_corte"),
        CheckConstraint(
            "i1_pct_completadas BETWEEN 0 AND 100", name="i1_porcentaje"
        ),
        CheckConstraint("i2_pct_pendientes BETWEEN 0 AND 100", name="i2_porcentaje"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyecto.id", ondelete="CASCADE")
    )
    fecha_corte: Mapped[date] = mapped_column(Date)
    # NULL en I1/I2 si el proyecto no tiene tareas; NULL en I4 si no hay actividad
    i1_pct_completadas: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    i2_pct_pendientes: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    i3_tareas_vencidas: Mapped[int] = mapped_column(Integer)
    i4_dias_sin_actividad: Mapped[int | None] = mapped_column(Integer)
    calculado_en: Mapped[datetime] = _ahora()


class Alerta(Base):
    """Alerta R1–R4 con su evidencia de origen (RN-003) y su explicación."""

    __tablename__ = "alerta"
    __table_args__ = (
        UniqueConstraint("proyecto_id", "fecha_corte", "regla", "evidencia_id"),
        CheckConstraint("regla IN ('R1', 'R2', 'R3', 'R4')", name="regla_valida"),
        CheckConstraint(
            "origen_explicacion IN ('gemini', 'plantilla')", name="origen_valido"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyecto.id", ondelete="CASCADE")
    )
    evidencia_id: Mapped[int] = mapped_column(ForeignKey("evidencia.id"))
    regla: Mapped[str] = mapped_column(String(2))
    fecha_corte: Mapped[date] = mapped_column(Date)
    explicacion: Mapped[str] = mapped_column(Text)
    origen_explicacion: Mapped[str] = mapped_column(String(10))  # gemini | plantilla
    creada_en: Mapped[datetime] = _ahora()


class Validacion(Base):
    """Resultado de una ejecución de CP-17 (Playwright en GitHub Actions)."""

    __tablename__ = "validacion"
    __table_args__ = (
        CheckConstraint("resultado IN ('PASS', 'FAIL')", name="resultado_valido"),
        CheckConstraint("duracion_ms >= 0", name="duracion_valida"),
        Index("ix_validacion_proyecto_id_ejecutada_en", "proyecto_id", "ejecutada_en"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(
        ForeignKey("proyecto.id", ondelete="CASCADE")
    )
    resultado: Mapped[str] = mapped_column(String(4))  # PASS | FAIL
    duracion_ms: Mapped[int] = mapped_column(Integer)
    ejecutada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    run_id_actions: Mapped[int] = mapped_column(BigInteger)  # id de la ejecución (RN-003)
    captura_url: Mapped[str | None] = mapped_column(String(500))  # artefacto si FAIL
