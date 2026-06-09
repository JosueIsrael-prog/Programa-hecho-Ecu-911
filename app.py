import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import os

try:
    from db import conn_info
    from centros_repo import fetch_centers
    from incidentes_repo import get_anios, get_meses, get_dias, incidentes_por_hora
    from incidentes_repo import obtener_opciones_verificador  # ya lo tenías
except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error de Inicio Crítico", f"El sistema no pudo iniciar debido a un error en el código o entorno.\n\nDetalle: {str(e)}\n\n{traceback.format_exc()}")
    raise SystemExit(1)

MES_NOMBRE = {
    1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
    7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        info = conn_info()
        self.title("ECU 911 - Centros e Incidentes")
        self.geometry("1100x650")

        # header
        hdr = tk.Label(self, text=f"Servidor: {info['server']}   |   Base: {info['database']}   |   Driver: {info['driver']}",
                       anchor="w", fg="#444")
        hdr.pack(fill="x", padx=10, pady=(10, 0))

        # Filtros Globales (Año, Mes, Día, Verificador)
        filt_frame = tk.LabelFrame(self, text="Filtros Generales", padx=10, pady=5)
        filt_frame.pack(fill="x", padx=10, pady=(8, 0))

        row1 = tk.Frame(filt_frame)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Año:").pack(side="left", padx=(0,4))
        self.cbo_anio = ttk.Combobox(row1, state="readonly", width=8)
        self.cbo_anio.pack(side="left")
        self.cbo_anio.bind("<<ComboboxSelected>>", self.on_change_anio)

        tk.Label(row1, text="Mes:").pack(side="left", padx=(12,4))
        self.cbo_mes = ttk.Combobox(row1, state="readonly", width=14, values=[])
        self.cbo_mes.pack(side="left")
        self.cbo_mes.bind("<<ComboboxSelected>>", self.on_change_mes)

        tk.Label(row1, text="Día:").pack(side="left", padx=(12,4))
        self.cbo_dia = ttk.Combobox(row1, state="readonly", width=12, values=[])
        self.cbo_dia.pack(side="left")

        row2 = tk.Frame(filt_frame)
        row2.pack(fill="x", pady=(5,2))
        try:
            self.col_verif, opciones = obtener_opciones_verificador()
        except Exception:
            self.col_verif, opciones = ("CodVerificador", [("Todos", None), ("Validos (1)",1), ("No validos (0)",0)])
        
        tk.Label(row2, text="Verificador:").pack(side="left", padx=(0,6))
        self.verif_var = tk.StringVar(value=str(opciones[0][1]))
        for texto, val in opciones:
            tk.Radiobutton(row2, text=texto, variable=self.verif_var, value=str(val)).pack(side="left", padx=6)

        row3 = tk.Frame(filt_frame)
        row3.pack(fill="x", pady=(5,0))
        tk.Button(row3, text="Cargar Datos (BD y Cubo)", command=self.load_all_data, bg="#d9edf7", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        tk.Button(row3, text="Comparar BD vs Cubo", command=self.load_comparacion, bg="#fcf8e3", font=("Arial", 9, "bold")).pack(side="left", padx=10)

        # notebook (pestañas)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # TAB 1: Datos BD
        self.tab_bd = tk.Frame(nb)
        nb.add(self.tab_bd, text="Datos Base de Datos")
        self._build_tab_bd()

        # TAB 2: Datos Cubo
        self.tab_cubo = tk.Frame(nb)
        nb.add(self.tab_cubo, text="Datos Cubo OLAP")
        self._build_tab_cubo()

        # TAB 3: Comparación
        self.tab_comparacion = tk.Frame(nb)
        nb.add(self.tab_comparacion, text="Comparación")
        self._build_tab_comparacion()

        # TAB 4: Detalle de Errores
        self.tab_errores = tk.Frame(nb)
        nb.add(self.tab_errores, text="Detalle de Errores")
        self._build_tab_errores()

        # cargas iniciales
        self.after(100, self.load_anios)

    # ---------------- TAB DATOS BD ----------------
    def _build_tab_bd(self):
        frame = tk.Frame(self.tab_bd)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ["CenterId","CenterName"] + [str(h) for h in range(24)] + ["Total"]
        self.tree_bd = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_bd.heading(c, text=c)
        self.tree_bd.column("CenterId", width=80, anchor="center", stretch=False)
        self.tree_bd.column("CenterName", width=240, anchor="w")
        for h in range(24):
            self.tree_bd.column(str(h), width=45, anchor="e", stretch=False)
        self.tree_bd.column("Total", width=70, anchor="e", stretch=False)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_bd.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree_bd.xview)
        self.tree_bd.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree_bd.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.lbl_total_bd = tk.Label(self.tab_bd, text="Total general BD: 0", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_total_bd.pack(anchor="e", pady=6, padx=10)

    # ---------------- TAB DATOS CUBO ----------------
    def _build_tab_cubo(self):
        frame = tk.Frame(self.tab_cubo)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ["CenterName"] + [str(h) for h in range(24)] + ["Total"]
        self.tree_cubo = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_cubo.heading(c, text=c)
        self.tree_cubo.column("CenterName", width=240, anchor="w")
        for h in range(24):
            self.tree_cubo.column(str(h), width=45, anchor="e", stretch=False)
        self.tree_cubo.column("Total", width=70, anchor="e", stretch=False)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_cubo.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree_cubo.xview)
        self.tree_cubo.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree_cubo.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.lbl_total_cubo = tk.Label(self.tab_cubo, text="Total general Cubo: 0", font=("Arial", 9, "bold"), fg="green")
        self.lbl_total_cubo.pack(anchor="e", pady=6, padx=10)

    # ---------------- TAB COMPARACION ----------------
    def _build_tab_comparacion(self):
        frame = tk.Frame(self.tab_comparacion)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("Tipo Error", "Ubicación (Centro)", "Hora", "Valor Cubo", "Valor BD", "Diferencia")
        self.tree_comp = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_comp.heading(c, text=c)
        self.tree_comp.column("Tipo Error", width=120)
        self.tree_comp.column("Ubicación (Centro)", width=250)
        self.tree_comp.column("Hora", width=60, anchor="center")
        self.tree_comp.column("Valor Cubo", width=90, anchor="e")
        self.tree_comp.column("Valor BD", width=90, anchor="e")
        self.tree_comp.column("Diferencia", width=90, anchor="e")

        # Configurar colores para diferencias
        self.tree_comp.tag_configure("diferencia", background="#ffcccc", foreground="black")
        self.tree_comp.tag_configure("coincidencia", background="#d4edda", foreground="black")
        self.tree_comp.tag_configure("falta", background="#fcf8e3", foreground="black")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_comp.yview)
        self.tree_comp.configure(yscrollcommand=vsb.set)
        self.tree_comp.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.lbl_resumen_comp = tk.Label(self.tab_comparacion, text="Resumen: Pendiente de comparación", justify="left", font=("Arial", 9, "bold"))
        self.lbl_resumen_comp.pack(anchor="w", padx=10, pady=10)

    # ---------------- TAB ERRORES ----------------
    def _build_tab_errores(self):
        frame = tk.Frame(self.tab_errores)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("Tipo Error", "Ubicación (Centro)", "Campo", "Valores", "Descripción")
        self.tree_errores = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_errores.heading(c, text=c)
        self.tree_errores.column("Tipo Error", width=120)
        self.tree_errores.column("Ubicación (Centro)", width=250)
        self.tree_errores.column("Campo", width=120)
        self.tree_errores.column("Valores", width=200)
        self.tree_errores.column("Descripción", width=300)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_errores.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree_errores.xview)
        self.tree_errores.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree_errores.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    # carga combos de fecha
    def load_anios(self):
        try:
            anios = get_anios()
            self.cbo_anio["values"] = anios
            if anios:
                self.cbo_anio.set(anios[0])
                self.on_change_anio()
        except Exception as e:
            messagebox.showerror("Error obteniendo años", str(e))

    def on_change_anio(self, *_):
        val_anio = self.cbo_anio.get()
        if not val_anio:
            return
        try:
            anio = int(val_anio)
            meses = get_meses(anio)
            self.cbo_mes["values"] = [f"{int(m):02d} - {MES_NOMBRE.get(int(m), m)}" for m in meses if m is not None]
            if meses:
                self.cbo_mes.current(0)
                self.on_change_mes()
            else:
                self.cbo_mes.set('')
                self.cbo_dia["values"] = []
                self.cbo_dia.set('')
        except Exception as e:
            messagebox.showerror("Error obteniendo meses", str(e))

    def on_change_mes(self, *_):
        val_mes = self.cbo_mes.get()
        val_anio = self.cbo_anio.get()
        if not val_mes or not val_anio:
            return
        try:
            anio = int(val_anio)
            mes = int(val_mes.split(" - ")[0])
            dias = get_dias(anio, mes)  # 'YYYY-MM-DD'
            self.cbo_dia["values"] = dias
            if dias:
                self.cbo_dia.current(0)
            else:
                self.cbo_dia.set('')
        except Exception as e:
            messagebox.showerror("Error obteniendo días", str(e))

    def load_all_data(self):
        self.load_bd()
        self.load_cubo()

    def load_bd(self):
        fecha = self.cbo_dia.get()
        if not fecha:
            messagebox.showwarning("Atención", "Selecciona una fecha.")
            return
        sel = self.verif_var.get()
        verif = None if sel == "None" else int(sel)

        try:
            rows = incidentes_por_hora(fecha, verif)
            # pivot a dict: (id, nombre) -> vector 0..23
            data = {}
            for cid, cname, hora, cnt in rows:
                key = (cid, cname)
                if key not in data:
                    data[key] = [0]*24
                
                try:
                    if hora is not None:
                        h = int(hora)
                        if 0 <= h <= 23:
                            data[key][h] += int(cnt or 0)
                except (ValueError, TypeError):
                    pass

            # rellenar UI
            self.tree_bd.delete(*self.tree_bd.get_children())
            total_general = 0
            for (cid, cname), vec in sorted(data.items(), key=lambda x: str(x[0][0])):
                fila_total = sum(vec)
                total_general += fila_total
                self.tree_bd.insert("", "end",
                                       values=[cid, cname] + vec + [fila_total])
            self.lbl_total_bd.config(text=f"Total general BD: {total_general}")
        except Exception as e:
            messagebox.showerror("Error al cargar incidentes BD", f"{str(e)}\n\n{traceback.format_exc()}")

    def load_cubo(self):
        fecha = self.cbo_dia.get()
        if not fecha:
            return

        sel = self.verif_var.get()
        modo = "todos"
        if sel == "1":
            modo = "validos"
        elif sel == "0":
            modo = "no_validos"

        try:
            anio, mes, dia = map(int, fecha.split("-"))
        except:
            messagebox.showerror("Error", "Formato de fecha inválido.")
            return

        try:
            from datos import obtener_centros_por_hora
            df_cubo = obtener_centros_por_hora(anio, mes, dia, modo)

            self.tree_cubo.delete(*self.tree_cubo.get_children())
            if df_cubo.empty:
                self.lbl_total_cubo.config(text="Total general Cubo: 0")
                return

            total_general = 0
            for centro, row in df_cubo.iterrows():
                vec = []
                for h in range(24):
                    vec.append(int(row.get(h, 0)))
                fila_total = sum(vec)
                total_general += fila_total
                self.tree_cubo.insert("", "end", values=[centro] + vec + [fila_total])

            self.lbl_total_cubo.config(text=f"Total general Cubo: {total_general}")

        except Exception as e:
            self.lbl_total_cubo.config(text="Total general Cubo: error")
            messagebox.showerror("Error al cargar Cubo", f"{str(e)}\n\n{traceback.format_exc()}")

    def load_comparacion(self):
        fecha = self.cbo_dia.get()
        if not fecha:
            messagebox.showwarning("Atención", "Selecciona una fecha válida.")
            return

        sel = self.verif_var.get()
        modo = "todos"
        if sel == "1": modo = "validos"
        elif sel == "0": modo = "no_validos"

        try:
            anio, mes, dia = map(int, fecha.split("-"))
        except:
            messagebox.showerror("Error", "Formato de fecha inválido.")
            return

            import sys
            # Buscar la carpeta del Cubo en una variable de entorno o en rutas comunes
            cubo_env = os.environ.get("CUBO_PATH")
            candidate_paths = [cubo_env, r"C:\Users\DNAD\OneDrive\Escritorio\Cubo\Cubo", r"C:\Users\MONICA.ROJAS\Documents\Cubo"]
            used_cubo_path = None
            for p in candidate_paths:
                if not p:
                    continue
                if os.path.isdir(p):
                    if p not in sys.path:
                        sys.path.append(p)
                    used_cubo_path = p
                    break
        
        try:
            from datos import obtener_centros_por_hora, obtener_centros_por_hora_db, comparar_tablas_cubo_vs_db

            # Cargar datos BD para que la UI muestre la información actual
            self.load_bd()

            df_cubo = obtener_centros_por_hora(anio, mes, dia, modo)
            df_db = obtener_centros_por_hora_db(anio, mes, dia, modo)

            if df_cubo.empty and df_db.empty:
                messagebox.showinfo("Sin Datos", "Ambas fuentes no tienen datos para esta fecha.")
                return

            if df_cubo.empty:
                messagebox.showwarning("Cubo vacío", "El Cubo devolvió datos vacíos para esta fecha.")
            if df_db.empty:
                messagebox.showwarning("BD vacía", "La base de datos devolvió datos vacíos para esta fecha.")

            res = comparar_tablas_cubo_vs_db(df_cubo, df_db)

            self.tree_comp.delete(*self.tree_comp.get_children())
            self.tree_errores.delete(*self.tree_errores.get_children())

            for c in res["faltan_en_db"]:
                self.tree_comp.insert("", "end", values=("Falta en BD", c, "-", "-", "-", "-"), tags=("falta",))
                self.tree_errores.insert("", "end", values=("Centro Faltante", c, "BD", "-", "Centro existe en Cubo pero no en BD antigua"))
            for c in res["faltan_en_cubo"]:
                self.tree_comp.insert("", "end", values=("Falta en Cubo", c, "-", "-", "-", "-"), tags=("falta",))
                self.tree_errores.insert("", "end", values=("Centro Faltante", c, "Cubo", "-", "Centro existe en BD pero no en Cubo"))
            for m in res["mismatches"]:
                self.tree_comp.insert("", "end", values=("Diferencia de Datos", m["Centro"], f"{m['Hora']}", m["Cubo"], m["DB"], m["Diferencia"]), tags=("diferencia",))
                self.tree_errores.insert("", "end", values=("Valor Diferente", m["Centro"], f"Hora {m['Hora']}", f"Cubo: {m['Cubo']} / BD: {m['DB']}", f"Diferencia de {m['Diferencia']} incidentes"))

            if not res["faltan_en_db"] and not res["faltan_en_cubo"] and not res["mismatches"]:
                self.tree_comp.insert("", "end", values=("✅ COINCIDENCIA", "Todos los centros y horas cuadran", "OK", "-", "-", "-"), tags=("coincidencia",))
                self.tree_errores.insert("", "end", values=("✅ Todo OK", "Sin errores", "-", "-", "No se encontraron discrepancias"))

            self.lbl_resumen_comp.config(text=" | ".join(res["summary"][:6]) + f"\n\nDetalle: {res['summary'][-1]}")

        except ImportError as e:
            messagebox.showerror("Falta Módulo", f"No se pudo importar la lógica del cubo.\n\n{e}\n\nAsegúrate de tener instalados los paquetes 'pandas' y 'pywin32'.")
        except Exception as e:
            messagebox.showerror("Error de Comparación", f"{str(e)}\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    App().mainloop()
