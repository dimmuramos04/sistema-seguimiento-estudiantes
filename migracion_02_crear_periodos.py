# migracion_02_periodos_atencion.py
import sqlite3

DATABASE_NAME = 'seguimiento.db'
print("Iniciando migración para la tabla PeriodosAtencion...")

try:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # --- Parte 1: Crear la tabla (solo si no existe) ---
    print("Paso 1: Asegurando que la tabla 'PeriodosAtencion' exista...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PeriodosAtencion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rut_estudiante TEXT NOT NULL,
        fecha_ingreso TEXT NOT NULL,
        motivo_ingreso TEXT NOT NULL, -- 'Ideación' o 'Tentativa'
        estado_periodo TEXT NOT NULL, -- 'Activo', 'Activo (Reingreso)', 'Alta', etc.
        fecha_alta TEXT,
        FOREIGN KEY (rut_estudiante) REFERENCES Estudiantes (rut)
    )
    ''')
    print("Tabla 'PeriodosAtencion' verificada/creada exitosamente.")

    # --- Parte 2: Migrar los datos existentes ---
    print("\nPaso 2: Migrando datos de ingreso iniciales...")

    # Leer los datos de ingreso de la tabla Estudiantes
    cursor.execute("SELECT rut, fecha_ingreso_programa, tentativa_ideacion, estado_en_programa FROM Estudiantes")
    estudiantes = cursor.fetchall()

    migrados = 0
    for rut, fecha_ingreso, motivo, estado in estudiantes:
        # Verificar que el estudiante no tenga ya un período inicial migrado
        cursor.execute("SELECT COUNT(*) FROM PeriodosAtencion WHERE rut_estudiante = ?", (rut,))
        if cursor.fetchone()[0] == 0:
            if fecha_ingreso and motivo and estado: # Solo migrar si los datos existen
                cursor.execute('''
                    INSERT INTO PeriodosAtencion (rut_estudiante, fecha_ingreso, motivo_ingreso, estado_periodo)
                    VALUES (?, ?, ?, ?)
                ''', (rut, fecha_ingreso, motivo, estado))
                migrados += 1

    conn.commit()
    print(f"¡Éxito! Se han migrado los datos de {migrados} nuevos estudiantes a la tabla.")

except Exception as e:
    print(f"Ocurrió un error durante la migración: {e}")
finally:
    if conn:
        conn.close()