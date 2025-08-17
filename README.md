# Sistema de Gestión y Seguimiento de Estudiantes

Sistema web desarrollado en Flask para el registro, seguimiento y gestión de estudiantes del Programa de Acompañamiento y Seguimiento, enfocado en la prevención del suicidio.

## Características Principales

### Gestión de Estudiantes
- **Registro Completo:** Creación de fichas de estudiantes con datos personales, académicos y de contacto.
- **Edición de Datos:** Modificación de la información de los estudiantes.
- **Historial de Cambios:** Registro automático de las modificaciones realizadas en la ficha del estudiante.
- **Reingreso de Estudiantes:** Permite registrar un nuevo periodo de atención para estudiantes que retornan al programa.
- **Eliminación Segura:** Funcionalidad para eliminar estudiantes y todos sus datos asociados (restringido a administradores).

### Gestión de Seguimientos
- **Registro de Sesiones:** Creación de seguimientos detallados por cada estudiante, incluyendo bitácoras y resultados.
- **Edición de Seguimientos:** Corrección y actualización de los registros de seguimiento.
- **Corrección de Registros:** Permite marcar un seguimiento como una corrección de uno anterior, manteniendo la integridad de los datos.
- **Alertas Visuales:** Indicadores en la interfaz para seguimientos importantes o pendientes.

### Gestión de Usuarios y Roles
- **Sistema de Autenticación:** Login seguro para acceder al sistema.
- **Roles de Usuario:** Tres roles con distintos niveles de permiso:
    - `admin`: Control total del sistema, incluyendo gestión de usuarios.
    - `profesional`: Acceso a los estudiantes que tiene asignados, para registrar y editar seguimientos.
    - `ingreso`: Permiso para registrar nuevos estudiantes en el sistema.
- **Panel de Administración:** Interfaz para que los administradores puedan crear, editar, activar/desactivar y eliminar cuentas de usuario.

### Reportes y Visualización de Datos
- **Dashboard Interactivo:** Panel con gráficos dinámicos sobre:
    - Estado actual de los estudiantes en el programa.
    - Top 10 de carreras con más estudiantes atendidos.
    - Número de seguimientos realizados por mes.
    - Comparativa anual de ingresos por ideación vs. tentativa.
- **Generador de Reportes:** Página para crear reportes personalizados por rango de fechas y agrupar los datos por distintos criterios (género, carrera, etc.).
- **Exportación de Datos:** Descarga de la base de datos de estudiantes, seguimientos y periodos de atención en formato CSV.

### Seguridad
- **Protección CSRF y XSS:** Implementado con Flask-Talisman para mitigar ataques comunes.
- **Cookies Seguras:** Configuración de cookies de sesión con atributos `Secure`, `HttpOnly` y `SameSite`.
- **Hashing de Contraseñas:** Almacenamiento seguro de contraseñas usando `pbkdf2:sha256`.

## Stack Tecnológico
- **Backend:** Python 3
- **Framework:** Flask
- **Base de Datos:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Librerías Principales:**
    - Flask-Login (Manejo de sesiones)
    - Flask-WTF (Formularios)
    - Flask-Talisman (Seguridad)
    - Chart.js (Gráficos)

## Instalación y Puesta en Marcha

**Nota de Seguridad:** Se han eliminado las credenciales de prueba que estaban en este archivo. Es una mala práctica de seguridad exponer usuarios y contraseñas. Se recomienda crear usuarios de prueba directamente en la aplicación usando una cuenta de administrador.

1.  **Clonar el Repositorio**
    ```bash
    git clone <URL-DEL-REPOSITORIO>
    cd seguimiento_estudiantes
    ```

2.  **Crear y Activar Entorno Virtual**
    ```bash
    # Crear el entorno
    python -m venv .venv
    # Activar en Windows
    .\.venv\Scripts\activate
    # Activar en macOS/Linux
    source .venv/bin/activate
    ```

3.  **Crear Archivo de Variables de Entorno**
    - Crea un archivo llamado `.env` en la raíz del proyecto.
    - Agrega la siguiente línea, reemplazando `'tu_clave_secreta_aqui'` por una cadena de texto larga y aleatoria. Esta clave es fundamental para la seguridad de las sesiones.
    ```
    SECRET_KEY='tu_clave_secreta_aqui'
    ```

4.  **Instalar Dependencias**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Inicializar la Base de Datos**
    - Ejecuta el siguiente script **una sola vez** para crear el archivo `database.db` y las tablas necesarias.
    ```bash
    python init_server_db.py
    ```
    - Después de inicializar, puede que necesites ejecutar los scripts de migración en orden si existen (ej. `migracion_02_...`, `migracion_03_...`).

6.  **Crear Usuario Administrador**
    - Una vez creada la base de datos, ejecuta el siguiente script para crear tu cuenta de administrador de forma interactiva y segura.
    ```bash
    python create_admin.py
    ```

7.  **Ejecutar la Aplicación**
    ```bash
    flask run
    ```
    La aplicación estará disponible en `http://127.0.0.1:5000`. Para iniciar sesión, usa las credenciales que creaste en el paso anterior.

## Estructura del Proyecto
- `app.py`: Lógica principal de la aplicación, rutas y controladores.
- `database.py`: Esquema de la base de datos y constantes.
- `forms.py`: Definiciones de los formularios web con WTForms.
- `init_server_db.py`: Script para la creación inicial de la base de datos.
- `requirements.txt`: Lista de dependencias de Python.
- `static/`: Archivos estáticos (CSS, JavaScript, imágenes).
- `templates/`: Plantillas HTML (Jinja2).

## Autor
Sebastián Andrés Ramos Ortiz

## Contacto
sebastian.ramoso@userena.cl