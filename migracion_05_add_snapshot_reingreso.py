# migracion_05_add_snapshot_reingreso.py
import sqlite3

DATABASE_NAME = 'seguimiento.db'
print("Iniciando migración para añadir campos de snapshot a PeriodosAtencion...")

try:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # --- Parte 1: Añadir las nuevas columnas si no existen ---
    cursor.execute("PRAGMA table_info(PeriodosAtencion)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    nuevas_columnas = {
        'carrera_periodo': 'TEXT',
        'facultad_periodo': 'TEXT',
        'estado_academico_periodo': 'TEXT'
    }

    for col, tipo in nuevas_columnas.items():
        if col not in columns:
            print(f"Añadiendo columna '{col}'...")
            # Las añadimos permitiendo que estén vacías inicialmente
            cursor.execute(f"ALTER TABLE PeriodosAtencion ADD COLUMN {col} {tipo}")
            print(f"Columna '{col}' añadida.")
        else:
            print(f"La columna '{col}' ya existe.")

    # --- Parte 2: Rellenar los datos para los periodos existentes (Backfill) ---
    print("\nActualizando periodos de atención existentes con datos académicos...")
    
    # Seleccionamos los periodos que no tienen información académica
    cursor.execute("""
        SELECT pa.id, e.carrera_programa, e.facultad, e.estado_academico 
        FROM PeriodosAtencion pa
        JOIN Estudiantes e ON pa.rut_estudiante = e.rut
        WHERE pa.carrera_periodo IS NULL
    """)
    periodos_a_actualizar = cursor.fetchall()

    if periodos_a_actualizar:
        for periodo in periodos_a_actualizar:
            cursor.execute("""
                UPDATE PeriodosAtencion 
                SET carrera_periodo = ?, facultad_periodo = ?, estado_academico_periodo = ?
                WHERE id = ?
            """, (periodo['carrera_programa'], periodo['facultad'], periodo['estado_academico'], periodo['id']))
        conn.commit()
        print(f"Se han actualizado {len(periodos_a_actualizar)} registros de periodos existentes.")
    else:
        print("No hay periodos existentes que necesiten ser actualizados.")

    print("\nMigración completada exitosamente.")

except Exception as e:
    if conn:
        conn.rollback()
    print(f"Ocurrió un error durante la migración: {e}")
finally:
    if conn:
        conn.close()