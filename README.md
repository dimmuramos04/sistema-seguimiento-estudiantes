* Objetivo del Proyecto
Sistema de Ingreso y Seguimiento de Estudiantes para el programa de Acompañamiento y Seguimiento.
Permite registrar estudiantes, sus seguimientos y generar reportes.

* Tecnologías usadas
Backend en Python con Flask, Frontend con plantillas HTML/Jinja2, Base de datos SQLite.

* Instalación y ejecución
1. Clonar el repositorio.
2. Crear un entorno virtual. 
3. Instalar las dependencias con pip install -r requirements.txt.
4. En caso de que hayan datos previos, tenerlos ordenados en un excel según el orden de la tabla creada en la aplicación. 
4. Ejecutar el script init_server_db.py para crear la base de datos. 
5. Recargar la aplicación web.

* Usuarios de prueba
Para acceder, usar: usuario admin, contraseña 5114501-Maxi.

* Funcionalidades principales
1. Registro y edición de estudiantes en el Programa de Acompañamiento y Seguimiento.
2. Sistema de usuarios con roles (admin, profesional e ingrerso), según las responsabilidades que tengan en el Programa.
3. Dashboard con estadísticas visuales tales como; gráfico de torta respecto a la cantidad de estudiantes que están en cierto estado (Activo, Alta del Programa, etc.), las 10 carreras con más estudiantes estén o hayan pasado por el Programa, cantidad de seguimientos por mes/año y cantidad de estudiantes que ingresaron por ideación o tentativa por año.
4. Registro y edición de los seguimientos de estudiantes en el Programa de Acompañamiento y Seguimiento.
5. Descarga de datos en formato CSV.

* Estructura del Proyecto
1. app.py: Contiene la lógica principal de la aplicación y las rutas.
2. database.py: Define el esquema de la base de datos y la carga inicial de datos.
3. fronted.py: Define los formularios web
4. /templates: Contiene todas las plantillas HTML

* Autor
Sebastián Andrés Ramos Ortiz

* Contacto
sebastian.ramoso@userena.cl
