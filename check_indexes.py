import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Ver índices de la tabla app_registrotiempo
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='app_registrotiempo';")
indices = cursor.fetchall()

print("Índices en app_registrotiempo:")
for idx in indices:
    print(f"  - {idx[0]}")

conn.close()
