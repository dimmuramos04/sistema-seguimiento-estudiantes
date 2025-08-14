# database.py
import sqlite3
import os
from datetime import date
from werkzeug.security import generate_password_hash
import pandas as pd
import numpy as np

# --- Constantes para las Listas Desplegables ---
# (Las listas de constantes permanecen sin cambios)
LISTA_GENERO = ["Femenino", "Masculino", "No binario", "Otro", "Prefiero no indicar", "No registrado"]
LISTA_SEXO = ["Femenino", "Masculino", "Intersexual", "No registrado"]
LISTA_FACULTADES = [
    "Facultad de Ciencias",
    "Facultad de Ciencias Sociales, Empresariales y Jurídicas",
    "Facultad de Humanidades",
    "Facultad de Ingeniería",
    "Programa de Postgrado y Postítulo",
    "Otro",
    "No registrado"
]
LISTA_CARRERAS = [
    "Administración Pública", "Administración Turística", "Arquitectura", "Auditoría", "Derecho", "Diseño",
    "Diseño Mención Comunicación/Equipamiento", "Diplomado en Desarrollo y Gestión de Intervención en el Espacio Público",
    "Diplomado en Docencia en Educación Superior", "Diplomado en Gestión Ambiental y Sustentabilidad Energética",
    "Diplomado en Rehabilitación Oral Adhesiva y Digital", "Diplomado Gestión Curricular en Educación Superior",
    "Doctorado en Alimentos y Bioprocesos", "Doctorado en Astronomía", "Doctorado en Biología y Ecología Aplicada",
    "Doctorado en Ciencias Biológicas Mención Ecología de Zonas Áridas", "Doctorado en Ciencias Mención Física",
    "Doctorado en Educación", "Doctorado en Energía, Agua y Medio Ambiente", "Doctorado en Psicología", "Enfermería",
    "Ingeniería Agronómica", "Ingeniería Civil", "Ingeniería Civil Ambiental", "Ingeniería Civil de Minas",
    "Ingeniería Civil en Computación e Informática", "Ingeniería Civil Industrial", "Ingeniería Civil Mecánica",
    "Ingeniería Comercial", "Ingeniería de Ejecución en Minas", "Ingeniería de Ejecución Mecánica",
    "Ingeniería de Minas", "Ingeniería en Administración de Empresas", "Ingeniería en Alimentos",
    "Ingeniería en Biotecnología Mención en Alimentos o Procesos Sustentables", "Ingeniería en Computación",
    "Ingeniería en Construcción", "Ingeniería Mecánica", "Kinesiología", "Licenciatura en Astronomía",
    "Licenciatura en Física", "Licenciatura en Matemáticas", "Licenciatura en Música", "Licenciatura en Química",
    "Magíster en Astronomía", "Magíster en Ciencias Biológicas Mención Ecología de Zonas Áridas",
    "Magíster en Ciencias Físicas", "Magíster en Ciencias Mención Ingeniería en Alimentos",
    "Magíster en Estudios del Discurso", "Magíster en Gestión Educacional", "Magíster en Liderazgo",
    "Magíster en Matemáticas", "Magíster en Mecánica Computacional", "Odontología",
    "Pedagogía en Biología y Ciencias Naturales", "Pedagogía en Castellano y Filosofía",
    "Pedagogía en Educación Diferencial", "Pedagogía en Educación General Básica", "Pedagogía en Educación General Básica Limarí", "Pedagogía en Educación Musical",
    "Pedagogía en Educación Parvularia", "Pedagogía en Historia y Geografía", "Pedagogía en Inglés",
    "Pedagogía en Matemáticas", "Pedagogía en Matemáticas y Computación", "Pedagogía en Matemáticas y Física",
    "Pedagogía en Química y Ciencias Naturales", "Periodismo", "Psicología", "Química", "Químico Laboratorista",
    "Traducción Inglés-Español", "No Registrado"
]
LISTA_TRABAJADORAS_SOCIALES = [
    "Marisol Avilés", "Patricia Astroza", "Paula Araya", "Natalia Mondaca",
    "Carolina Muñoz", "Sandra Tapia", "Romina Ugalde", "Victoria Viera"
]
LISTA_PSICOLOGOS = [
    "Cristian Echeverría", "Daniela Rojas", "Marianela Riffo", "Valentina Miranda"
]
LISTA_CESFAM = [
    "ATENCIÓN PARTICULAR", "CDT H. LA SERENA", "CECOSF ARCOS DE PINAMAR", "CECOSF VILLA ALEMANA", "CECOSF VILLA LAMBERT", "CESAM LA SERENA",
    "CESFAM C. CARO", "CESFAM CANELA", "CESFAM DR. SERGIO AGUILAR DELGADO", "CESFAM E. SCHAFFAUSSER", "CESFAM EL SAUCE",
    "CESFAM FRAY JORGE", "CESFAM JUAN PABLO II", "CESFAM JORGE JORDÁN", "CESFAM LA HIGUERA", "CEASFAM LAS COMPAÑIAS",
    "CESFAM LAS COMPAÑIAS", "CESFAM LILA CORTÉS GODOY", "CESFAM MARCOS MACUADA", "CESFAM MONTE PATRIA", "CESFAM OVALLE",  "CESFAM PAN DE AZUCAR",
    "CESFAM PEDRO AGUIRRE CERDA", "CESFAM PUNITAQUI", "CESFAM R.S. HENRÍQUEZ", "CESFAM SAN JUAN", "CESFAM SANTA CECILIA",
    "CESFAM SERGIO AGUILAR", "CESFAM TIERRAS BLANCAS", "CESFAM TONGOY", "CESFAM URBANO ILLAPEL", "CESFAM VILLA LAMBERT",
    "DIPRECA", "H. LA SERENA", "H. VICUÑA", "POSTA RURAL EL ROMERO", "SAR E. SCHAFFAUSSER (CALLE COLÓN)", "SAR MARCOS MACUADA", "SAR MONTE PATRIA",
    "SAR R.S. HENRÍQUEZ", "SAR TIERRAS BLANCAS", "No registrado"
]
LISTA_TENTATIVA_IDEACION = ["Ideación", "Tentativa"]
LISTA_ESTADO_PROGRAMA = ["Activo", "Activo (Reingreso)", "No acepta ingresar", "Desertó", "Alta del programa", "No sigue en en el programa por estado académico incompatible","Archivado", "No registrado"]
LISTA_ESTADO_DERIVACION_INICIAL = [
    "Aún no gestiona derivación", "Concretó la Derivación", "Se rehúsa a gestionar", "Gestiona apoyo privado", "No registrado"
]
LISTA_TIPO_INTERVENCION = [
    "Sesión Online", "Contacto Telefónico", "Contacto por Correo Electrónico",
    "Coordinación con Red de Apoyo (Familia, etc.)", "Coordinación con Centro de Salud", "Otro",
    "No se concretó la entrevista agendada", "No registrado"
]
LISTA_RESULTADO_CITA = [
    "Realizada", "No Asiste (Justificado)", "No Asiste (Sin Justificación)", "Estudiante Reagenda", "Otro", "No registrado"
]
LISTA_ASISTENCIA_CONTROLES_CESFAM = [
    "Si ha asistido", "Ha tenido problemas para conseguir hora", "Ha decidido dejar de asistir",
    "Asiste a una instancia particular", "No registrado"
]
LISTA_ESTADO_ACADEMICO = [
    "Puede Reservar Cupos", "Regular", "Suspensión de Estudios", "Postergación de Estudios", "Eliminación por RRE",
    "Abandono", "Renuncia", "Tesista", "Graduado/Titulado", "No registrado"
]
LISTA_ESTADO_CIVIL = ["Soltero/a", "Casado/a", "Conviviente civil", "Separado/a judicialmente", "Viudo/a", "Divorciado/a", "No registrado"]
LISTA_OCUPACION_LABORAL = ["Cesante", "Trabajador/a dependiente", "Trabajador/a independiente", "Informalidad laboral", "Microemprendimiento", "No registrado"]
LISTA_TIENE_HIJOS = ["No", "Sí", "Prefiero no indicar", "No registrado"]
LISTA_NACIONALIDADES = [
    "Chilena", "Peruana", "Boliviana", "Argentina", "Colombiana", "Paraguaya", "Venezolana", "Ecuatoriana",
    "Brasileña", "Haitiana", "Mexicana", "Estadounidense", "Española", "Francesa", "Alemana", "China", "Otra", "No registrado"
]
LISTA_FUENTE_DERIVACION = [
    "Solicitó hora al Dpto de Salud", "Trabajadora Social del Dpto de Bienestar",
    "Director/a, Coordinador/a o Docente de la carrera", "Profesionales de OAME",
    "Profesionales del área de Discapacidad de la AGDFI", "Profesionales del Dpto de Equidad y Género",
    "Otro", "No registrado"
]
LISTA_BENEFICIO_ARANCEL = [
    "Gratuidad", "Beca Vocación de Profesor", "Beca Bicentenario", "FSCU", "CAE", "FIA", "Becas ANID",
    "Becas Internas de Postgrado", "Sin Beneficio", "Otros", "No registrado"
]
LISTA_PARENTESCO = ["Madre", "Padre", "Abuela/o", "Tía/o", "Hermano/a", "Amigo/a", "Pareja", "Otro", "No registrado"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, 'seguimiento.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def seed_data():
    """Inserta datos desde Excel, manejando correctamente los valores nulos (NaN)."""
    print("Intentando sembrar datos...")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(id) FROM Usuarios")
    if cursor.fetchone()[0] > 0:
        conn.close()
        print("La base de datos ya tiene datos. No se necesita sembrar.")
        return
    
    print("Base de datos vacía. Sembrando datos nuevos...")
    try:
        # 1. Sembrar Usuarios
        usuarios = [
            ('admin', generate_password_hash('admin123', method='pbkdf2:sha256'), 'admin', 'Admin General', 1),
            ('profesional1', generate_password_hash('profe123', method='pbkdf2:sha256'), 'profesional', 'Patricia Astroza', 1)
        ]
        cursor.executemany("INSERT INTO Usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)", usuarios)
        print(f"{len(usuarios)} usuarios de prueba insertados.")

        excel_path = os.path.join(BASE_DIR, 'datos_iniciales.xlsx')
        if not os.path.exists(excel_path):
            print("ADVERTENCIA: No se encontró el archivo 'datos_iniciales.xlsx'.")
        else:
            # --- Procesar Hoja 'Estudiantes' ---
            print("\n--- Procesando hoja 'Estudiantes' ---")
            df_estudiantes = pd.read_excel(excel_path, sheet_name='Estudiantes')
            
            # Convertir columnas de fecha, manejando errores
            columnas_fecha_est = ['fecha_nacimiento', 'fecha_ingreso_programa', 'fecha_derivacion_cesfam', 'fecha_autorizacion_investigacion']
            for col in columnas_fecha_est:
                df_estudiantes[col] = pd.to_datetime(df_estudiantes[col], errors='coerce', dayfirst=True).dt.strftime('%Y-%m-%d')
            
            # *** CAMBIO CLAVE AQUÍ ***
            # Reemplazar todos los tipos de nulos de Pandas (NaN, NaT) por None de Python.
            # El truco de .astype(object) asegura que la conversión se pueda hacer sin conflictos de tipo.
            df_estudiantes = df_estudiantes.astype(object).where(pd.notnull(df_estudiantes), None)
            
            estudiantes_para_insertar = list(df_estudiantes.to_records(index=False))
            cursor.executemany("INSERT INTO Estudiantes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", estudiantes_para_insertar)
            print(f"{len(estudiantes_para_insertar)} estudiantes insertados desde Excel.")

            # --- Procesar Hoja 'Seguimientos' ---
            print("\n--- Procesando hoja 'Seguimientos' ---")
            df_seguimientos = pd.read_excel(excel_path, sheet_name='Seguimientos')
            
            # Convertir columnas numéricas a un tipo que soporta nulos (Int64)
            columnas_numericas = ['alta_mejora_animo', 'alta_disminucion_riesgo', 'alta_redes_apoyo', 'alta_adherencia_tratamiento', 'alta_no_registrado', 'es_correccion', 'corrige_id_seguimiento']
            for col in columnas_numericas:
                df_seguimientos[col] = pd.to_numeric(df_seguimientos[col], errors='coerce').astype('Int64')
            
            # Convertir columnas de fecha
            columnas_fecha_seg = ['fecha_sesion', 'extension_programa_otorgada']
            for col in columnas_fecha_seg:
                df_seguimientos[col] = pd.to_datetime(df_seguimientos[col], errors='coerce', dayfirst=True).dt.strftime('%Y-%m-%d')
            
            # *** CAMBIO CLAVE AQUÍ (misma lógica que antes) ***
            # Esto convierte NaN, NaT, y pd.NA a None, que es lo que SQL entiende como NULL.
            df_seguimientos = df_seguimientos.astype(object).where(pd.notnull(df_seguimientos), None)

            seguimientos_para_insertar = list(df_seguimientos.to_records(index=False))
            
            # Consulta SQL para insertar en la tabla Seguimientos
            cursor.executemany("""
                INSERT INTO Seguimientos (
                    rut_estudiante, trabajadora_social_sesion, psicologo_sesion, fecha_sesion, 
                    estado_derivacion_cesfam_actual, tipo_intervencion, resultado_cita, 
                    confirmacion_gestion_hora_cesfam, fechas_sesiones_cesfam, bitacora_sesion, 
                    cambio_estado_programa_a, cambio_estado_academico_a, creado_por_usuario, 
                    alta_mejora_animo, alta_disminucion_riesgo, alta_redes_apoyo, 
                    alta_adherencia_tratamiento, alta_no_registrado, extension_programa_otorgada, 
                    es_correccion, corrige_id_seguimiento
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, seguimientos_para_insertar)
            print(f"{len(seguimientos_para_insertar)} seguimientos insertados desde Excel.")
        
        conn.commit()
        print("\nDatos sembrados exitosamente.")
    except Exception as e:
        import traceback
        print(f"Error al sembrar datos: {e}")
        traceback.print_exc()
        conn.rollback()
    finally:
        if conn:
            conn.close()

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen (Sintaxis SQLite)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Definiciones de las tablas (sin cambios)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Estudiantes (
        rut TEXT PRIMARY KEY, nombre TEXT NOT NULL, apellido_paterno TEXT NOT NULL, apellido_materno TEXT NOT NULL,
        genero TEXT, fecha_nacimiento DATE, nacionalidad TEXT, estado_civil TEXT, tiene_hijos TEXT,
        carrera_programa TEXT, estado_academico TEXT, ocupacion_laboral TEXT, residencia_academica TEXT,
        residencia_familiar TEXT, celular TEXT, trabajadora_social_asignada TEXT, psicologo_asignado TEXT,
        fecha_ingreso_programa DATE, fuente_derivacion TEXT, estado_en_programa TEXT, fecha_derivacion_cesfam DATE,
        cesfam_derivacion TEXT, tentativa_ideacion TEXT, fecha_autorizacion_investigacion DATE,
        nombre_contacto_emergencia TEXT, parentesco_contacto_emergencia TEXT, telefono_contacto_emergencia TEXT,
        beneficio_arancel TEXT, estado_derivacion_maestro TEXT NOT NULL DEFAULT 'Aún no gestiona derivación'
    )''')
    print("Tabla Estudiantes (SQLite) verificada/creada.")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Seguimientos (
        id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT, rut_estudiante TEXT NOT NULL,
        trabajadora_social_sesion TEXT, psicologo_sesion TEXT, fecha_sesion DATE NOT NULL,
        estado_derivacion_cesfam_actual TEXT, tipo_intervencion TEXT, resultado_cita TEXT,
        confirmacion_gestion_hora_cesfam TEXT, fechas_sesiones_cesfam TEXT, bitacora_sesion TEXT,
        cambio_estado_programa_a TEXT, cambio_estado_academico_a TEXT, creado_por_usuario TEXT,
        alta_mejora_animo INTEGER DEFAULT 0, alta_disminucion_riesgo INTEGER DEFAULT 0,
        alta_redes_apoyo INTEGER DEFAULT 0, alta_adherencia_tratamiento INTEGER DEFAULT 0,
        alta_no_registrado INTEGER DEFAULT 0, extension_programa_otorgada DATE,
        es_correccion INTEGER DEFAULT 0, corrige_id_seguimiento INTEGER,
        FOREIGN KEY (rut_estudiante) REFERENCES Estudiantes (rut)
    )''')
    print("Tabla Seguimientos (SQLite) verificada/creada.")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PeriodosAtencion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rut_estudiante TEXT NOT NULL,
        fecha_ingreso TEXT NOT NULL,
        motivo_ingreso TEXT NOT NULL, -- 'Ideación' o 'Tentativa'
        estado_periodo TEXT NOT NULL, -- 'Activo', 'Activo (Reingreso)', 'Alta', 'Archivado', etc.
        fecha_alta TEXT,
        FOREIGN KEY (rut_estudiante) REFERENCES Estudiantes (rut)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        rol TEXT NOT NULL, nombre_completo TEXT, activo INTEGER NOT NULL DEFAULT 1
    )''')
    print("Tabla Usuarios (SQLite) verificada/creada.")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS HistorialCambios (
        id_cambio INTEGER PRIMARY KEY AUTOINCREMENT, fecha_cambio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        nombre_usuario TEXT NOT NULL, accion TEXT NOT NULL, modelo_afectado TEXT NOT NULL,
        id_registro_afectado TEXT NOT NULL, detalles TEXT
    )''')
    print("Tabla HistorialCambios (SQLite) verificada/creada.")

    conn.commit()
    conn.close()
    print("Tablas SQLite inicializadas/verificadas.")

    # Llama a la función para sembrar los datos si la BD está vacía
    seed_data()

if __name__ == '__main__':
    init_db()
    print(f"Base de datos SQLite en '{DATABASE_NAME}' inicializada y tablas creadas/verificadas.")
