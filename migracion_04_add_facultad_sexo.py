# migracion_04_add_facultad_sexo.py
import sqlite3

DATABASE_NAME = 'seguimiento.db'
print("Iniciando migración para añadir 'facultad' y 'sexo' a la tabla Estudiantes...")

try:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Verificamos la existencia de las columnas antes de intentar añadirlas
    cursor.execute("PRAGMA table_info(Estudiantes)")
    columns = [row[1] for row in cursor.fetchall()]

    # Añadir la columna 'facultad' si no existe
    if 'facultad' not in columns:
        print("Añadiendo columna 'facultad'...")
        # La clave está aquí: NOT NULL DEFAULT 'No registrado'
        cursor.execute("ALTER TABLE Estudiantes ADD COLUMN facultad TEXT NOT NULL DEFAULT 'No registrado'")
        print("Columna 'facultad' añadida exitosamente.")
    else:
        print("La columna 'facultad' ya existe.")

    # Añadir la columna 'sexo' si no existe
    if 'sexo' not in columns:
        print("Añadiendo columna 'sexo'...")
        cursor.execute("ALTER TABLE Estudiantes ADD COLUMN sexo TEXT NOT NULL DEFAULT 'No registrado'")
        print("Columna 'sexo' añadida exitosamente.")
    else:
        print("La columna 'sexo' ya existe.")

    conn.commit()
    print("Migración completada.")

except Exception as e:
    print(f"Ocurrió un error durante la migración: {e}")
finally:
    if conn:
        conn.close()