from db import get_connection

TABLAS = [
    ("dbo","DIM_Center"),
    ("dbo","DIM_Fecha"),
    ("dbo","DIM_Verificador"),
    ("dbo","DMH_INCIDENT"),
    ("dbo", "DMH_LLAMADAS"),
    ("dbo","DIM_Servicio"),
    ("dbo","DIM_Mes"),
    ("dbo", "DIM_Hora")
]

with get_connection() as cn:
    cur = cn.cursor()
    for sch, tbl in TABLAS:
        print(f"\n== {sch}.{tbl} ==")
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA=? AND TABLE_NAME=?
            ORDER BY ORDINAL_POSITION;
        """, (sch,tbl))
        for name, dtype in cur.fetchall():
            print(f" - {name:30s} {dtype}")
