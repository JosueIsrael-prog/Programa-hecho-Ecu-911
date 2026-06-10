import glob
import importlib.util
import logging
import os
import sys

import pandas as pd
from incidentes_repo import incidentes_por_hora

logger = logging.getLogger(__name__)


def _expand_path(path):
    if not path:
        return None
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _candidate_cubo_paths():
    home = os.path.expanduser("~")
    candidates = [
        os.environ.get('CUBO_PATH'),
        os.path.join(os.path.dirname(__file__), "Cubos"),
        os.path.join(os.path.dirname(__file__), "Cubo"),
        os.path.join(home, "OneDrive", "Escritorio", "Cubo", "Cubo"),
        os.path.join(home, "Documents", "Cubo"),
        os.path.join(home, "OneDrive", "Documents", "Cubo"),
        os.path.join(os.path.dirname(__file__), "..", "Cubo"),
        os.path.join(os.path.dirname(__file__), "..", "Cubo", "Cubo"),
        os.path.join(os.path.dirname(__file__), "..", "Cubo", "datos.py"),
    ]
    return [p for p in (_expand_path(candidate) for candidate in candidates) if p]


def _resolve_cubo_module_path():
    for candidate in _candidate_cubo_paths():
        if os.path.isdir(candidate):
            candidate_path = os.path.join(candidate, 'datos.py')
            if os.path.isfile(candidate_path):
                return candidate_path
        elif os.path.isfile(candidate) and os.path.basename(candidate).lower() == 'datos.py':
            return candidate
    return None

CUBE_DATOS_PATH = _resolve_cubo_module_path()


