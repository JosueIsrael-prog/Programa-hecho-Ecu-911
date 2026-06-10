import win32com.client
import traceback

conn_str = (
    "Provider=MSOLAP.8;"
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

def main():
    try:
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open(conn_str)
        print("Conexion abierta.")

        cmd = win32com.client.Dispatch("ADODB.Command")
        cmd.ActiveConnection = conn

        mdx = """
        SELECT
          { [Measures].[SumaIncidentes] } ON COLUMNS,
          HEAD([Fecha].[fechad].MEMBERS, 50)
            DIMENSION PROPERTIES MEMBER_UNIQUE_NAME, MEMBER_CAPTION
          ON ROWS
        FROM [Modelo]
        """

        cmd.CommandText = mdx

        result = cmd.Execute()
        rs = result[0] if isinstance(result, tuple) else result

        if rs is None:
            print("No se obtuvo recordset.")
            conn.Close()
            return

        field_names = [rs.Fields.Item(i).Name for i in range(rs.Fields.Count)]
        print("Columnas devueltas:")
        for i, name in enumerate(field_names):
            print(f"  {i}: {name}")

        print("\nFilas de ejemplo:")
        while not rs.EOF:
            values = [rs.Fields.Item(i).Value for i in range(rs.Fields.Count)]
            print(values)
            rs.MoveNext()

        rs.Close()
        conn.Close()
        print("\nListo.")
    except Exception as e:
        print("Error:")
        print(e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
