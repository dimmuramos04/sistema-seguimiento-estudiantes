# util_limpiar_datos.py
import sqlite3

DATABASE_NAME = 'seguimiento.db'
print("Iniciando script de limpieza de datos...")

try:
    conn = sqlite3.connect(DATABASE_NAME)
    # Importante: Usamos sqlite3.Row para acceder a las filas por nombre de columna
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Columnas de texto que queremos limpiar (quitar espacios al inicio y final)
    columnas_a_limpiar = [
        'genero', 'sexo', 'facultad', 'carrera_programa', 
        'estado_academico', 'nacionalidad', 'estado_civil',
        'trabajadora_social_asignada', 'psicologo_asignado'
    ]

    print("Obteniendo todos los registros de estudiantes...")
    #nosec
    cursor.execute("SELECT rut, " + ", ".join(columnas_a_limpiar) + " FROM Estudiantes")
    estudiantes = cursor.fetchall()

    print(f"Se procesarán {len(estudiantes)} estudiantes.")
    cambios_realizados = 0

    for estudiante in estudiantes:
        rut = estudiante['rut']
        actualizaciones = []
        valores = []

        for columna in columnas_a_limpiar:
            valor_original = estudiante[columna]
            # Verificamos que el valor no sea nulo antes de intentar limpiarlo
            if valor_original:
                valor_limpio = valor_original.strip() # .strip() quita los espacios
                
                # Si el valor limpio es diferente al original, preparamos la actualización
                if valor_limpio != valor_original:
                    actualizaciones.append(f"{columna} = ?")
                    valores.append(valor_limpio)
        
        # Si encontramos al menos un campo para actualizar en este estudiante...
        if actualizaciones:
            valores.append(rut) # Añadimos el RUT al final para el WHERE
            #nosec
            query_update = f"UPDATE Estudiantes SET {', '.join(actualizaciones)} WHERE rut = ?"
            
            cursor.execute(query_update, tuple(valores))
            cambios_realizados += 1
            print(f"  -> Se corrigieron datos para el RUT: {rut}")

    conn.commit()
    
    if cambios_realizados > 0:
        print(f"\n¡Éxito! Se limpiaron los datos de {cambios_realizados} estudiantes.")
    else:
        print("\nNo se encontraron datos que necesitaran limpieza. ¡Tu base de datos está en buen estado!")

except Exception as e:
    if conn:
        conn.rollback()
    print(f"Ocurrió un error durante la limpieza: {e}")
finally:
    if conn:
        conn.close()