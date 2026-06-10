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


def explorar_jerarquias_y_niveles_incidenttype(conn):
    print("\n=== JERARQUIAS de la dimension incident en el cubo [Modelo] ===")

    # ----- HIERARCHIES -----
    rs_h = win32com.client.Dispatch("ADODB.Recordset")
    query_h = "SELECT * FROM $system.MDSCHEMA_HIERARCHIES"
    rs_h.Open(query_h, conn)

    fields_h = {rs_h.Fields.Item(i).Name: i for i in range(rs_h.Fields.Count)}
    cube_idx      = fields_h.get("CUBE_NAME")
    dim_idx       = fields_h.get("DIMENSION_UNIQUE_NAME")
    hier_cap_idx  = fields_h.get("HIERARCHY_CAPTION")
    hier_uniq_idx = fields_h.get("HIERARCHY_UNIQUE_NAME")

    hierarquias_InvalidIncidentTypeMaster = []



    rs_h = win32com.client.Dispatch("ADODB.Recordset")
    query_h = "SELECT * FROM $system.MDSCHEMA_HIERARCHIES"
    rs_h.Open(query_h, conn)



    while not rs_h.EOF:
        cube_name = rs_h.Fields.Item(cube_idx).Value if cube_idx is not None else None
        dim_name  = rs_h.Fields.Item(dim_idx).Value if dim_idx is not None else None

        if cube_name == "Modelo" and dim_name == "[InvalidIncidentTypeMaster]":
            hier_cap  = rs_h.Fields.Item(hier_cap_idx).Value if hier_cap_idx is not None else "N/A"
            hier_uniq = rs_h.Fields.Item(hier_uniq_idx).Value if hier_uniq_idx is not None else "N/A"
            print(f"- Jerarquia: {hier_cap} | Unique: {hier_uniq}")
            hierarquias_InvalidIncidentTypeMaster.append(hier_uniq)

        rs_h.MoveNext()
    

    rs_h.Close()


    # Si encontramos al menos una jerarquia, vemos niveles de la primera
    if hierarquias_InvalidIncidentTypeMaster:
        target_hier = hierarquias_InvalidIncidentTypeMaster[0]
        print(f"\n=== NIVELES de la jerarquia {target_hier} ===")

        rs_l = win32com.client.Dispatch("ADODB.Recordset")
        query_l = "SELECT * FROM $system.MDSCHEMA_LEVELS"
        rs_l.Open(query_l, conn)

        fields_l = {rs_l.Fields.Item(i).Name: i for i in range(rs_l.Fields.Count)}
        hier_uniq_idx2 = fields_l.get("HIERARCHY_UNIQUE_NAME")
        level_cap_idx  = fields_l.get("LEVEL_CAPTION")
        level_uniq_idx = fields_l.get("LEVEL_UNIQUE_NAME")
        level_num_idx  = fields_l.get("LEVEL_NUMBER")

        while not rs_l.EOF:
            hier_uniq_val = rs_l.Fields.Item(hier_uniq_idx2).Value if hier_uniq_idx2 is not None else None

            if hier_uniq_val == target_hier:
                lvl_cap  = rs_l.Fields.Item(level_cap_idx).Value if level_cap_idx is not None else "N/A"
                lvl_uniq = rs_l.Fields.Item(level_uniq_idx).Value if level_uniq_idx is not None else "N/A"
                lvl_num  = rs_l.Fields.Item(level_num_idx).Value if level_num_idx is not None else "N/A"
                print(f"- Nivel #{lvl_num}: {lvl_cap} | Unique: {lvl_uniq}")
            rs_l.MoveNext()

        rs_l.Close()
    else:
        print("No se encontraron jerarquias para invalid (raro).")














def explorar_jerarquias_y_niveles_fecha(conn):
    print("\n=== JERARQUIAS de la dimension [Fecha] en el cubo [Modelo] ===")

    # ----- HIERARCHIES -----
    rs_h = win32com.client.Dispatch("ADODB.Recordset")
    query_h = "SELECT * FROM $system.MDSCHEMA_HIERARCHIES"
    rs_h.Open(query_h, conn)

    fields_h = {rs_h.Fields.Item(i).Name: i for i in range(rs_h.Fields.Count)}
    cube_idx      = fields_h.get("CUBE_NAME")
    dim_idx       = fields_h.get("DIMENSION_UNIQUE_NAME")
    hier_cap_idx  = fields_h.get("HIERARCHY_CAPTION")
    hier_uniq_idx = fields_h.get("HIERARCHY_UNIQUE_NAME")

    hierarquias_fecha = []



    rs_h = win32com.client.Dispatch("ADODB.Recordset")
    query_h = "SELECT * FROM $system.MDSCHEMA_HIERARCHIES"
    rs_h.Open(query_h, conn)



    while not rs_h.EOF:
        cube_name = rs_h.Fields.Item(cube_idx).Value if cube_idx is not None else None
        dim_name  = rs_h.Fields.Item(dim_idx).Value if dim_idx is not None else None

        if cube_name == "Modelo" and dim_name == "[Fecha]":
            hier_cap  = rs_h.Fields.Item(hier_cap_idx).Value if hier_cap_idx is not None else "N/A"
            hier_uniq = rs_h.Fields.Item(hier_uniq_idx).Value if hier_uniq_idx is not None else "N/A"
            print(f"- Jerarquia: {hier_cap} | Unique: {hier_uniq}")
            hierarquias_fecha.append(hier_uniq)

        rs_h.MoveNext()



        

    rs_h.Close()




    # Si encontramos al menos una jerarquia, vemos niveles de la primera
    if hierarquias_fecha:
        target_hier = hierarquias_fecha[0]
        print(f"\n=== NIVELES de la jerarquia {target_hier} ===")

        rs_l = win32com.client.Dispatch("ADODB.Recordset")
        query_l = "SELECT * FROM $system.MDSCHEMA_LEVELS"
        rs_l.Open(query_l, conn)

        fields_l = {rs_l.Fields.Item(i).Name: i for i in range(rs_l.Fields.Count)}
        hier_uniq_idx2 = fields_l.get("HIERARCHY_UNIQUE_NAME")
        level_cap_idx  = fields_l.get("LEVEL_CAPTION")
        level_uniq_idx = fields_l.get("LEVEL_UNIQUE_NAME")
        level_num_idx  = fields_l.get("LEVEL_NUMBER")

        while not rs_l.EOF:
            hier_uniq_val = rs_l.Fields.Item(hier_uniq_idx2).Value if hier_uniq_idx2 is not None else None

            if hier_uniq_val == target_hier:
                lvl_cap  = rs_l.Fields.Item(level_cap_idx).Value if level_cap_idx is not None else "N/A"
                lvl_uniq = rs_l.Fields.Item(level_uniq_idx).Value if level_uniq_idx is not None else "N/A"
                lvl_num  = rs_l.Fields.Item(level_num_idx).Value if level_num_idx is not None else "N/A"
                print(f"- Nivel #{lvl_num}: {lvl_cap} | Unique: {lvl_uniq}")
            rs_l.MoveNext()

        rs_l.Close()
    else:
        print("No se encontraron jerarquias para [Fecha] (raro).")

def main():
    try:
        print("Abriendo conexion al cubo...")
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open(conn_str)
        print(" Conexion abierta. Estado:", conn.State)

        explorar_jerarquias_y_niveles_fecha(conn)
        explorar_jerarquias_y_niveles_incidenttype(conn)

        conn.Close()
        print("\n Exploracion terminada.")
    except Exception as e:
        print("\n Error:")
        print(e)
        print("\nDetalle completo:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