def _load_external_cubo_module():
    if not os.path.exists(CUBE_DATOS_PATH):
        return None

    try:
        cubo_folder = os.path.dirname(CUBE_DATOS_PATH)
        if cubo_folder not in sys.path:
            sys.path.insert(0, cubo_folder)

        spec = importlib.util.spec_from_file_location("datos_cubo", CUBE_DATOS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        logger.warning("No se pudo cargar el módulo de cubo externo '%s': %s", CUBE_DATOS_PATH, exc)
        return None


def _cubo_csv_to_dataframe(csv_path):
    try:
        df_csv = pd.read_csv(csv_path, sep=None, engine='python')
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo: {e}")

    cols_lower = {str(c).lower().strip(): c for c in df_csv.columns}
    
    center_col = None
    for cand in ["centername", "centro", "nombre", "center", "centerid", "nombrecentro"]:
        if cand in cols_lower:
            center_col = cols_lower[cand]
            break
            
    if not center_col:
        raise ValueError(f"No se detectó columna de Centro. Columnas encontradas: {list(df_csv.columns)}")

    hora_col = None
    for cand in ["hora", "hour", "tiempo", "time"]:
        if cand in cols_lower:
            hora_col = cols_lower[cand]
            break

    value_col = None
    for cand in ["conteo", "sumaincidentes", "value", "count", "total", "incidentes", "cantidad"]:
        if cand in cols_lower:
            value_col = cols_lower[cand]
            break

    if hora_col and value_col:
        df = df_csv.pivot_table(
            index=center_col,
            columns=hora_col,
            values=value_col,
            aggfunc="sum",
            fill_value=0,
        )
    else:
        hour_cols = [c for c in df_csv.columns if str(c).isdigit() or (isinstance(c, str) and c.isdigit())]
        if not hour_cols:
            raise ValueError(f"CSV de Cubo no tiene columnas de hora reconocibles. Columnas: {list(df_csv.columns)}")
        df = df_csv.set_index(center_col)[hour_cols]

    for h in range(24):
        if h not in df.columns:
            df[h] = 0

    df = df.reindex(columns=range(24), fill_value=0)
    df = df.sort_index()
    return df


def _find_cubo_base_folders():
    candidates = []
    if CUBE_DATOS_PATH:
        if os.path.isfile(CUBE_DATOS_PATH):
            candidates.append(os.path.dirname(CUBE_DATOS_PATH))
        elif os.path.isdir(CUBE_DATOS_PATH):
            candidates.append(CUBE_DATOS_PATH)

    for path in _candidate_cubo_paths():
        if os.path.isfile(path):
            candidates.append(os.path.dirname(path))
        elif os.path.isdir(path):
            candidates.append(path)

    candidates.extend([
        os.getcwd(),
        os.path.dirname(__file__),
    ])

    normalized = []
    for folder in candidates:
        if not folder:
            continue
        path = os.path.abspath(folder)
        if path not in normalized:
            normalized.append(path)
    return normalized


def _find_cubo_export_csv(fecha):
    candidates = []
    for base in _find_cubo_base_folders():
        for folder in [base, os.path.join(base, "exports", "facts"), os.path.join(base, "exports")]:
            if not os.path.isdir(folder):
                continue
            patterns = [f"*{fecha.replace('-', '_')}*.csv", f"*{fecha.replace('-', '')}*.csv", f"*.csv"]
            for pattern in patterns:
                candidates.extend(glob.glob(os.path.join(folder, pattern)))
            if candidates:
                break
        if candidates:
            break

    return candidates


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

    if isinstance(rows, pd.DataFrame):
        if rows.empty:
            return pd.DataFrame(columns=list(range(24)))
            
        # Si ya viene pivoteado con las horas como columnas numéricas
        if 0 in rows.columns and 23 in rows.columns:
            for h in range(24):
                if h not in rows.columns:
                    rows[h] = 0
            return rows.reindex(columns=range(24), fill_value=0).sort_index()
            
        df = rows.copy()
    else:
        if not rows:
            return pd.DataFrame(columns=list(range(24)))
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
    print("\n=== DEBUG INFO: _rows_for_cubo ===")
    print(f"CUBO_PATH en os.environ: {os.environ.get('CUBO_PATH')}")
    print(f"CUBE_DATOS_PATH resuelto: {CUBE_DATOS_PATH}")
    base_folders = _find_cubo_base_folders()
    print(f"Carpetas base detectadas: {base_folders}")
    for base in base_folders:
        for folder in [base, os.path.join(base, "exports", "facts"), os.path.join(base, "exports")]:
            patterns = [f"*{fecha.replace('-', '_')}*.csv", f"*{fecha.replace('-', '')}*.csv", f"*.csv"]
            print(f" -> Evaluando ruta absoluta: {folder} | ¿Existe directorio?: {os.path.isdir(folder)}")
            print(f"    Patrones CSV a buscar: {patterns}")
    print("==================================\n")

    cubo_mod = _load_external_cubo_module()
    if cubo_mod is None:
        logger.warning(
            f"No se encontró el módulo externo de Cubo en '{CUBE_DATOS_PATH}'. "
            "Se omitirá la conexión directa y se buscarán archivos CSV locales."
        )
    else:
        if hasattr(cubo_mod, "incidentes_por_hora"):
            try:
                return cubo_mod.incidentes_por_hora(fecha, verif)
            except Exception as exc:
                logger.warning("Error ejecutando incidentes_por_hora del Cubo: %s", exc)

        if hasattr(cubo_mod, "obtener_centros_por_hora"):
            try:
                return cubo_mod.obtener_centros_por_hora(*map(int, fecha.split("-")), "todos" if verif is None else ("validos" if verif == 1 else "no_validos"))
            except Exception as exc:
                logger.warning("Error ejecutando obtener_centros_por_hora del Cubo: %s", exc)

    # Intentar cargar CSV de exportación del Cubo si la conexión MDX falla
    csv_files = _find_cubo_export_csv(fecha)
    
    print("\n=== DEBUG: LECTURA DE ARCHIVOS ===")
    print(f"Archivos .csv válidos encontrados: {csv_files}")

    if csv_files:
        for csv_file in csv_files:
            try:
                logger.info("Cargando datos del Cubo desde CSV: %s", csv_file)
                print(f" -> Intentando parsear: {csv_file}")
                df = _cubo_csv_to_dataframe(csv_file)
                print(f" -> ¡Éxito! Datos cargados de: {csv_file}")
                return df
            except Exception as exc:
                logger.warning("No se pudo parsear CSV del Cubo '%s': %s", csv_file, exc)
                print(f" -> [ERROR] Falló lectura de {csv_file}: {exc}")
    else:
        print(" -> No hay archivos CSV que coincidan con la fecha. Contenido de las carpetas:")
        for base in base_folders:
            if os.path.exists(base):
                print(f"    Directorio: {base}")
                try:
                    for f in os.listdir(base)[:10]:
                        print(f"      - {f}")
                except Exception as e:
                    print(f"      [No se pudo listar: {e}]")

    print("\n=== DEBUG CRÍTICO: JUSTO ANTES DEL ERROR ===")
    print(f"CUBO_PATH configurado: {os.environ.get('CUBO_PATH')}")
    print("Carpetas 'exports/facts' exactas que el sistema buscó:")
    for base in _find_cubo_base_folders():
        facts_folder = os.path.join(base, "exports", "facts")
        print(f" -> {facts_folder} | ¿Directorio existe en Windows?: {os.path.isdir(facts_folder)}")
    print(f"Archivos CSV totales encontrados y evaluados: {csv_files}")
    print("==============================================\n")

    logger.warning(
        "No se pudieron obtener datos del Cubo. "
        "Verifica que CUBO_PATH apunte a la carpeta correcta y que el proveedor MSOLAP esté instalado, "
        "o coloca CSV exportados del Cubo en CUBO_PATH/exports/facts/. "
        "FORZANDO DATOS DE BD PARA EL CUBO PARA EVITAR TABLA VACÍA."
    )
    return incidentes_por_hora(fecha, verif)


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
        
        val_cubo = sum(int(row_cubo[h]) for h in range(24))
        val_db = sum(int(row_db[h]) for h in range(24))
        if val_cubo != val_db:
            mismatches.append({
                "Centro": centro,
                "Cubo": val_cubo,
                "DB": val_db,
                "Diferencia": val_cubo - val_db,
            })

    summary = [
        f"Centros Cubo: {len(centers_cubo)}",
        f"Centros BD: {len(centers_db)}",
        f"Faltan en BD: {len(faltan_en_db)}",
        f"Faltan en Cubo: {len(faltan_en_cubo)}",
        f"Diferencias por centro: {len(mismatches)}",
        "Comparación completada.",
    ]

    return {
        "faltan_en_db": faltan_en_db,
        "faltan_en_cubo": faltan_en_cubo,
        "mismatches": mismatches,
        "summary": summary,
    }
