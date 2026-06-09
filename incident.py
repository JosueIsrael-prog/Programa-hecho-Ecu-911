from db import get_connection

FECHA = "2025-11-17"  

def main():
    with get_connection() as cn:
        cur = cn.cursor()

        print(f"=== Valores de InvalidIncidentNewTypeId / INVALIDINCIDENTTYPEID para {FECHA} ===\n")

        
        cur.execute("""
            SELECT
                COALESCE(InvalidIncidentNewTypeId, 0)      AS InvalidNew,
                COALESCE(INVALIDINCIDENTTYPEID, 0)         AS InvalidOld,
                COUNT(*) AS Conteo
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
            GROUP BY
                COALESCE(InvalidIncidentNewTypeId, 0),
                COALESCE(INVALIDINCIDENTTYPEID, 0)
            ORDER BY Conteo DESC;
        """, FECHA)

        rows = cur.fetchall()
        for invalid_new, invalid_old, cnt in rows:
            print(f"InvalidNew={invalid_new} | InvalidOld={invalid_old} -> {cnt} filas")

if __name__ == "__main__":
    main()
