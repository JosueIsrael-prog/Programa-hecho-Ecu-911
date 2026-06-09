import importlib.util
import logging
import os

import pandas as pd
from incidentes_repo import incidentes_por_hora

logger = logging.getLogger(__name__)
CUBE_DATOS_PATH = None

# Determinar la ruta al módulo de datos del Cubo: usar la variable de
# entorno `CUBO_PATH` (puede ser carpeta o ruta completa al archivo datos.py),
# y si no existe usar la ruta por defecto que había en el proyecto.
cubo_env = os.environ.get('CUBO_PATH')
if cubo_env:
    if os.path.isdir(cubo_env):
        CUBE_DATOS_PATH = os.path.join(cubo_env, 'datos.py')
    else:
        CUBE_DATOS_PATH = cubo_env
else:
    CUBE_DATOS_PATH = r"c:\Users\MONICA.ROJAS\Documents\Cubo\datos.py"


def _load_external_cubo_module():
    if not os.path.exists(CUBE_DATOS_PATH):
        return None

    try:
        spec = importlib.util.spec_from_file_location("datos_cubo", CUBE_DATOS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        logger.warning("No se pudo cargar el módulo de cubo externo '%s': %s", CUBE_DATOS_PATH, exc)
        return None


def _modo_to_verif(modo):
    if modo == "validos":
        return 1
    if modo == "no_validos":
        return 0
    return None


def _normalize_rows(rows):
    def _is_sequence(obj):
        return (
            hasattr(obj, "__len__")
            and hasattr(obj, "__getitem__")
            and not isinstance(obj, (str, bytes, dict, pd.Series))
        )

    if rows is None:
        return []

    if hasattr(rows, "fetchall"):
        rows = rows.fetchall()

    if isinstance(rows, pd.DataFrame):
        return rows

    if _is_sequence(rows):
        if not rows:
            return []

        if len(rows) == 4 and all(not _is_sequence(x) for x in rows):
            return [tuple(rows)]

        if len(rows) == 1:
            first = rows[0]
            if _is_sequence(first) and len(first) == 4:
                return [tuple(first)]
            if isinstance(first, dict):
                return [(first.get("CenterId"), first.get("CenterName"), first.get("Hora"), first.get("Conteo"))]

    rows = list(rows)
    if not rows:
        return []

    normalized = []
    for r in rows:
        if isinstance(r, dict):
            normalized.append((r.get("CenterId"), r.get("CenterName"), r.get("Hora"), r.get("Conteo")))
            continue

        if _is_sequence(r):
            if len(r) == 1:
                inner = r[0]
                if _is_sequence(inner):
                    normalized.append(tuple(inner))
                    continue
            normalized.append(tuple(r))
            continue

        normalized.append((r,))

    return normalized


def _rows_to_dataframe(rows):
    rows = _normalize_rows(rows)
    if not rows:
        return pd.DataFrame(columns=list(range(24)))

    if isinstance(rows, pd.DataFrame):
        df = rows.copy()
    else:
        df = pd.DataFrame.from_records(rows, columns=["CenterId", "CenterName", "Hora", "Conteo"])

    df["Hora"] = df["Hora"].fillna(0).astype(int)
    df["Conteo"] = df["Conteo"].fillna(0).astype(int)

    df = df.pivot_table(
        index="CenterName",
        columns="Hora",
        values="Conteo",
        aggfunc="sum",
        fill_value=0,
    )

    # Asegurar columnas 0..23
    for h in range(24):
        if h not in df.columns:
            df[h] = 0

    df = df.reindex(columns=range(24), fill_value=0)
    df = df.sort_index()
    return df


def _rows_for_cubo(fecha, verif):
    cubo_mod = _load_external_cubo_module()
    if cubo_mod is None:
        raise FileNotFoundError(
            f"No se encontró el módulo externo de Cubo en '{CUBE_DATOS_PATH}'. "
            "Define la variable de entorno CUBO_PATH apuntando a la carpeta o al archivo datos.py del Cubo."
        )

    if not hasattr(cubo_mod, "incidentes_por_hora"):
        raise AttributeError(
            f"El módulo del Cubo cargado desde '{CUBE_DATOS_PATH}' no tiene la función incidentes_por_hora."
        )

    return cubo_mod.incidentes_por_hora(fecha, verif)


def obtener_centros_por_hora(anio, mes, dia, modo="todos"):
    """Carga datos del Cubo."""
    fecha = f"{anio:04d}-{mes:02d}-{dia:02d}"
    verif = _modo_to_verif(modo)
    rows = _rows_for_cubo(fecha, verif)
    return _rows_to_dataframe(rows)


def obtener_centros_por_hora_db(anio, mes, dia, modo="todos"):
    """Carga datos directamente de la BD."""
    fecha = f"{anio:04d}-{mes:02d}-{dia:02d}"
    verif = _modo_to_verif(modo)
    rows = incidentes_por_hora(fecha, verif)
    return _rows_to_dataframe(rows)


def comparar_tablas_cubo_vs_db(df_cubo, df_db):
    df_cubo = df_cubo.copy()
    df_db = df_db.copy()

    for h in range(24):
        if h not in df_cubo.columns:
            df_cubo[h] = 0
        if h not in df_db.columns:
            df_db[h] = 0

    df_cubo = df_cubo.reindex(columns=range(24), fill_value=0)
    df_db = df_db.reindex(columns=range(24), fill_value=0)

    centers_cubo = set(df_cubo.index)
    centers_db = set(df_db.index)

    faltan_en_db = sorted(centers_cubo - centers_db)
    faltan_en_cubo = sorted(centers_db - centers_cubo)

    mismatches = []
    for centro in sorted(centers_cubo & centers_db):
        row_cubo = df_cubo.loc[centro]
        row_db = df_db.loc[centro]
        for h in range(24):
            val_cubo = int(row_cubo[h])
            val_db = int(row_db[h])
            if val_cubo != val_db:
                mismatches.append({
                    "Centro": centro,
                    "Hora": h,
                    "Cubo": val_cubo,
                    "DB": val_db,
                    "Diferencia": val_cubo - val_db,
                })

    summary = [
        f"Centros Cubo: {len(centers_cubo)}",
        f"Centros BD: {len(centers_db)}",
        f"Faltan en BD: {len(faltan_en_db)}",
        f"Faltan en Cubo: {len(faltan_en_cubo)}",
        f"Diferencias horarias: {len(mismatches)}",
        "Comparación completada.",
    ]

    return {
        "faltan_en_db": faltan_en_db,
        "faltan_en_cubo": faltan_en_cubo,
        "mismatches": mismatches,
        "summary": summary,
    }
