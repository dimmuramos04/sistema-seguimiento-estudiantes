# migracion_03_add_nota_estudiante.py
import sqlite3

DATABASE_NAME = 'seguimiento.db'
print("Iniciando migración para añadir 'nota_importante' a la tabla Estudiantes...")

try:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Verificamos si la columna ya existe para evitar errores
    cursor.execute("PRAGMA table_info(Estudiantes)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'nota_importante' not in columns:
        print("La columna 'nota_importante' no existe. Añadiéndola...")
        # Si no existe, la añadimos. TEXT permite notas largas.
        cursor.execute("ALTER TABLE Estudiantes ADD COLUMN nota_importante TEXT")
        conn.commit()
        print("¡Éxito! La columna 'nota_importante' fue añadida a la tabla Estudiantes.")
    else:
        print("La columna 'nota_importante' ya existe. No se necesita ninguna acción.")

except Exception as e:
    print(f"Ocurrió un error durante la migración: {e}")
finally:
    if conn:
        conn.close()