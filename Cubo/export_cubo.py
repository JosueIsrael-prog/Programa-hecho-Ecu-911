import os
import csv
import traceback
from pathlib import Path
import pandas as pd

try:
    from cuboconexion import open_connection
except Exception:
    # si se ejecuta desde fuera, intentar ruta relativa
    from Cubo.cuboconexion import open_connection

import win32com.client
import zipfile


def execute_mdx(mdx: str):
    conn = open_connection()

    cmd = win32com.client.Dispatch("ADODB.Command")
    cmd.ActiveConnection = conn
    cmd.CommandText = mdx

    result = cmd.Execute()
    rs = result[0] if isinstance(result, tuple) else result

    if rs is None:
        conn.Close()
        return []

    field_names = [rs.Fields.Item(i).Name for i in range(rs.Fields.Count)]
    rows = []
    while not rs.EOF:
        values = [rs.Fields.Item(i).Value for i in range(rs.Fields.Count)]
        rows.append(dict(zip(field_names, values)))
        rs.MoveNext()

    rs.Close()
    conn.Close()
    return rows


def dump_query_to_csv(rows, out_path):
    if not rows:
        return
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def dump_metadata(out_dir="exports"):
    print("Extrayendo metadata (dimensiones, jerarquias, niveles, medidas)...")
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # dimensiones
    rows = execute_mdx("SELECT * FROM $system.MDSCHEMA_DIMENSIONS")
    dump_query_to_csv(rows, os.path.join(out_dir, "dimensions.csv"))

    # jerarquias
    rows = execute_mdx("SELECT * FROM $system.MDSCHEMA_HIERARCHIES")
    dump_query_to_csv(rows, os.path.join(out_dir, "hierarchies.csv"))

    # niveles
    rows = execute_mdx("SELECT * FROM $system.MDSCHEMA_LEVELS")
    dump_query_to_csv(rows, os.path.join(out_dir, "levels.csv"))

    # medidas
    rows = execute_mdx("SELECT * FROM $system.MDSCHEMA_MEASURES")
    dump_query_to_csv(rows, os.path.join(out_dir, "measures.csv"))

    print("Metadata exportada en:", out_dir)


def dump_members_for_levels(out_dir="exports", max_per_level=0):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    print("Extrayendo miembros por nivel (usar max_per_level>0 para limitar)...")

    levels = execute_mdx("SELECT * FROM $system.MDSCHEMA_LEVELS")

    # Lista de niveles con demasiados miembros para exportar, que causan timeouts.
    # Estos son generalmente campos de hechos (IDs, fecha/hora, coordenadas) que no se
    # deben tratar como jerarquías para explorar.
    niveles_a_omitir = {
        "[DMH_INCIDENT].[endtime].[endtime]",
        "[DMH_INCIDENT].[IncidentInformationId].[IncidentInformationId]",
        "[DMH_INCIDENT].[IncidentNumber].[IncidentNumber]",
        "[DMH_INCIDENT].[latitud].[latitud]",
        "[DMH_INCIDENT].[longitud].[longitud]",
        "[DMH_INCIDENT].[starttime].[starttime]",
    }

    for lvl in levels:
        try:
            cube = lvl.get("CUBE_NAME")
            level_unique = lvl.get("LEVEL_UNIQUE_NAME")
            level_caption = lvl.get("LEVEL_CAPTION") or lvl.get("LEVEL_UNIQUE_NAME")
            if cube != "Modelo" or not level_unique:
                continue

            if level_unique in niveles_a_omitir:
                print(f"  -> Omitiendo nivel de alta cardinalidad: {level_caption}")
                continue

            safe_name = level_unique.replace("[", "").replace("]", "_").replace(".", "_")
            out_path = os.path.join(out_dir, f"members_{safe_name}.csv")

            mdx = f"""
            SELECT
              {{ [Measures].[SumaIncidentes] }} ON COLUMNS,
              {level_unique}.MEMBERS DIMENSION PROPERTIES MEMBER_UNIQUE_NAME, MEMBER_CAPTION
              ON ROWS
            FROM [Modelo]
            """

            rows = execute_mdx(mdx)
            if max_per_level and len(rows) > max_per_level:
                rows = rows[:max_per_level]

            dump_query_to_csv(rows, out_path)
            print(f"  -> {level_caption} -> {out_path} (rows: {len(rows)})")
        except Exception:
            traceback.print_exc()


