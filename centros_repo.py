from db import get_connection

def fetch_centers():
    sql = "SELECT CenterId, CenterName FROM dbo.DIM_Center ORDER BY CenterId;"
    with get_connection() as cn:
        cur = cn.cursor()
        cur.execute(sql)
        return cur.fetchall()  # lista de tuplas (id, nombre)
