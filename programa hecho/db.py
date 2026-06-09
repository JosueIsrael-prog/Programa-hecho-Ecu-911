import os
import pyodbc

def load_dotenv_simple(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

load_dotenv_simple()

SERVER   = os.getenv("DB_SERVER",   "10.121.5.80,1433")
DATABASE = os.getenv("DB_DATABASE", "ECU911DMS")
USER     = os.getenv("DB_USERNAME", "ereporte")
PWD      = os.getenv("DB_PASSWORD", "3st@distic@")
DRIVER   = os.getenv("DB_DRIVER",   "ODBC Driver 18 for SQL Server")

CONN_STR = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USER};PWD={PWD};"
    "Encrypt=yes;TrustServerCertificate=yes;"
)

def get_connection(timeout=10):
    return pyodbc.connect(CONN_STR, timeout=timeout)

def conn_info():
    return {"server": SERVER, "database": DATABASE, "driver": DRIVER}
