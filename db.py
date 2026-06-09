import os
import time
import logging
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
# Configurables via .env / env vars
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "30"))
DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "3"))
DB_RETRY_DELAY = float(os.getenv("DB_RETRY_DELAY", "2"))
DB_ENCRYPT = os.getenv("DB_ENCRYPT", "yes").lower() in ("yes", "true", "1")
DB_TRUST_SERVER_CERT = os.getenv("DB_TRUST_SERVER_CERT", "yes").lower() in ("yes", "true", "1")

encrypt_part = "Encrypt=yes;" if DB_ENCRYPT else "Encrypt=no;"
trust_part = "TrustServerCertificate=yes;" if DB_TRUST_SERVER_CERT else ""
CONN_STR = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USER};PWD={PWD};"
    f"{encrypt_part}{trust_part}"
    f"Connection Timeout={DB_TIMEOUT};"
)


def _connect_once(timeout):
    """Attempt a single connection and return the connection or raise the exception."""
    try:
        return pyodbc.connect(CONN_STR, timeout=timeout)
    except TypeError:
        # Older pyodbc versions may not accept timeout kw; set on connection object
        conn = pyodbc.connect(CONN_STR)
        try:
            conn.timeout = timeout
        except Exception:
            # Some drivers/versions may not support setting timeout; ignore
            pass
        return conn


def get_connection(timeout=None, retries=None, delay=None):
    """Get a DB connection with retries and clearer errors.

    Parameters are optional and default to env-configured values.
    """
    if timeout is None:
        timeout = DB_TIMEOUT
    if retries is None:
        retries = DB_CONNECT_RETRIES
    if delay is None:
        delay = DB_RETRY_DELAY

    logger = logging.getLogger("db")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"DB connect attempt %d/%d (timeout=%s)", attempt, retries, timeout)
            conn = _connect_once(timeout)
            logger.info("DB connection established")
            return conn
        except pyodbc.Error as e:
            last_exc = e
            logger.warning("DB connect failed on attempt %d: %s", attempt, e)
            if attempt < retries:
                time.sleep(delay * attempt)

    # If we reach here, all attempts failed — raise a clearer exception
    raise ConnectionError(
        f"Unable to connect to database {SERVER} after {retries} attempts. "
        f"Last error: {last_exc}")

def conn_info():
    return {"server": SERVER, "database": DATABASE, "driver": DRIVER}


def available_drivers():
    """Return installed ODBC drivers (for diagnostics)."""
    try:
        return pyodbc.drivers()
    except Exception:
        return []


def diagnose_connection(try_drivers=None, try_encrypt_options=True, timeout=None):
    """Run diagnostic connection attempts and return dict with results.

    - try_drivers: list of driver names to try (if None, will probe installed drivers and try current DRIVER plus common ones)
    - try_encrypt_options: if True, also try toggling Encrypt on/off
    """
    results = {"probed_drivers": available_drivers(), "attempts": []}
    if timeout is None:
        timeout = DB_TIMEOUT

    probe_drivers = [] if try_drivers is None else list(try_drivers)
    # ensure current driver is first
    if DRIVER not in probe_drivers:
        probe_drivers.insert(0, DRIVER)
    # add common alternative
    for alt in ("ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"):
        if alt not in probe_drivers:
            probe_drivers.append(alt)

    for drv in probe_drivers:
        for encrypt in ([True, False] if try_encrypt_options else [DB_ENCRYPT]):
            conn_str = (
                f"DRIVER={{{drv}}};"
                f"SERVER={SERVER};"
                f"DATABASE={DATABASE};"
                f"UID={USER};PWD={PWD};"
                f"Encrypt={'yes' if encrypt else 'no'};"
                f"TrustServerCertificate={'yes' if DB_TRUST_SERVER_CERT else 'no'};"
                f"Connection Timeout={timeout};"
            )
            attempt = {"driver": drv, "encrypt": encrypt, "conn_str": conn_str, "ok": False, "error": None}
            try:
                # try connect with compatibility for timeout kw
                try:
                    conn = pyodbc.connect(conn_str, timeout=timeout)
                except TypeError:
                    conn = pyodbc.connect(conn_str)
                    try:
                        conn.timeout = timeout
                    except Exception:
                        pass
                conn.close()
                attempt["ok"] = True
            except Exception as e:
                attempt["error"] = str(e)
            results["attempts"].append(attempt)

    return results
