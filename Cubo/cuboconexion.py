import win32com.client
import traceback

PROVIDERS = [
    "MSOLAP.8",
    "MSOLAP.9",
    "MSOLAP.10",
    "MSOLAP.11",
    "MSOLAP.12",
    "MSOLAP.13",
    "MSOLAP.14",
    "MSOLAP",
]

BASE_CONN_STR = (
    "Persist Security Info=True;"
    "User ID=dwh\\ana.cartagena;"
    "Password=p.123456;"
    "Initial Catalog=TabSanitaria;"
    "Data Source=10.121.6.61;"
    "Location=10.121.6.61;"
    "MDX Compatibility=1;"
    "Safety Options=2;"
    "MDX Missing Member Mode=Error;"
    "Update Isolation Level=2;"
)


def open_connection():
    last_error = None
    for provider in PROVIDERS:
        conn_str = f"Provider={provider};" + BASE_CONN_STR
        try:
            conn = win32com.client.Dispatch("ADODB.Connection")
            conn.Open(conn_str)
            return conn
        except Exception as exc:
            last_error = exc
            # try next provider
            continue

    raise RuntimeError(
        "No se encontró un proveedor OLAP válido. "
        "Instala el proveedor MSOLAP adecuado o revisa la versión instalada.",
        last_error,
    )

def main():
    try:
        print("Creando conexion ADODB...")
        conn = win32com.client.Dispatch("ADODB.Connection")

        print("Abriendo conexion al cubo con MSOLAP...")
        conn.Open(conn_str)
        print(" Conexion abierta. Estado:", conn.State) 

        # Probar una consulta de metadatos de cubos
        print("\nConsultando lista de cubos con $system.MDSCHEMA_CUBES ...")

        rs = win32com.client.Dispatch("ADODB.Recordset")
        query = "SELECT * FROM $system.MDSCHEMA_CUBES"
        rs.Open(query, conn)

        #  columnas por nombre
        fields = {rs.Fields.Item(i).Name: i for i in range(rs.Fields.Count)}
        cube_name_idx = fields.get("CUBE_NAME")
        catalog_name_idx = fields.get("CATALOG_NAME")

        print("\nCubos:")
        count = 0
        while not rs.EOF and count < 10:
            cube_name = rs.Fields.Item(cube_name_idx).Value if cube_name_idx is not None else "N/A"
            catalog_name = rs.Fields.Item(catalog_name_idx).Value if catalog_name_idx is not None else "N/A"
            print(f"  - Catalogo: {catalog_name} | Cubo: {cube_name}")
            rs.MoveNext()
            count += 1

        rs.Close()
        conn.Close()
        print("\n Si valiooo")

    except Exception as e:
        print("\n No valio conectarse ;(")
        print(e)
        print("\nDetalle")
        traceback.print_exc()

if __name__ == "__main__":
    main()
