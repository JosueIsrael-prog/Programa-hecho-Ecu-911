# Sistema de Comparación de Datos ECU 911 (BD vs Cubo OLAP)

Este es un sistema con interfaz gráfica desarrollado en Python (Tkinter) que permite extraer, visualizar y comparar datos de incidentes por hora y por centro de operaciones entre dos fuentes principales:
1. **Base de Datos Relacional (SQL Server):** Extracción directa a través de consultas SQL.
2. **Cubo Multidimensional (OLAP):** Extracción a través de consultas MDX.

El sistema genera tablas comparativas y reportes de discrepancias para facilitar la auditoría de la información.

---

## 📋 Requisitos Previos (Prerrequisitos)

Para que el sistema funcione correctamente en una máquina nueva, necesitas tener instalado lo siguiente:

1. **Python 3.8 o superior.**
2. **Controladores de Base de Datos:**
   - [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/es-es/sql/connect/odbc/download-odbc-driver-for-sql-server) (Para conectarse a la Base de Datos).
   - Proveedor **MSOLAP** (Microsoft OLE DB Provider for Analysis Services, para conectarse al Cubo).
3. Sistema Operativo **Windows** (requerido para la librería `pywin32` y las conexiones ADODB).

---

## 🚀 Instalación y Configuración

Sigue estos pasos para ejecutar el proyecto en una máquina desde cero:

### 1. Clonar el repositorio
Abre tu terminal y ejecuta:
```bash
git clone https://github.com/JosueIsrael-prog/Programa-hecho-Ecu-911.git
cd "Programa-hecho-Ecu-911/programa hecho"
```

### 2. Crear un Entorno Virtual (Recomendado)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar las Dependencias
Ejecuta el siguiente comando para instalar las librerías necesarias (`pandas`, `pyodbc`, `pywin32`, etc.):
```bash
pip install -r requerimientos.txt
```

### 4. Configurar las Credenciales (Archivo `.env`)
En la carpeta raíz del proyecto, debes crear un archivo llamado `.env` (sin nombre, solo la extensión) y colocar tus credenciales de acceso a la base de datos:

```env
DB_SERVER=10.121.5.80,1433
DB_DATABASE=ECU911DMS
DB_USERNAME=tu_usuario
DB_PASSWORD=tu_contraseña
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TIMEOUT=30
DB_ENCRYPT=yes
DB_TRUST_SERVER_CERT=yes
```
*(Nota: El archivo `.env` se recomienda no subirlo a GitHub por seguridad).*

---

## 💻 Uso del Sistema

Para iniciar la aplicación, asegúrate de estar dentro de la carpeta del proyecto y ejecuta:

```bash
python app.py
```

### Funciones principales:
* **Generar Tablas:** Carga la información de una fecha específica seleccionada desde la BD y el Cubo simultáneamente.
* **Comparar Datos:** Realiza un cruce de información detectando qué datos faltan en cada origen o qué centros tienen diferencias en el conteo de incidentes.