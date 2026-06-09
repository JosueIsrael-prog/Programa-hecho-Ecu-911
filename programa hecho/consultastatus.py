from db import get_connection

FECHA = "2025-11-17"  # misma fecha

def main():
    with get_connection() as cn:
        cur = cn.cursor()

        print(f"=== Fecha: {FECHA} ===\n")

        # Conteo por StatusIncident
        cur.execute("""
            SELECT StatusIncident, COUNT(*) AS Conteo
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
            GROUP BY StatusIncident
            ORDER BY StatusIncident;
        """, FECHA)
        print("Por StatusIncident:")
        for status, cnt in cur.fetchall():
            print(f"  Status {status}: {cnt}")

        print()

        # Conteo por IncidentDisposalTypeId (por si acaso)
        cur.execute("""
            SELECT IncidentDisposalTypeId, COUNT(*) AS Conteo
            FROM dbo.DMH_INCIDENT
            WHERE CAST(starttime AS date) = ?
            GROUP BY IncidentDisposalTypeId
            ORDER BY IncidentDisposalTypeId;
        """, FECHA)
        print("Por IncidentDisposalTypeId:")
        for dispo, cnt in cur.fetchall():
            print(f"  Dispo {dispo}: {cnt}")

if __name__ == "__main__":
    main()
