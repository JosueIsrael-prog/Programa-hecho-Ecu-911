import os, sys, traceback, csv
from datetime import datetime

# Ensure project root in path
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

from datos import obtener_centros_por_hora, obtener_centros_por_hora_db, comparar_tablas_cubo_vs_db

# Params
FECHA = '2026-03-01'
OUT_DIR = os.path.join(PROJ_ROOT, 'reports')
os.makedirs(OUT_DIR, exist_ok=True)

# Apuntar automáticamente a la carpeta arrastrada si no hay otra configurada
if not os.environ.get('CUBO_PATH'):
    os.environ['CUBO_PATH'] = os.path.join(PROJ_ROOT, "Cubos")

print('Comparing sources for date', FECHA)

try:
    anio, mes, dia = map(int, FECHA.split('-'))
except Exception as e:
    print('Fecha invalida:', FECHA)
    raise

# Load DB
try:
    df_db = obtener_centros_por_hora_db(anio, mes, dia, modo='todos')
    total_db = int(df_db[range(24)].values.sum()) if not df_db.empty else 0
    print('Total BD =', total_db)
except Exception:
    print('Error cargando datos BD:')
    traceback.print_exc()
    df_db = None
    total_db = None

# Load Cubo
try:
    df_cubo = obtener_centros_por_hora(anio, mes, dia, modo='todos')
    total_cubo = int(df_cubo[range(24)].values.sum()) if not df_cubo.empty else 0
    print('Total Cubo =', total_cubo)
except Exception:
    print('No se pudo cargar Cubo via MDX (provider u otros). Intentando buscar CSV exportados...')
    traceback.print_exc()
    df_cubo = None
    total_cubo = None
    # buscar CSV en CUBO_PATH/exports/facts_*
    cubo_path = os.environ.get('CUBO_PATH')
    if cubo_path and os.path.isdir(cubo_path):
        exports_dir = os.path.join(cubo_path, 'exports', 'facts')
        if os.path.isdir(exports_dir):
            print('Buscando CSVs en', exports_dir)
            # try to find a facts CSV matching date
            matches = []
            for fn in os.listdir(exports_dir):
                if fn.lower().endswith('.csv') and FECHA.replace('-', '_') in fn:
                    matches.append(os.path.join(exports_dir, fn))
            if matches:
                # load the first matching CSV into a DataFrame-like structure
                import pandas as pd
                try:
                    df_csv = pd.read_csv(matches[0])
                    print('Cargado CSV de cubo:', matches[0])
                    # attempt to pivot similar to datos._rows_to_dataframe
                    if 'CenterName' in df_csv.columns and 'Hora' in df_csv.columns and 'Conteo' in df_csv.columns:
                        df_cubo = df_csv.pivot_table(index='CenterName', columns='Hora', values='Conteo', aggfunc='sum', fill_value=0)
                        for h in range(24):
                            if h not in df_cubo.columns:
                                df_cubo[h] = 0
                        df_cubo = df_cubo.reindex(columns=range(24), fill_value=0)
                        total_cubo = int(df_cubo[range(24)].values.sum())
                        print('Total Cubo (desde CSV) =', total_cubo)
                except Exception:
                    print('Error cargando CSV de cubo:')
                    traceback.print_exc()

# If we have both frames, compare
if df_cubo is None or df_db is None:
    print('\nNo hay ambos orígenes disponibles para comparar. Acciones sugeridas:')
    print('- Asegúrate de que el proveedor MSOLAP/ADODB esté instalado para consultar el Cubo con MDX.')
    print('- O genera/coloca CSV exportados del Cubo en CUBO_PATH/exports/facts/ con nombres que incluyan la fecha.')
    sys.exit(0)

print('\nEjecutando comparación...')
res = comparar_tablas_cubo_vs_db(df_cubo, df_db)

summary = res.get('summary', [])
print('\nResumen:')
for s in summary:
    print(' -', s)

mismatches = res.get('mismatches', [])
reports_csv = os.path.join(OUT_DIR, f'mismatches_{FECHA}.csv')
with open(reports_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Centro','Cubo','DB','Diferencia'])
    writer.writeheader()
    for m in mismatches:
        writer.writerow({'Centro': m['Centro'], 'Cubo': m['Cubo'], 'DB': m['DB'], 'Diferencia': m['Diferencia']})

print('\nMismatches escritos en', reports_csv)
print('Done')
