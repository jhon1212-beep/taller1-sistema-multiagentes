/**
 * HU-006 / HU-007 · Datos de supervisión (indicadores I1–I4 y alertas R1–R4).
 * Generado por backend/scripts/generar_demo_supervision.py con el motor de TA-019
 * sobre el dataset de TA-017; no editar a mano. Se reemplaza por la API en TA-040.
 */

export const FECHA_CORTE = "2026-10-13T04:59:59Z"

export const DESCRIPCION_REGLAS = {
  "R1": "Tarea no completada con fecha limite anterior al corte.",
  "R2": "Tarea en curso sin ediciones durante mas de 7 dias.",
  "R3": "Repositorio sin commits en los 7 dias previos al corte.",
  "R4": "Carpeta sin documentos modificados en los 14 dias previos al corte."
}

export const SUPERVISION_DEMO = {
  "1": {
    "nombre": "Seguimiento académico",
    "indicadores": {
      "I1": 40.0,
      "I2": 60.0,
      "I3": 4,
      "I4": 0
    },
    "detalle": {
      "tareas_total": 20,
      "tareas_listas": 8,
      "ultima_actividad": "2026-10-12T09:00:00Z",
      "evidencias": {
        "github": 20,
        "notion": 20,
        "drive": 10
      }
    },
    "alertas": [
      {
        "id": "R1-tarea-p1-09",
        "regla": "R1",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p1-09"
        ],
        "explicacion": "Regla R1: Tarea no completada con fecha limite anterior al corte. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p1-09.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p1-09",
          "responsable": "Ana Torres",
          "fecha": "2026-10-02T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Consulta de tareas · 9",
          "estado": "En curso",
          "fecha_limite": "2026-10-07"
        }
      },
      {
        "id": "R1-tarea-p1-12",
        "regla": "R1",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p1-12"
        ],
        "explicacion": "Regla R1: Tarea no completada con fecha limite anterior al corte. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p1-12.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p1-12",
          "responsable": "Diego Paz",
          "fecha": "2026-10-10T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Registro de proyecto · 12",
          "estado": "En curso",
          "fecha_limite": "2026-10-09"
        }
      },
      {
        "id": "R1-tarea-p1-15",
        "regla": "R1",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p1-15"
        ],
        "explicacion": "Regla R1: Tarea no completada con fecha limite anterior al corte. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p1-15.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p1-15",
          "responsable": "Marta Ruiz",
          "fecha": "2026-09-28T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Pruebas de integración · 15",
          "estado": "Sin empezar",
          "fecha_limite": "2026-10-08"
        }
      },
      {
        "id": "R1-tarea-p1-16",
        "regla": "R1",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p1-16"
        ],
        "explicacion": "Regla R1: Tarea no completada con fecha limite anterior al corte. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p1-16.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p1-16",
          "responsable": "Diego Paz",
          "fecha": "2026-09-29T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Inicio de sesión docente · 16",
          "estado": "Sin empezar",
          "fecha_limite": "2026-10-10"
        }
      },
      {
        "id": "R2-tarea-p1-09",
        "regla": "R2",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p1-09"
        ],
        "explicacion": "Regla R2: Tarea en curso sin ediciones durante mas de 7 dias. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p1-09.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p1-09",
          "responsable": "Ana Torres",
          "fecha": "2026-10-02T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Consulta de tareas · 9",
          "estado": "En curso",
          "fecha_limite": "2026-10-07"
        }
      },
      {
        "id": "R2-tarea-p1-10",
        "regla": "R2",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p1-10"
        ],
        "explicacion": "Regla R2: Tarea en curso sin ediciones durante mas de 7 dias. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p1-10.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p1-10",
          "responsable": "Luis Vega",
          "fecha": "2026-10-03T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Pruebas de integración · 10",
          "estado": "En curso",
          "fecha_limite": "2026-10-20"
        }
      }
    ]
  },
  "2": {
    "nombre": "Biblioteca digital",
    "indicadores": {
      "I1": 37.5,
      "I2": 62.5,
      "I3": 2,
      "I4": 7
    },
    "detalle": {
      "tareas_total": 8,
      "tareas_listas": 3,
      "ultima_actividad": "2026-10-05T09:00:00Z",
      "evidencias": {
        "github": 12,
        "notion": 8,
        "drive": 6
      }
    },
    "alertas": [
      {
        "id": "R1-tarea-p2-04",
        "regla": "R1",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p2-04"
        ],
        "explicacion": "Regla R1: Tarea no completada con fecha limite anterior al corte. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p2-04.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p2-04",
          "responsable": "Carlos León",
          "fecha": "2026-09-27T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Módulo de catálogo · 4",
          "estado": "En curso",
          "fecha_limite": "2026-10-04"
        }
      },
      {
        "id": "R1-tarea-p2-07",
        "regla": "R1",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p2-07"
        ],
        "explicacion": "Regla R1: Tarea no completada con fecha limite anterior al corte. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p2-07.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p2-07",
          "responsable": "Elena Ríos",
          "fecha": "2026-09-26T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Módulo de catálogo · 7",
          "estado": "Sin empezar",
          "fecha_limite": "2026-10-03"
        }
      },
      {
        "id": "R2-tarea-p2-04",
        "regla": "R2",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p2-04"
        ],
        "explicacion": "Regla R2: Tarea en curso sin ediciones durante mas de 7 dias. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p2-04.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p2-04",
          "responsable": "Carlos León",
          "fecha": "2026-09-27T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Módulo de catálogo · 4",
          "estado": "En curso",
          "fecha_limite": "2026-10-04"
        }
      },
      {
        "id": "R2-tarea-p2-05",
        "regla": "R2",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p2-05"
        ],
        "explicacion": "Regla R2: Tarea en curso sin ediciones durante mas de 7 dias. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p2-05.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p2-05",
          "responsable": "Elena Ríos",
          "fecha": "2026-09-28T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Módulo de catálogo · 5",
          "estado": "En curso",
          "fecha_limite": "2026-10-30"
        }
      },
      {
        "id": "R2-tarea-p2-06",
        "regla": "R2",
        "fuente": "notion",
        "evidencia_ids": [
          "tarea-p2-06"
        ],
        "explicacion": "Regla R2: Tarea en curso sin ediciones durante mas de 7 dias. Fuente: notion. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: tarea-p2-06.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "tarea-p2-06",
          "responsable": "Carlos León",
          "fecha": "2026-10-02T15:00:00Z",
          "tipo": "tarea",
          "titulo": "Módulo de catálogo · 6",
          "estado": "En curso",
          "fecha_limite": "2026-10-31"
        }
      },
      {
        "id": "R3-31f68efa64c1",
        "regla": "R3",
        "fuente": "github",
        "evidencia_ids": [
          "31f68efa64c129a123afda04f2f1c97aa737cc46"
        ],
        "explicacion": "Regla R3: Repositorio sin commits en los 7 dias previos al corte. Fuente: github. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: 31f68efa64c129a123afda04f2f1c97aa737cc46.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "31f68efa64c129a123afda04f2f1c97aa737cc46",
          "responsable": "Carlos León",
          "fecha": "2026-10-05T09:00:00Z",
          "tipo": "commit",
          "titulo": "Mostrar tareas por proyecto",
          "sha": "31f68ef"
        }
      },
      {
        "id": "R4-archivo-p2-0",
        "regla": "R4",
        "fuente": "drive",
        "evidencia_ids": [
          "archivo-p2-06"
        ],
        "explicacion": "Regla R4: Carpeta sin documentos modificados en los 14 dias previos al corte. Fuente: drive. Fecha de corte: 2026-10-13T04:59:59Z. Referencias de evidencia: archivo-p2-06.",
        "origen_explicacion": "plantilla",
        "evidencia": {
          "id": "archivo-p2-06",
          "responsable": "Carlos León",
          "fecha": "2026-09-25T13:00:00Z",
          "tipo": "documento",
          "titulo": "Plan del proyecto · 6",
          "tipo_archivo": "application/vnd.google-apps.document"
        }
      }
    ]
  }
}
