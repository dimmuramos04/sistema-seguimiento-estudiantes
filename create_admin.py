import sqlite3
import os
from getpass import getpass
from werkzeug.security import generate_password_hash

# --- Configuración ---
# Nos aseguramos de que la ruta a la base de datos sea la misma que en la app.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, 'seguimiento.db')

def create_admin():
    """
    Script interactivo para crear el primer usuario administrador.
    """
    print("--- Creación de Usuario Administrador ---")

    if not os.path.exists(DATABASE_NAME):
        print(f"Error: La base de datos '{DATABASE_NAME}' no ha sido encontrada.")
        print("Por favor, ejecuta primero 'python init_server_db.py' para crearla.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # 1. Verificar si ya existe un administrador
        cursor.execute("SELECT COUNT(id) FROM Usuarios WHERE rol = 'admin'")
        if cursor.fetchone()[0] > 0:
            print("Error: Ya existe al menos un usuario administrador en la base de datos.")
            print("Este script es solo para crear el *primer* administrador.")
            return

        print("No se han encontrado administradores. Procediendo a crear el primero.")
        
        # 2. Solicitar datos del nuevo administrador
        username = input("Ingresa el nombre de usuario para el admin: ").strip()
        nombre_completo = input("Ingresa el nombre completo del administrador: ").strip()

        if not username or not nombre_completo:
            print("El nombre de usuario y el nombre completo no pueden estar vacíos.")
            return

        # 3. Solicitar contraseña de forma segura
        while True:
            password = getpass("Ingresa la contraseña (no se mostrará en pantalla): ")
            password_confirm = getpass("Confirma la contraseña: ")

            if not password or not password_confirm:
                print("La contraseña no puede estar vacía. Inténtalo de nuevo.")
                continue
            
            if password != password_confirm:
                print("Las contraseñas no coinciden. Inténtalo de nuevo.")
            else:
                break
        
        # 4. Hashear la contraseña e insertar el usuario
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        cursor.execute(
            "INSERT INTO Usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, 'admin', nombre_completo, 1)
        )
        conn.commit()
        
        print("\n¡Éxito!")
        print(f"Usuario administrador '{username}' creado correctamente.")

    except sqlite3.IntegrityError:
        print(f"\nError: El nombre de usuario '{username}' ya existe. Por favor, ejecuta el script de nuevo con otro nombre.")
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_admin()
