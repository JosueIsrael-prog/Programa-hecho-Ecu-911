# incidentes_repo.py
from db import get_connection

# -----------------------
# utilidades de columnas
# -----------------------
def _columns(schema, table):
    sql = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=? AND TABLE_NAME=?
        ORDER BY ORDINAL_POSITION;
    """
    with get_connection() as cn:
        cur = cn.cursor()
        cur.execute(sql, (schema, table))
        return [(r[0], (r[1] or "").lower()) for r in cur.fetchall()]

def _has_col(schema, table, colname):
    cols = _columns(schema, table)
    return any(c[0].lower() == colname.lower() for c in cols)

def _pick_datetime_col(cols, prefer=("incident", "start", "fecha", "time", "date")):
    dt = {"datetime", "datetime2", "smalldatetime", "date", "datetimeoffset"}
    for k in prefer:
        for name, typ in cols:
            if typ in dt and k in name.lower():
                return name
    for name, typ in cols:
        if typ in dt:
            return name
    return None

def _pick_int_col(cols, keywords=("center", "centro")):
    ints = {"int", "bigint", "smallint", "tinyint"}
    for k in keywords:
        for name, typ in cols:
            if typ in ints and k in name.lower():
                return name
    for name, typ in cols:
        if typ in ints:
            return name
    return None

# -----------------------
# DIM_Verificador (para armar el combo)
# -----------------------
def obtener_opciones_verificador():
    """
    Usamos DIM_Verificador solo para armar las opciones del filtro:
    - Todos
    - Validos (1)
    - No validos (0)

    El filtro REAL se aplica sobre DMH_INCIDENT.StatusIncident.
    """
    with get_connection() as cn:
        cur = cn.cursor()
        cur.execute("""
            SELECT DISTINCT CodVerificador
            FROM dbo.DIM_Verificador;
        """)
        vals = {int(r[0]) for r in cur.fetchall() if r[0] is not None}

    opciones = [("Todos", None)]
    if 1 in vals:
        opciones.append(("Validos (1)", 1))
    if 0 in vals:
        opciones.append(("No validos (0)", 0))

    # por si acaso la tabla está rara:
    if len(opciones) == 1:
        opciones.extend([("Validos (1)", 1), ("No validos (0)", 0)])

    # el primer valor es solo un "nombre" para la UI, no afecta el filtro real
    return ("CodVerificador", opciones)

# -----------------------
# DIM_Fecha (catálogos)
# -----------------------
def _fecha_col_dim():
    cols = _columns("dbo", "DIM_Fecha")
    col = _pick_datetime_col(cols, prefer=("fecha", "date"))
    return col or "Fecha"

def get_anios():
    col = _fecha_col_dim()
    sql = f"SELECT DISTINCT YEAR([{col}]) AS Anio FROM dbo.DIM_Fecha ORDER BY Anio DESC;"
    with get_connection() as cn:
        cur = cn.cursor()
        cur.execute(sql)
        return [r[0] for r in cur.fetchall() if r[0] is not None]

def get_meses(anio: int):
    col = _fecha_col_dim()
    sql = f"""
        SELECT DISTINCT MONTH([{col}]) AS Mes
        FROM dbo.DIM_Fecha
        WHERE YEAR([{col}])=?
        ORDER BY Mes;
    """
    with get_connection() as cn:
        cur = cn.cursor()
        cur.execute(sql, (anio,))
        return [r[0] for r in cur.fetchall() if r[0] is not None]

def get_dias(anio: int, mes: int):
    col = _fecha_col_dim()
    sql = f"""
        SELECT DISTINCT CAST([{col}] AS date) AS Fecha
        FROM dbo.DIM_Fecha
        WHERE YEAR([{col}])=? AND MONTH([{col}])=?
        ORDER BY Fecha;
    """
    with get_connection() as cn:
        cur = cn.cursor()
        cur.execute(sql, (anio, mes))
        return [str(r[0]) for r in cur.fetchall() if r[0] is not None]  # 'YYYY-MM-DD'

# -----------------------
# DMH_INCIDENT (por hora)
# -----------------------
def _fact_cols():
    return _columns("dbo", "DMH_INCIDENT")

def _fact_datetime_col():
    cols = _fact_cols()
    # en tu tabla hay 'starttime' y 'endtime'; prioricemos starttime
    for cand in ("IncidentTime", "starttime", "IncidentDateTime", "FechaIncidente", "endtime"):
        if any(c[0].lower() == cand.lower() for c in cols):
            return cand
    return _pick_datetime_col(
        cols,
        prefer=("incidenttime", "start", "fecha", "incident", "time", "date")
    ) or "starttime"

def _fact_center_col():
    cols = _fact_cols()
    for cand in ("CenterId", "IdCenter", "CentroId"):
        if any(c[0].lower() == cand.lower() for c in cols):
            return cand
    return _pick_int_col(cols, keywords=("center", "centro")) or "CenterId"

def _fact_verif_strategy():
    """
    Ahora el filtro se hace directo sobre StatusIncident:
      - 1 -> "validos"
      - 0 -> "no validos"
    """
    if _has_col("dbo", "DMH_INCIDENT", "StatusIncident"):
        return ("StatusIncident", "direct")
    return (None, "none")

def incidentes_por_hora(fecha_iso: str, verif_val=None):
    """
    Devuelve filas: (CenterId, CenterName, Hora, Conteo)
    - fecha_iso: 'YYYY-MM-DD'
    - verif_val:
        None -> no filtra (todos)  -> 8353
        1    -> StatusIncident = 1 -> 8293
        0    -> StatusIncident = 0 -> 60
    """
    dt_col   = _fact_datetime_col()
    cen_col  = _fact_center_col()
    vcol, modo = _fact_verif_strategy()

    filtro = ""
    params = [fecha_iso]

    if verif_val is not None and vcol and modo == "direct":
        filtro = f" AND f.[{vcol}] = ?"
        params.append(int(verif_val))

    sql = f"""
        SELECT
            c.CenterId,
            c.CenterName,
            DATEPART(hour, f.[{dt_col}]) AS Hora,
            COUNT(*) AS Conteo
        FROM dbo.DMH_INCIDENT f
        JOIN dbo.DIM_Center c ON c.CenterId = f.[{cen_col}]
        WHERE CAST(f.[{dt_col}] AS date) = ?
        {filtro}
        GROUP BY
            c.CenterId,
            c.CenterName,
            DATEPART(hour, f.[{dt_col}])
        ORDER BY
            c.CenterId,
            Hora;
    """

    with get_connection() as cn:
        cur = cn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
