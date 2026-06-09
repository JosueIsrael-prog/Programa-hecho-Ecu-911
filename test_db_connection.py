import traceback
from db import get_connection, diagnose_connection, available_drivers


def print_diag():
    print('Installed ODBC drivers:')
    for d in available_drivers():
        print(' -', d)
    print('\nRunning diagnostic attempts (driver 18/17 and encrypt on/off)...')
    res = diagnose_connection()
    for a in res.get('attempts', []):
        ok = 'OK' if a.get('ok') else 'FAIL'
        print(f"Driver={a.get('driver')}, Encrypt={a.get('encrypt')}: {ok}")
        if a.get('error'):
            print('  Error:', a.get('error'))


if __name__ == '__main__':
    print_diag()
    try:
        conn = get_connection()
        print('DB connection established:', conn)
        conn.close()
    except Exception as e:
        print('DB connection failed:')
        traceback.print_exc()
