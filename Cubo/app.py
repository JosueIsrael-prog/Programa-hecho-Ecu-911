import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datos import cargar_calendario, obtener_centros_por_hora

meses_nombres = {
    1: "1 - Enero",
    2: "2 - Febrero",
    3: "3 - Marzo",
    4: "4 - Abril",
    5: "5 - Mayo",
    6: "6 - Junio",
    7: "7 - Julio",
    8: "8 - Agosto",
    9: "9 - Septiembre",
    10: "10 - Octubre",
    11: "11 - Noviembre",
    12: "12 - Diciembre",
}

# Estas variables se van a inicializar en crear_ui
combo_anio = None
combo_mes = None
combo_dia = None
tree = None
label_total = None
var_modo = None
mapa_calendario = {}

def crear_mapa_calendario(df_cal: pd.DataFrame):
    mapa = {}
    for _, fila in df_cal.iterrows():
        y = int(fila["year"])
        m = int(fila["month"])
        d = int(fila["day"])
        if y not in mapa:
            mapa[y] = {}
        if m not in mapa[y]:
            mapa[y][m] = set()
        mapa[y][m].add(d)

    for y in mapa:
        for m in mapa[y]:
            mapa[y][m] = sorted(list(mapa[y][m]))

    return mapa

def actualizar_meses(*args):
    global combo_anio, combo_mes, combo_dia, mapa_calendario
    if combo_anio is None:
        return
    try:
        anio = int(combo_anio.get())
    except:
        return

    meses = sorted(mapa_calendario.get(anio, {}).keys())
    valores = [meses_nombres[m] for m in meses]
    combo_mes["values"] = valores

    combo_dia["values"] = []
    if valores:
        combo_mes.current(0)
        actualizar_dias()

def actualizar_dias(*args):
    global combo_anio, combo_mes, combo_dia, mapa_calendario
    if combo_anio is None or combo_mes is None or combo_dia is None:
        return

    try:
        anio = int(combo_anio.get())
    except:
        return

    texto_mes = combo_mes.get()
    if not texto_mes:
        return

    numero_mes = int(texto_mes.split(" - ")[0])
    dias = mapa_calendario.get(anio, {}).get(numero_mes, [])
    combo_dia["values"] = dias
    if dias:
        combo_dia.current(0)

def cargar_tabla():
    global combo_anio, combo_mes, combo_dia, var_modo, tree, label_total
    try:
        anio = int(combo_anio.get())
        texto_mes = combo_mes.get()
        if not texto_mes:
            messagebox.showwarning("Seleccion", "Selecciona un mes.")
            return
        mes = int(texto_mes.split(" - ")[0])
        dia = int(combo_dia.get())
    except Exception:
        messagebox.showwarning("Seleccion", "Selecciona año, mes y día válidos.")
        return

    modo = var_modo.get()

    try:
        df = obtener_centros_por_hora(anio, mes, dia, modo)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return

    if df.empty:
        messagebox.showinfo("Sin datos", "No hay datos para esa fecha y filtro.")
        limpiar_tabla()
        label_total.config(text="Total general: 0")
        return

    mostrar_dataframe(df)

def limpiar_tabla():
    global tree
    tree.delete(*tree.get_children())
    tree["columns"] = ()
    tree["show"] = "headings"

def mostrar_dataframe(df: pd.DataFrame):
    global tree, label_total
    limpiar_tabla()

    df_show = df.copy()
    df_show.insert(0, "Centro", df_show.index)

    columnas = list(df_show.columns)
    tree["columns"] = columnas
    tree["show"] = "headings"

    for col in columnas:
        tree.heading(col, text=str(col))
        if isinstance(col, int) or str(col).isdigit():
            tree.column(col, width=40, anchor=tk.E)
        else:
            tree.column(col, width=140 if col == "Centro" else 80, anchor=tk.W)

    for _, fila in df_show.iterrows():
        valores = [fila[col] for col in columnas]
        tree.insert("", tk.END, values=valores)

    columnas_horas = [c for c in columnas if isinstance(c, int) or str(c).isdigit()]
    total_general = df_show[columnas_horas].values.sum()
    label_total.config(text=f"Total general: {int(total_general)}")

def crear_ui(root, anios_disponibles):
    global combo_anio, combo_mes, combo_dia, tree, label_total, var_modo

    root.title("ECU 911 - Centros e Incidentes (Cubo)")
    root.geometry("1200x600")

    var_modo = tk.StringVar(value="todos")

    frame_filtros = ttk.Frame(root, padding=10)
    frame_filtros.pack(side=tk.TOP, fill=tk.X)

    ttk.Label(frame_filtros, text="Año:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    combo_anio = ttk.Combobox(frame_filtros, state="readonly", values=anios_disponibles, width=8)
    combo_anio.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(frame_filtros, text="Mes:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    combo_mes = ttk.Combobox(frame_filtros, state="readonly", values=[], width=15)
    combo_mes.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    ttk.Label(frame_filtros, text="Día:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
    combo_dia = ttk.Combobox(frame_filtros, state="readonly", values=[], width=5)
    combo_dia.grid(row=0, column=5, padx=5, pady=5, sticky="w")

    boton_cargar = ttk.Button(frame_filtros, text="Cargar tabla", command=cargar_tabla)
    boton_cargar.grid(row=0, column=6, padx=10, pady=5)

    frame_verificador = ttk.LabelFrame(root, text="Filtro verificador", padding=10)
    frame_verificador.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))

    ttk.Radiobutton(frame_verificador, text="Todos", value="todos", variable=var_modo).grid(row=0, column=0, padx=5)
    ttk.Radiobutton(frame_verificador, text="Válidos (1)", value="validos", variable=var_modo).grid(row=0, column=1, padx=5)
    ttk.Radiobutton(frame_verificador, text="No válidos (0)", value="no_validos", variable=var_modo).grid(row=0, column=2, padx=5)

    frame_tabla = ttk.Frame(root)
    frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    tree = ttk.Treeview(frame_tabla)
    tree_scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tree.yview)
    tree_scroll_x = ttk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

    tree.grid(row=0, column=0, sticky="nsew")
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    tree_scroll_x.grid(row=1, column=0, sticky="ew")

    frame_tabla.rowconfigure(0, weight=1)
    frame_tabla.columnconfigure(0, weight=1)

    frame_total = ttk.Frame(root, padding=10)
    frame_total.pack(side=tk.BOTTOM, fill=tk.X)
    label_total = ttk.Label(frame_total, text="Total general: 0")
    label_total.pack(side=tk.RIGHT)

    # eventos
    combo_anio.bind("<<ComboboxSelected>>", actualizar_meses)
    combo_mes.bind("<<ComboboxSelected>>", actualizar_dias)

    # dejar seleccion inicial
    if anios_disponibles:
        combo_anio.current(0)
        actualizar_meses()

    # guardar referencias globales
    globals()["combo_mes"] = combo_mes
    globals()["combo_dia"] = combo_dia
    globals()["tree"] = tree
    globals()["label_total"] = label_total

if __name__ == "__main__":
    cal_df = cargar_calendario()
    if cal_df.empty:
        raise SystemExit("No se pudo cargar el calendario desde el cubo.")

    mapa_calendario = crear_mapa_calendario(cal_df)
    anios_disponibles = sorted(mapa_calendario.keys())

    root = tk.Tk()
    crear_ui(root, anios_disponibles)
    root.mainloop()
