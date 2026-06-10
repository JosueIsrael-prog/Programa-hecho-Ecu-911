import win32com.client
import traceback
import pandas as pd
from datetime import datetime

from cuboconexion import open_connection

# ================== UTILIDADES BASE ==================

def ejecutar_mdx(mdx: str) -> pd.DataFrame:
    conn = open_connection()

    cmd = win32com.client.Dispatch("ADODB.Command")
    cmd.ActiveConnection = conn
    cmd.CommandText = mdx

    result = cmd.Execute()
    rs = result[0] if isinstance(result, tuple) else result

    if rs is None:
        conn.Close()
        return pd.DataFrame()

    field_names = [rs.Fields.Item(i).Name for i in range(rs.Fields.Count)]
    rows = []

    while not rs.EOF:
        values = [rs.Fields.Item(i).Value for i in range(rs.Fields.Count)]
        rows.append(dict(zip(field_names, values)))
        rs.MoveNext()

    rs.Close()
    conn.Close()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def cargar_calendario() -> pd.DataFrame:
    mdx = """
    SELECT
      { [Measures].[SumaIncidentes] } ON COLUMNS,
      [Fecha].[fechad].MEMBERS
        DIMENSION PROPERTIES MEMBER_UNIQUE_NAME, MEMBER_CAPTION
      ON ROWS
    FROM [Modelo]
    """

    df = ejecutar_mdx(mdx)
    if df.empty:
        print("No se pudo obtener el calendario desde el cubo.")
        return pd.DataFrame()

    cols = list(df.columns)
    unique_col = next(c for c in cols if "fechad" in c and "UNIQUE_NAME" in c)
    caption_col = next(c for c in cols if "fechad" in c and "MEMBER_CAPTION" in c)

    data = []
    for unique_name, caption in df[[unique_col, caption_col]].itertuples(index=False, name=None):
        if not caption:
            continue
        try:
            dt = datetime.strptime(str(caption), "%d/%m/%Y")
        except:
            continue
        data.append({
            "unique_name": unique_name,
            "caption": caption,
            "year": dt.year,
            "month": dt.month,
            "day": dt.day
        })

    cal_df = pd.DataFrame(data)
    if cal_df.empty:
        print("Calendario vacio despues de procesar capturas de fecha.")
    return cal_df


def buscar_fecha_unique_name(calendario: pd.DataFrame, year: int, month: int, day: int):
    cal_anio = calendario[calendario["year"] == year]
    if cal_anio.empty:
        raise ValueError(f"No hay registros para el anio {year}. Anios disponibles: {sorted(calendario['year'].unique())}")

    cal_mes = cal_anio[cal_anio["month"] == month]
    if cal_mes.empty:
        raise ValueError(
            f"No hay registros para {year}-{month:02d}. "
            f"Meses disponibles para ese anio: {sorted(cal_anio['month'].unique())}"
        )

    cal_dia = cal_mes[cal_mes["day"] == day]
    if cal_dia.empty:
        raise ValueError(
            f"No hay registros para la fecha {year}-{month:02d}-{day:02d}. "
            f"Dias disponibles para ese mes: {sorted(cal_mes['day'].unique())}"
        )

    fila = cal_dia.iloc[0]
    return fila["unique_name"], fila["caption"]


def construir_where(fecha_unique_name: str, modo_verificador: str) -> str:
    partes = ["[Measures].[SumaIncidentes]", fecha_unique_name]

    modo = modo_verificador.lower()
    if modo == "validos":
        partes.append("[Verificador].[CodVerificador].&[1]")
    elif modo == "no_validos":
        partes.append("[Verificador].[CodVerificador].&[0]")
    

    return "( " + ", ".join(partes) + " )"

# ============ NUCLEO: CENTROS X HORA ==============

def tabla_centros_por_hora(fecha_unique_name: str, modo_verificador: str = "todos") -> pd.DataFrame:
    where_tuple = construir_where(fecha_unique_name, modo_verificador)

    mdx = f"""
    SELECT
      NON EMPTY
        [HoraMinSec].[Horas].[Hour].Members
      ON COLUMNS,
      NON EMPTY
        [Center].[CenterName].[CenterName].Members
          DIMENSION PROPERTIES MEMBER_CAPTION
      ON ROWS
    FROM [Modelo]
    WHERE {where_tuple}
    """

    df_raw = ejecutar_mdx(mdx)

    if df_raw.empty:
        print("No se recibieron datos del cubo para esa fecha / filtro.")
        return df_raw

    cols = list(df_raw.columns)
    center_col = cols[0]
    hour_cols = cols[1:]

    # renombrar columnas de hora
    new_names = {}
    for col in hour_cols:
        name = str(col)
        if "&[" in name and name.endswith("]"):
            hora = name.split("&[")[-1].rstrip("]")
        else:
            hora = name
        new_names[col] = int(hora) if hora.isdigit() else hora

    df = df_raw.rename(columns=new_names)
    df = df.set_index(center_col)

    horas_ordenadas = sorted([c for c in df.columns if isinstance(c, int)])
    otras_cols = [c for c in df.columns if c not in horas_ordenadas]
    df = df[horas_ordenadas + otras_cols].fillna(0)

    total_general = df[horas_ordenadas].values.sum()

    print(f"\nTabla centros x hora  (modo_verificador = {modo_verificador}):")
    print(df[horas_ordenadas])
    print("\nTotal general:", int(total_general))

    return df

# ============ FUNCION PRINCIPAL ==============

def obtener_centros_por_hora(year: int, month: int, day: int, modo_verificador: str = "todos") -> pd.DataFrame:
    calendario = cargar_calendario()
    if calendario.empty:
        raise RuntimeError("No se pudo cargar el calendario desde el cubo.")

    fecha_unique_name, caption = buscar_fecha_unique_name(calendario, year, month, day)

    print("\nFecha seleccionada en el cubo:")
    print(f"{fecha_unique_name}  ->  {caption}")

    df = tabla_centros_por_hora(fecha_unique_name, modo_verificador)
    return df














