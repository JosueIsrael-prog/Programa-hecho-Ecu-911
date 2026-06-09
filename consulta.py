from db import get_connection  # usa la misma conexión que tu app

FECHA = "2025-11-17"  # <<< cambia aquí la fecha que quieras probar


def main():
    with get_connection() as cn:
        cur = cn.cursor()

        print(f"=== Fecha: {FECHA} ===\n")

        # A) Filas totales en DMH_INCIDENT
        cur.execute("""
            SELECT COUNT(*)
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
        """, FECHA)
        filas_total = cur.fetchone()[0]
        print("A) Filas totales (COUNT *):", filas_total)

        # B) Filas 'validas' según la misma regla que usa tu programa
        case_expr = """
            CASE
              WHEN COALESCE(InvalidIncidentNewTypeId,0)=0
               AND COALESCE(INVALIDINCIDENTTYPEID,0)=0
              THEN 1 ELSE 0
            END
        """
        cur.execute(f"""
            SELECT COUNT(*)
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
              AND {case_expr} = 1
        """, FECHA)
        filas_validas = cur.fetchone()[0]
        print("B) Filas validas (CASE=1):", filas_validas)

        # C) Incidentes distintos por IncidentInformationId
        cur.execute("""
            SELECT COUNT(DISTINCT IncidentInformationId)
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
        """, FECHA)
        dist_info = cur.fetchone()[0]
        print("C) Distintos IncidentInformationId:", dist_info)

        # D) Incidentes distintos por IncidentNumber
        cur.execute("""
            SELECT COUNT(DISTINCT IncidentNumber)
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
        """, FECHA)
        dist_number = cur.fetchone()[0]
        print("D) Distintos IncidentNumber:", dist_number)


if __name__ == "__main__":
    main()
