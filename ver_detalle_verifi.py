from db import get_connection

# Pon aquí la fecha que estás analizando
FECHA = "2025-11-17"   # <-- cámbiala si quieres


def main():
    with get_connection() as cn:
        cur = cn.cursor()

        # 1) Ver todo lo que hay en DIM_Verificador
        print("=== Contenido de DIM_Verificador ===\n")
        cur.execute("""
            SELECT CodVerificador, Descripcion
            FROM dbo.DIM_Verificador
            ORDER BY CodVerificador;
        """)
        rows = cur.fetchall()
        if not rows:
            print("DIM_Verificador está vacía o no devolvió filas.")
        else:
            for cod, desc in rows:
                print(f"CodVerificador={cod} | Descripcion={desc}")
        print("\n")

        # 2) Valores distintos de InvalidIncidentNewTypeId para la fecha
        print(f"=== InvalidIncidentNewTypeId en DMH_INCIDENT para {FECHA} ===\n")
        cur.execute("""
            SELECT
                InvalidIncidentNewTypeId,
                COUNT(*) AS Conteo
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
            GROUP BY InvalidIncidentNewTypeId
            ORDER BY Conteo DESC;
        """, FECHA)
        rows = cur.fetchall()
        if not rows:
            print("No hay filas en DMH_INCIDENT para esa fecha.")
        else:
            for invalid_new, cnt in rows:
                print(f"InvalidIncidentNewTypeId={invalid_new} -> {cnt} filas")
        print("\n")

        # 3) Valores distintos de INVALIDINCIDENTTYPEID para la fecha
        print(f"=== INVALIDINCIDENTTYPEID en DMH_INCIDENT para {FECHA} ===\n")
        cur.execute("""
            SELECT
                INVALIDINCIDENTTYPEID,
                COUNT(*) AS Conteo
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
            GROUP BY INVALIDINCIDENTTYPEID
            ORDER BY Conteo DESC;
        """, FECHA)
        rows = cur.fetchall()
        if not rows:
            print("No hay filas en DMH_INCIDENT para esa fecha.")
        else:
            for invalid_old, cnt in rows:
                print(f"INVALIDINCIDENTTYPEID={invalid_old} -> {cnt} filas")
        print("\n")

        # 4) Valores distintos de IncidentNewTypeId para la fecha
        print(f"=== IncidentNewTypeId en DMH_INCIDENT para {FECHA} ===\n")
        cur.execute("""
            SELECT
                IncidentNewTypeId,
                COUNT(*) AS Conteo
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
            GROUP BY IncidentNewTypeId
            ORDER BY Conteo DESC;
        """, FECHA)
        rows = cur.fetchall()
        if not rows:
            print("No hay filas en DMH_INCIDENT para esa fecha.")
        else:
            for inc_new, cnt in rows:
                print(f"IncidentNewTypeId={inc_new} -> {cnt} filas")
        print("\n")

        # 5) Valores distintos de IncidentTypeId para la fecha
        print(f"=== IncidentTypeId en DMH_INCIDENT para {FECHA} ===\n")
        cur.execute("""
            SELECT
                IncidentTypeId,
                COUNT(*) AS Conteo
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
            GROUP BY IncidentTypeId
            ORDER BY Conteo DESC;
        """, FECHA)
        rows = cur.fetchall()
        if not rows:
            print("No hay filas en DMH_INCIDENT para esa fecha.")
        else:
            for inc_type, cnt in rows:
                print(f"IncidentTypeId={inc_type} -> {cnt} filas")


if __name__ == "__main__":
    main()