def dump_facts_by_date(out_dir="exports/facts", date_level_hint="fechad", limit_dates=0, combine=False):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    print("Extrayendo hechos por fecha (puede tardar; usa limit_dates para limitar)...")

    # 1) localizar nivel de fecha más detallado
    levels = execute_mdx("SELECT * FROM $system.MDSCHEMA_LEVELS")
    date_levels = [l for l in levels if l.get("DIMENSION_UNIQUE_NAME") == "[Fecha]"]

    target_level = None
    for l in date_levels:
        if l.get("LEVEL_UNIQUE_NAME") and date_level_hint.lower() in str(l.get("LEVEL_UNIQUE_NAME")).lower():
            target_level = l
            break

    if not target_level and date_levels:
        # pick the deepest level (max LEVEL_NUMBER)
        target_level = max(date_levels, key=lambda x: x.get("LEVEL_NUMBER") or 0)

    if not target_level:
        print("No se encontro un nivel de fecha. Abortando dump de hechos.")
        return

    level_unique = target_level.get("LEVEL_UNIQUE_NAME")
    print("Usando nivel de fecha:", level_unique)

    # 2) obtener miembros de fecha
    mdx_members = f"SELECT {{ [Measures].[SumaIncidentes] }} ON COLUMNS, {level_unique}.MEMBERS DIMENSION PROPERTIES MEMBER_UNIQUE_NAME, MEMBER_CAPTION ON ROWS FROM [Modelo]"
    date_rows = execute_mdx(mdx_members)
    if not date_rows:
        print("No se obtuvieron miembros de fecha.")
        return

    if limit_dates and len(date_rows) > limit_dates:
        date_rows = date_rows[:limit_dates]

    combined_rows = [] if combine else None

    # 3) para cada fecha, pedir crossjoin Center x Hour
    for dr in date_rows:
        date_member = dr.get(next(k for k in dr.keys() if "UNIQUE_NAME" in k))
        date_caption = dr.get(next((k for k in dr.keys() if "MEMBER_CAPTION" in k), None))
        if not date_member:
            continue

        safe_date = str(date_member).replace("[", "").replace("]", "_").replace(".", "_")
        out_path = os.path.join(out_dir, f"facts_{safe_date}.csv")

        mdx = f"""
        SELECT
          {{ [Measures].[SumaIncidentes] }} ON COLUMNS,
          NON EMPTY
            CrossJoin([Center].[CenterName].[CenterName].Members, [HoraMinSec].[Horas].[Hour].Members)
          DIMENSION PROPERTIES MEMBER_UNIQUE_NAME, MEMBER_CAPTION ON ROWS
        FROM [Modelo]
        WHERE ( {date_member} )
        """

        rows = execute_mdx(mdx)
        # añadir campo fecha en cada fila
        for r in rows:
            r["date_unique_name"] = date_member
            r["date_caption"] = date_caption

        dump_query_to_csv(rows, out_path)
        print(f"  -> fecha {date_caption} -> {out_path} rows: {len(rows)}")

        if combine:
            combined_rows.extend(rows)

    if combine:
        combined_path = os.path.join(Path(out_dir).parent, "facts_combined.csv")
        print(f"Guardando facts combinados en {combined_path} (rows: {len(combined_rows)})")
        dump_query_to_csv(combined_rows, combined_path)
        return combined_path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="exports", help="Directorio de salida")
    parser.add_argument("--max-members", type=int, default=0, help="Limitar miembros por nivel (0 = ilimitado)")
    parser.add_argument("--dump-facts", action="store_true", help="Volcar hechos por fecha (potencialmente pesado)")
    parser.add_argument("--limit-dates", type=int, default=0, help="Limitar numero de fechas a extraer para hechos")
    parser.add_argument("--combine-facts", action="store_true", help="Guardar un solo CSV combinado con todos los hechos")
    parser.add_argument("--zip", action="store_true", help="Comprimir el directorio de salida en un ZIP al finalizar")
    args = parser.parse_args()

    try:
        dump_metadata(args.out)
        dump_members_for_levels(args.out, max_per_level=args.max_members)
        combined_path = None
        if args.dump_facts:
            combined_path = dump_facts_by_date(os.path.join(args.out, "facts"), limit_dates=args.limit_dates, combine=args.combine_facts)

        if args.zip:
            zip_path = os.path.join(args.out + ".zip")
            print(f"Comprimiendo {args.out} -> {zip_path} ...")
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(args.out):
                    for f in files:
                        full = os.path.join(root, f)
                        arcname = os.path.relpath(full, start=os.path.dirname(args.out))
                        zf.write(full, arcname)
            print("ZIP creado:", zip_path)
    except Exception as e:
        print("Error:")
        print(e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
