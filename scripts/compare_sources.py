import os, sys, traceback

# Asegurar que el directorio padre (proyecto) esté en sys.path para poder
# importar `incidentes_repo`, `datos`, etc.
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

# Ajusta aquí la fecha que quieras comprobar
FECHA = '2026-03-01'
VERIF = None  # None todos, or 1, or 0

# Ruta del Cubo local (ajusta si tu carpeta es distinta)
os.environ['CUBO_PATH'] = r"C:\Users\DNAD\OneDrive\Escritorio\Cubo\Cubo"

# Asegurar que el path del cubo esté en sys.path
cubo_path = os.environ.get('CUBO_PATH')
if cubo_path and os.path.isdir(cubo_path):
    if cubo_path not in sys.path:
        sys.path.insert(0, cubo_path)

print('Using CUBO_PATH=', cubo_path)

try:
    # BD (incidentes_repo.incidentes_por_hora)
    from incidentes_repo import incidentes_por_hora
    rows = incidentes_por_hora(FECHA, VERIF)
    print('\nBD rows returned:', len(rows))
    total_bd = 0
    per_center_bd = {}
    for cid, cname, hora, cnt in rows:
        key = (cid, cname)
        per_center_bd.setdefault(key, [0]*24)
        if hora is not None:
            try:
                h = int(hora)
                per_center_bd[key][h] += int(cnt or 0)
            except Exception:
                pass
    for key, vec in per_center_bd.items():
        total_bd += sum(vec)
    print('Total general BD:', total_bd)
    # show top centers
    top_bd = sorted(((sum(v), k) for k, v in per_center_bd.items()), reverse=True)[:10]
    print('\nTop BD centers (total, (id,name)):')
    for s, k in top_bd:
        print(s, k)

except Exception as e:
    print('Error loading BD data:')
    traceback.print_exc()

try:
    # Cubo (datos.obtener_centros_por_hora)
    from datos import obtener_centros_por_hora
    anio, mes, dia = map(int, FECHA.split('-'))
    df = obtener_centros_por_hora(anio, mes, dia, 'todos')
    print('\nCubo df shape:', getattr(df, 'shape', 'no df'))
    # compute total by summing all numeric columns 0..23
    total_cubo = 0
    per_center_cubo = {}
    if df is not None:
        # df may have hours as columns; iterate
        for centro, row in df.iterrows():
            s = 0
            for h in range(24):
                try:
                    s += int(row.get(h, 0))
                except Exception:
                    pass
            per_center_cubo[centro] = s
            total_cubo += s
    print('Total general Cubo:', total_cubo)
    top_cubo = sorted(((v, k) for k, v in per_center_cubo.items()), reverse=True)[:10]
    print('\nTop Cubo centers (total, name):')
    for s, k in top_cubo:
        print(s, k)

except Exception as e:
    print('Error loading Cubo data:')
    traceback.print_exc()

# Compare totals
try:
    print('\nDifference (Cubo - BD):', total_cubo - total_bd)
except Exception:
    pass

print('\nDone')
