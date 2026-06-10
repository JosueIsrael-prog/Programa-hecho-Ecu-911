import win32com.client
import traceback
import pandas as pd

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
        # 1. Conexion
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open(conn_str)
        print("Conexion abierta.")

        # 2. Comando MDX
        cmd = win32com.client.Dispatch("ADODB.Command")
        cmd.ActiveConnection = conn

        mdx = """
        SELECT
          { [Measures].[SumaIncidentes] } ON COLUMNS,
          { [Fecha].[Anio].[Anio].MEMBERS } ON ROWS
        FROM [Modelo]
        """

        cmd.CommandText = mdx

        # 3. Ejecutar y manejar el resultado (puede ser Recordset o (Recordset, records_affected))
        result = cmd.Execute()

        # Si viene como tupla, tomamos el primer elemento (Recordset)
        if isinstance(result, tuple):
            rs = result[0]
        else:
            rs = result

        if rs is None:
            print("No se obtuvo Recordset (rs es None).")
            conn.Close()
            return

        # 4. Extraer nombres de columnas
        field_names = [rs.Fields.Item(i).Name for i in range(rs.Fields.Count)]
        print("\nColumnas devueltas por el MDX:")
        for i, name in enumerate(field_names):
            print(f"  {i}: {name}")

        # 5. Recorrer filas
        rows = []
        print("\nFilas de ejemplo (crudas):")

        max_print = 10
        printed = 0

        while not rs.EOF:
            values = [rs.Fields.Item(i).Value for i in range(rs.Fields.Count)]

            if printed < max_print:
                print(values)
                printed += 1

            row_dict = dict(zip(field_names, values))
            rows.append(row_dict)

            rs.MoveNext()

        rs.Close()
        conn.Close()

        # 6. Crear DataFrame
        if not rows:
            print("\nNo se recibieron filas del cubo.")
            return

        df = pd.DataFrame(rows)
        print("\nDataFrame completo (primeras filas):")
        print(df.head())

        # 7. Intentar limpiar la columna del miembro (anio)
        miembro_col = field_names[0]  # normalmente la primera es el miembro de la dimension en filas
        if miembro_col in df.columns:
            def limpiar_miembro(m):
                if m is None:
                    return None
                m = str(m)
                # ej: [Fecha].[Anio].&[2023] -> 2023
                if "&[" in m and m.endswith("]"):
                    return m.split("&[")[-1].rstrip("]")
                return m

            df["Anio_limpio"] = df[miembro_col].apply(limpiar_miembro)

        print("\nDataFrame con columna Anio_limpio (si se pudo limpiar):")
        print(df.head())

        

    except Exception as e:
        print("\nError ejecutando MDX:")
        print(e)
        print("\nDetalle completo:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
