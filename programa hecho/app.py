import tkinter as tk
from tkinter import ttk, messagebox

from db import conn_info
from centros_repo import fetch_centers
from incidentes_repo import get_anios, get_meses, get_dias, incidentes_por_hora
from incidentes_repo import obtener_opciones_verificador  # ya lo tenías

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

        # filtro verificador (global)
        filt_frame = tk.LabelFrame(self, text="Filtro verificador")
        filt_frame.pack(fill="x", padx=10, pady=(8, 0))
        try:
            self.col_verif, opciones = obtener_opciones_verificador()
        except Exception:
            self.col_verif, opciones = ("CodVerificador", [("Todos", None), ("Validos (1)",1), ("No validos (0)",0)])
        tk.Label(filt_frame, text=f"Columna: {self.col_verif}").pack(side="left", padx=(10,6))
        self.verif_var = tk.StringVar(value=str(opciones[0][1]))
        for texto, val in opciones:
            tk.Radiobutton(filt_frame, text=texto, variable=self.verif_var, value=str(val)).pack(side="left", padx=6)

        # notebook (pestañas)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # TAB 1: Centros
        self.tab_centros = tk.Frame(nb)
        nb.add(self.tab_centros, text="Centros")

        self._build_tab_centros()

        # TAB 2: Incidentes por hora
        self.tab_horas = tk.Frame(nb)
        nb.add(self.tab_horas, text="Incidentes por hora")

        self._build_tab_horas()

        # cargas iniciales
        self.after(100, self.load_centers)
        self.after(200, self.load_anios)

    # ---------------- TAB CENTROS ----------------
    def _build_tab_centros(self):
        table_frame = tk.Frame(self.tab_centros)
        table_frame.pack(fill="both", expand=True)

        cols = ("ID", "Centro")
        self.tree_centros = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree_centros.heading("ID", text="CenterId")
        self.tree_centros.heading("Centro", text="CenterName")
        self.tree_centros.column("ID", width=90, anchor="center", stretch=False)
        self.tree_centros.column("Centro", width=900, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_centros.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree_centros.xview)
        self.tree_centros.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree_centros.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        actions = tk.Frame(self.tab_centros)
        actions.pack(fill="x", pady=6)
        tk.Button(actions, text="Refrescar", command=self.load_centers).pack(side="left")
        self.lbl_total_centros = tk.Label(actions, text="Total: 0 centros")
        self.lbl_total_centros.pack(side="right")

    def load_centers(self):
        try:
            rows = fetch_centers()
            self.tree_centros.delete(*self.tree_centros.get_children())
            for r in rows:
                self.tree_centros.insert("", "end", values=(r[0], r[1]))
            self.lbl_total_centros.config(text=f"Total: {len(rows)} centros")
        except Exception as e:
            messagebox.showerror("Error al cargar centros", str(e))

    # ---------------- TAB HORAS ----------------
    def _build_tab_horas(self):
        top = tk.Frame(self.tab_horas)
        top.pack(fill="x", pady=(0,8))

        tk.Label(top, text="Año:").pack(side="left", padx=(0,4))
        self.cbo_anio = ttk.Combobox(top, state="readonly", width=8)
        self.cbo_anio.pack(side="left")
        self.cbo_anio.bind("<<ComboboxSelected>>", self.on_change_anio)

        tk.Label(top, text="Mes:").pack(side="left", padx=(12,4))
        self.cbo_mes = ttk.Combobox(top, state="readonly", width=14, values=[])
        self.cbo_mes.pack(side="left")
        self.cbo_mes.bind("<<ComboboxSelected>>", self.on_change_mes)

        tk.Label(top, text="Día:").pack(side="left", padx=(12,4))
        self.cbo_dia = ttk.Combobox(top, state="readonly", width=12, values=[])
        self.cbo_dia.pack(side="left")

        tk.Button(top, text="Cargar tabla", command=self.load_horas).pack(side="left", padx=12)

        # tabla horas: CentroId, Centro, 0..23, Total
        frame = tk.Frame(self.tab_horas)
        frame.pack(fill="both", expand=True)

        cols = ["CenterId","CenterName"] + [str(h) for h in range(24)] + ["Total"]
        self.tree_horas = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_horas.heading(c, text=c)
        self.tree_horas.column("CenterId", width=80, anchor="center", stretch=False)
        self.tree_horas.column("CenterName", width=240, anchor="w")
        for h in range(24):
            self.tree_horas.column(str(h), width=45, anchor="e", stretch=False)
        self.tree_horas.column("Total", width=70, anchor="e", stretch=False)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_horas.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree_horas.xview)
        self.tree_horas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree_horas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.lbl_total_general = tk.Label(self.tab_horas, text="Total general: 0")
        self.lbl_total_general.pack(anchor="e", pady=6)

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
        anio = int(self.cbo_anio.get())
        try:
            meses = get_meses(anio)
            self.cbo_mes["values"] = [f"{m:02d} - {MES_NOMBRE.get(m, m)}" for m in meses]
            if meses:
                self.cbo_mes.current(0)
                self.on_change_mes()
        except Exception as e:
            messagebox.showerror("Error obteniendo meses", str(e))

    def on_change_mes(self, *_):
        if not self.cbo_mes.get():
            return
        anio = int(self.cbo_anio.get())
        mes = int(self.cbo_mes.get().split(" - ")[0])
        try:
            dias = get_dias(anio, mes)  # 'YYYY-MM-DD'
            self.cbo_dia["values"] = dias
            if dias:
                self.cbo_dia.current(0)
        except Exception as e:
            messagebox.showerror("Error obteniendo días", str(e))

    # carga tabla por horas
    def load_horas(self):
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
                if 0 <= int(hora) <= 23:
                    data[key][int(hora)] = int(cnt)

            # rellenar UI
            self.tree_horas.delete(*self.tree_horas.get_children())
            total_general = 0
            for (cid, cname), vec in sorted(data.items(), key=lambda x: x[0][0]):
                fila_total = sum(vec)
                total_general += fila_total
                self.tree_horas.insert("", "end",
                                       values=[cid, cname] + vec + [fila_total])
            self.lbl_total_general.config(text=f"Total general: {total_general}")
        except Exception as e:
            messagebox.showerror("Error al cargar incidentes", str(e))

if __name__ == "__main__":
    App().mainloop()
