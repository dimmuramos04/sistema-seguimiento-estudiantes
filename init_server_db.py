# init_server_db.py
import os
from database import init_db, DATABASE_NAME

# Primero, eliminamos la base de datos vieja si existe,
# para asegurar una creación limpia.
if os.path.exists(DATABASE_NAME):
    print(f"Eliminando base de datos existente: {DATABASE_NAME}")
    os.remove(DATABASE_NAME)
    print("Base de datos eliminada.")

print("\nIniciando la creación y siembra de la nueva base de datos...")

# Llamamos a la función que ya tienes, que crea las tablas y siembra los datos.
init_db()

print("\n¡Proceso completado!")
print(f"La base de datos '{DATABASE_NAME}' ha sido creada y poblada exitosamente.")