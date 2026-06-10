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

def listar_dimensiones(conn):
    print("\n=== DIMENSIONES del cubo [Modelo] ===")

    rs = win32com.client.Dispatch("ADODB.Recordset")

    # Consulta generica: todas las columnas, todos los cubos
    query_dims = "SELECT * FROM $system.MDSCHEMA_DIMENSIONS"
    rs.Open(query_dims, conn)

    # Mapeamos nombres de columnas a indices por si cambian
    fields = {rs.Fields.Item(i).Name: i for i in range(rs.Fields.Count)}
    cube_idx       = fields.get("CUBE_NAME")
    dim_caption_ix = fields.get("DIMENSION_CAPTION")
    dim_unique_ix  = fields.get("DIMENSION_UNIQUE_NAME")
    dim_type_ix    = fields.get("DIMENSION_TYPE")

    count = 0
    while not rs.EOF:
        cube_name = rs.Fields.Item(cube_idx).Value if cube_idx is not None else None

        # Solo mostramos las dimensiones del cubo "Modelo"
        if cube_name == "Modelo":
            dim_caption = rs.Fields.Item(dim_caption_ix).Value if dim_caption_ix is not None else "N/A"
            dim_unique  = rs.Fields.Item(dim_unique_ix).Value  if dim_unique_ix is not None else "N/A"
            dim_type    = rs.Fields.Item(dim_type_ix).Value    if dim_type_ix is not None else "N/A"
            print(f"- Dimension: {dim_caption} | Unique: {dim_unique} | Tipo: {dim_type}")
            count += 1

        rs.MoveNext()

    rs.Close()
    if count == 0:
        print("No se encontraron dimensiones para el cubo 'Modelo' (raro, revisemos si el nombre del cubo es exacto).")


def listar_medidas(conn):
    print("\n=== MEDIDAS del cubo [Modelo] ===")

    rs = win32com.client.Dispatch("ADODB.Recordset")

    query_measures = "SELECT * FROM $system.MDSCHEMA_MEASURES"
    rs.Open(query_measures, conn)

    fields = {rs.Fields.Item(i).Name: i for i in range(rs.Fields.Count)}
    cube_idx         = fields.get("CUBE_NAME")
    measure_cap_ix   = fields.get("MEASURE_CAPTION")
    measure_uniq_ix  = fields.get("MEASURE_UNIQUE_NAME")
    group_name_ix    = fields.get("MEASUREGROUP_NAME")

    count = 0
    while not rs.EOF:
        cube_name = rs.Fields.Item(cube_idx).Value if cube_idx is not None else None

        if cube_name == "Modelo":
            measure_cap  = rs.Fields.Item(measure_cap_ix).Value  if measure_cap_ix is not None else "N/A"
            measure_uniq = rs.Fields.Item(measure_uniq_ix).Value if measure_uniq_ix is not None else "N/A"
            group_name   = rs.Fields.Item(group_name_ix).Value   if group_name_ix is not None else "N/A"
            print(f"- Medida: {measure_cap} | Unique: {measure_uniq} | Grupo: {group_name}")
            count += 1

        rs.MoveNext()

    rs.Close()
    if count == 0:
        print("No se encontraron medidas para el cubo 'Modelo'.")


def main():
    try:
        print("Abriendo conexion al cubo...")
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open(conn_str)
        print(" Conexion abierta. Estado:", conn.State)

        listar_dimensiones(conn)
        listar_medidas(conn)

        conn.Close()
        print("\n Exploracion terminada.")
    except Exception as e:
        print("\n Error:")
        print(e)
        print("\nDetalle completo:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
