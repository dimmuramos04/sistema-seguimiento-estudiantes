# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, Response, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from forms import LoginForm, NuevoEstudianteForm, CambiarPasswordForm, EditarEstudianteForm, NuevoSeguimientoForm, EditarSeguimientoForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, datetime
import sqlite3
import io
import csv
import json
from database import (
    get_db_connection, init_db,
    LISTA_GENERO, LISTA_CARRERAS, LISTA_TRABAJADORAS_SOCIALES,
    LISTA_PSICOLOGOS, LISTA_CESFAM, LISTA_TENTATIVA_IDEACION, LISTA_ESTADO_PROGRAMA,
    LISTA_ESTADO_DERIVACION_INICIAL, LISTA_ASISTENCIA_CONTROLES_CESFAM,
    LISTA_ESTADO_ACADEMICO, LISTA_ESTADO_CIVIL, LISTA_OCUPACION_LABORAL,LISTA_TIENE_HIJOS, LISTA_NACIONALIDADES,
    LISTA_TIPO_INTERVENCION, LISTA_RESULTADO_CITA, LISTA_FUENTE_DERIVACION, LISTA_BENEFICIO_ARANCEL
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

#init_db()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('No tienes permiso para acceder a esta página. Se requiere rol de administrador.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('login', next=request.url))
            if current_user.rol not in roles_permitidos:
                flash(f'No tienes permiso para acceder a esta página. Se requiere uno de los siguientes roles: {", ".join(roles_permitidos)}.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class User(UserMixin):
    def __init__(self, id, username, password_hash, rol, nombre_completo=None, activo=1):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.rol = rol
        self.nombre_completo = nombre_completo
        self.activo = activo
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Usuarios WHERE id = ?", (int(user_id),))
        user_data = cursor.fetchone()
        if user_data:
            return User(id=user_data['id'], username=user_data['username'],
                        password_hash=user_data['password_hash'], rol=user_data['rol'],
                        nombre_completo=user_data['nombre_completo'], activo=user_data['activo'])
        return None
    except Exception as e:
        print(f"Error en load_user: {e}")
        return None
    finally:
        if conn: conn.close()

# --- Definiciones de Rutas ---
@app.route('/')
@login_required
def index():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # --- PASO 1: Obtener estadísticas GLOBALES primero ---
        # Esta consulta se ejecuta siempre, para todos los roles, y no tiene filtros.
        query_conteo = """
            SELECT
                strftime('%Y', fecha_ingreso_programa) as anio_ingreso,
                COUNT(*) as cantidad_activos
            FROM
                Estudiantes
            WHERE
                estado_en_programa IN ('Activo', 'Activo (Reingreso)')
            GROUP BY
                anio_ingreso
            ORDER BY
                anio_ingreso DESC;
        """
        cursor.execute(query_conteo)
        conteo_activos_por_ano = cursor.fetchall()


        # --- PASO 2: Obtener las alertas, aplicando el filtro por ROL ---
        query_base_alertas = """
            SELECT
                e.rut, e.nombre, e.apellido_paterno, e.apellido_materno,
                MAX(s.fecha_sesion) as ultima_sesion,
                CAST(julianday('now') - julianday(MAX(s.fecha_sesion)) AS INTEGER) as dias_sin_seguimiento
            FROM Estudiantes e
            LEFT JOIN Seguimientos s ON e.rut = s.rut_estudiante
            WHERE e.estado_en_programa LIKE 'Activo%'
        """
        params_alertas = []

        if current_user.rol == 'profesional':
            if current_user.nombre_completo:
                query_base_alertas += " AND (e.trabajadora_social_asignada = ? OR e.psicologo_asignado = ?)"
                params_alertas.extend([current_user.nombre_completo, current_user.nombre_completo])
            else:
                query_base_alertas += " AND 1 = 0"

        query_final_alertas = query_base_alertas + """
            GROUP BY e.rut
            HAVING dias_sin_seguimiento > 30 OR ultima_sesion IS NULL
            ORDER BY dias_sin_seguimiento DESC;
        """
        cursor.execute(query_final_alertas, tuple(params_alertas))
        estudiantes_con_alerta = cursor.fetchall()


        # --- PASO 3: Obtener la lista de estudiantes, aplicando filtros de BÚSQUEDA y ROL ---
        search_term = request.args.get('search_term', '').strip()
        filter_estado = request.args.get('filter_estado', '').strip()
        show_archived = request.args.get('show_archived') == 'true'

        base_query = "SELECT rut, nombre, apellido_paterno, apellido_materno, carrera_programa, estado_en_programa FROM Estudiantes"
        conditions = []
        params = []

        if current_user.rol == 'profesional':
            if current_user.nombre_completo:
                conditions.append("(trabajadora_social_asignada = ? OR psicologo_asignado = ?)")
                params.extend([current_user.nombre_completo, current_user.nombre_completo])
            else:
                conditions.append("1 = 0")

        if search_term:
            conditions.append("(lower(rut) LIKE ? OR lower(nombre) LIKE ? OR lower(apellido_paterno) LIKE ? OR lower(apellido_materno) LIKE ?)")
            params.extend([f"%{search_term.lower()}%"] * 4)

        if filter_estado:
            conditions.append("LOWER(TRIM(estado_en_programa)) = ?")
            params.append(filter_estado.lower())
        elif not show_archived:
            conditions.append("LOWER(TRIM(estado_en_programa)) != ?")
            params.append("archivado")

        final_query = base_query
        if conditions:
            final_query += " WHERE " + " AND ".join(conditions)
        final_query += " ORDER BY apellido_paterno, apellido_materno, nombre"

        cursor.execute(final_query, tuple(params))
        estudiantes = cursor.fetchall()

        return render_template('index.html',
                               estudiantes=estudiantes,
                               conteo_anual=conteo_activos_por_ano,
                               estudiantes_con_alerta=estudiantes_con_alerta,
                               search_term_active=search_term,
                               filter_estado_active=filter_estado, show_archived_active=show_archived,
                               lista_estado_programa_template=LISTA_ESTADO_PROGRAMA)
    except Exception as e:
        print(f"EXCEPCIÓN en la función index: {e}")
        flash("Ocurrió un error al cargar la lista de estudiantes.", "danger")
        return render_template('index.html', estudiantes=[], conteo_anual=[],
                               estudiantes_con_alerta=[], search_term_active="",
                               filter_estado_active="", show_archived_active=False,
                               lista_estado_programa_template=LISTA_ESTADO_PROGRAMA)
    finally:
        if conn: conn.close()



@app.route('/estudiante/nuevo', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'ingreso')
def nuevo_estudiante():
    form = NuevoEstudianteForm()

    form.genero.choices = [('', 'Seleccione...')] + [(g, g) for g in LISTA_GENERO]
    form.carrera_programa.choices = [('', 'Seleccione...')] + [(c, c) for c in LISTA_CARRERAS]
    form.trabajadora_social.choices = [('', 'Seleccione...')] + [(ts, ts) for ts in LISTA_TRABAJADORAS_SOCIALES]
    form.psicologo.choices = [('', 'Seleccione...')] + [(p, p) for p in LISTA_PSICOLOGOS]
    form.nacionalidad.choices = [('', 'Seleccione...')] + [(n, n) for n in LISTA_NACIONALIDADES]

    opciones_estado_inicial = [e for e in LISTA_ESTADO_PROGRAMA if e in ["Activo", "No acepta ingresar", "En evaluación inicial"]]
    form.estado_programa.choices = [(e, e) for e in opciones_estado_inicial]

    lista_cesfam_para_formulario = [c for c in LISTA_CESFAM if c.upper() != "NINGUNO"]
    form.cesfam.choices = [('', 'Seleccione CESFAM...')] + [(c, c) for c in lista_cesfam_para_formulario]
    form.tentativa_ideacion.choices = [('', 'Seleccione...')] + [(ti, ti) for ti in LISTA_TENTATIVA_IDEACION]
    form.estado_academico.choices = [('', 'Seleccione...')] + [(e, e) for e in LISTA_ESTADO_ACADEMICO]
    form.estado_civil.choices = [('', 'Seleccione...')] + [(ec, ec) for ec in LISTA_ESTADO_CIVIL]
    form.tiene_hijos.choices = [('', 'Seleccione...')] + [(h, h) for h in LISTA_TIENE_HIJOS]
    form.ocupacion_laboral.choices = [('', 'Seleccione...')] + [(ol, ol) for ol in LISTA_OCUPACION_LABORAL]
    form.fuente_derivacion.choices = [('', 'Seleccione...')] + [(f, f) for f in LISTA_FUENTE_DERIVACION]

    if form.validate_on_submit():
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            fecha_autorizacion_investigacion = date.today() if form.autoriza_investigacion.data else None
            rut_ingresado = form.rut.data
            cursor.execute("SELECT rut FROM Estudiantes WHERE rut = ?", (rut_ingresado,))
            if cursor.fetchone():
                form.rut.errors.append(f"El RUT '{rut_ingresado}' ya se encuentra registrado.")
            else:
                cursor.execute('''
                    INSERT INTO Estudiantes (rut, nombre, apellido_paterno, apellido_materno, genero,
                    fecha_nacimiento, nacionalidad, estado_civil, tiene_hijos,
                    carrera_programa, estado_academico, ocupacion_laboral,
                    residencia_academica, residencia_familiar, celular,
                    trabajadora_social_asignada, psicologo_asignado, fecha_ingreso_programa,
                    fuente_derivacion, estado_en_programa, fecha_derivacion_cesfam, cesfam_derivacion,
                    tentativa_ideacion, fecha_autorizacion_investigacion, nombre_contacto_emergencia,
                    parentesco_contacto_emergencia, telefono_contacto_emergencia)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (form.rut.data, form.nombre.data, form.apellido_paterno.data, form.apellido_materno.data, form.genero.data,
                    form.fecha_nacimiento.data, form.nacionalidad.data, form.estado_civil.data, form.tiene_hijos.data,
                    form.carrera_programa.data, form.estado_academico.data, form.ocupacion_laboral.data,
                    form.residencia_academica.data, form.residencia_familiar.data, form.celular.data,
                    form.trabajadora_social.data, form.psicologo.data, form.fecha_ingreso.data,
                    form.fuente_derivacion.data, form.estado_programa.data, form.fecha_derivacion.data, form.cesfam.data,
                    form.tentativa_ideacion.data, fecha_autorizacion_investigacion, form.nombre_contacto_emergencia.data,
                    form.parentesco_contacto_emergencia.data, form.telefono_contacto_emergencia.data
                ))
                conn.commit()
                flash(f'Estudiante {form.nombre.data} {form.apellido_paterno.data} registrado exitosamente.', 'success')
                return redirect(url_for('index'))

        except sqlite3.Error as e:
            if conn: conn.rollback()
            flash(f"Error de base de datos al crear estudiante: {e}", "danger")
        finally:
            if conn: conn.close()

    return render_template('nuevo_estudiante.html', form=form)

@app.route('/estudiante/<rut_estudiante>')
@login_required
def detalle_estudiante(rut_estudiante):
    conn = None
    edad_estudiante = "No calculada"
    seguimiento_alta = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Estudiantes WHERE rut = ?", (rut_estudiante,))
        estudiante = cursor.fetchone()

        if not estudiante:
            flash('Estudiante no encontrado.', 'danger')
            return redirect(url_for('index'))

        # Lógica de permisos (sin cambios)
        if current_user.rol == 'profesional':
            nombre_profesional_actual = current_user.nombre_completo
            if not (estudiante['trabajadora_social_asignada'] == nombre_profesional_actual or \
                    estudiante['psicologo_asignado'] == nombre_profesional_actual):
                flash('No tienes permiso para ver los detalles de este estudiante.', 'danger')
                return redirect(url_for('index'))
        elif current_user.rol not in ['admin', 'ingreso']:
            flash('No tienes permiso para ver los detalles de este estudiante.', 'danger')
            return redirect(url_for('index'))

        # --- INICIO DEL BLOQUE DE DIAGNÓSTICO ---
        print("\n--- INICIANDO DIAGNÓSTICO DE ALTA ---")
        print(f"RUT del estudiante: {rut_estudiante}")

        # Imprimimos el valor exacto que viene de la base de datos
        if estudiante['estado_en_programa']:
            estado_crudo = estudiante['estado_en_programa']
            print(f"1. Estado en Programa (crudo desde BD): '{estado_crudo}'")

            # Imprimimos el valor después de limpiarlo
            estado_limpio = estado_crudo.strip().lower()
            print(f"2. Estado en Programa (limpio y en minúsculas): '{estado_limpio}'")

            # Comprobamos la condición
            condicion_cumplida = (estado_limpio == 'alta del programa')
            print(f"3. ¿La condición se cumple?: {condicion_cumplida}")

            if condicion_cumplida:
                print("4. La condición se cumplió. Procediendo a buscar el seguimiento...")
                cursor.execute("""
                    SELECT * FROM Seguimientos
                    WHERE rut_estudiante = ? AND (alta_mejora_animo = 1 OR alta_disminucion_riesgo = 1 OR alta_redes_apoyo = 1 OR alta_adherencia_tratamiento = 1 OR alta_no_registrado = 1)
                    ORDER BY fecha_sesion DESC, id_seguimiento DESC
                    LIMIT 1
                """, (rut_estudiante,))
                seguimiento_alta = cursor.fetchone()
                if seguimiento_alta:
                    print(f"5. ¡ÉXITO! Se encontró el seguimiento de alta con ID: {seguimiento_alta['id_seguimiento']}")
                else:
                    print("5. ADVERTENCIA: No se encontró un seguimiento que cumpla los criterios de alta.")
            else:
                print("4. La condición NO se cumplió. No se buscará el seguimiento de alta.")
        else:
            print("1. El campo 'estado_en_programa' está vacío en la base de datos.")

        print("--- FIN DEL DIAGNÓSTICO ---\n")
        # --- FIN DEL BLOQUE DE DIAGNÓSTICO ---

        # Cálculo de edad (sin cambios)
        if estudiante and estudiante['fecha_nacimiento']:
            try:
                fecha_nac = datetime.strptime(estudiante['fecha_nacimiento'], '%Y-%m-%d').date()
                hoy = date.today()
                edad_estudiante = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            except (ValueError, TypeError):
                edad_estudiante = "Fecha inválida"

        # El resto de la función permanece exactamente igual...
        query_seguimientos = """
            SELECT s.*, (EXISTS (SELECT 1 FROM Seguimientos s2 WHERE s2.corrige_id_seguimiento = s.id_seguimiento) OR (s.es_correccion = 1 AND EXISTS (SELECT 1 FROM Seguimientos s2 WHERE s2.es_correccion = 1 AND s2.corrige_id_seguimiento = s.corrige_id_seguimiento AND s2.id_seguimiento > s.id_seguimiento))) as fue_corregido
            FROM Seguimientos s
            WHERE s.rut_estudiante = ?
            ORDER BY s.fecha_sesion DESC, s.id_seguimiento DESC
        """
        seguimientos = conn.execute(query_seguimientos, (rut_estudiante,)).fetchall()

        historial = conn.execute("SELECT * FROM HistorialCambios WHERE id_registro_afectado = ? AND modelo_afectado = 'Estudiante' ORDER BY fecha_cambio DESC", (rut_estudiante,)).fetchall()
        ultima_extension = conn.execute("SELECT MAX(extension_programa_otorgada) as fecha_extension FROM Seguimientos WHERE rut_estudiante = ?", (rut_estudiante,)).fetchone()

        return render_template('detalle_estudiante.html',
                               estudiante=estudiante,
                               seguimientos=seguimientos,
                               historial=historial,
                               edad=edad_estudiante,
                               fecha_ultima_extension=ultima_extension['fecha_extension'],
                               seguimiento_alta=seguimiento_alta)

    except Exception as e:
        print(f"EXCEPCIÓN en detalle_estudiante: {e}")
        flash('Ocurrió un error al cargar los detalles del estudiante.', 'danger')
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()


@app.route('/estudiante/<rut_estudiante>/seguimiento/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_seguimiento(rut_estudiante):
    conn = None
    try:
        conn = get_db_connection()
        estudiante = conn.execute("SELECT * FROM Estudiantes WHERE rut = ?", (rut_estudiante,)).fetchone()

        if not estudiante:
            flash('Estudiante no encontrado. No se puede agregar seguimiento.', 'danger')
            return redirect(url_for('index'))

        tiene_permiso = False
        if current_user.rol == 'admin' or (current_user.rol == 'profesional' and (estudiante['trabajadora_social_asignada'] == current_user.nombre_completo or estudiante['psicologo_asignado'] == current_user.nombre_completo)):
            tiene_permiso = True

        if not tiene_permiso:
            flash('No tienes permiso para agregar seguimientos a este estudiante.', 'danger')
            return redirect(url_for('detalle_estudiante', rut_estudiante=rut_estudiante))

        estados_finalizados = ["Concretó la Derivación", "Gestiona apoyo privado", "Se rehúsa a gestionar"]
        mostrar_seccion_derivacion = estudiante['estado_derivacion_maestro'] not in estados_finalizados

        alerta_derivacion_msg = None
        ESTADOS_ALERTA_DERIVACION = ["Aún no gestiona derivación"]
        ESTADOS_ALERTA_CONFIRMACION = ["Ha tenido problemas para conseguir hora"]

        ultimo_seguimiento = conn.execute("SELECT estado_derivacion_cesfam_actual, confirmacion_gestion_hora_cesfam FROM Seguimientos WHERE rut_estudiante = ? ORDER BY fecha_sesion DESC, id_seguimiento DESC LIMIT 1", (rut_estudiante,)).fetchone()

        if ultimo_seguimiento:
            if ultimo_seguimiento['estado_derivacion_cesfam_actual'] in ESTADOS_ALERTA_DERIVACION:
                alerta_derivacion_msg = f"Recordatorio: El estado de la derivación incial CESFAM en el seguimiento anterior es: '{ultimo_seguimiento['estado_derivacion_cesfam_actual']}'."
            elif ultimo_seguimiento['confirmacion_gestion_hora_cesfam'] in ESTADOS_ALERTA_CONFIRMACION:
                alerta_derivacion_msg = f"Recordatorio: El estado del seguimiento de controles en Red de Salud anterior es: '{ultimo_seguimiento['confirmacion_gestion_hora_cesfam']}'."

        form = NuevoSeguimientoForm()

        form.tipo_intervencion.choices = [('', 'Seleccione...')] + [(item, item) for item in LISTA_TIPO_INTERVENCION]
        form.resultado_cita.choices = [('', 'Seleccione...')] + [(item, item) for item in LISTA_RESULTADO_CITA]
        form.estado_derivacion_cesfam_actual.choices = [('', 'Seleccione...')] + [(item, item) for item in LISTA_ESTADO_DERIVACION_INICIAL]
        form.confirmacion_gestion_hora_cesfam.choices = [('', 'Seleccione...')] + [(item, item) for item in LISTA_ASISTENCIA_CONTROLES_CESFAM]
        form.nuevo_estado_programa.choices = [('', 'Mantener estado actual')] + [(estado, estado) for estado in LISTA_ESTADO_PROGRAMA]
        form.nuevo_estado_academico.choices = [('', 'Mantener estado actual')] + [(e, e) for e in LISTA_ESTADO_ACADEMICO]

        seguimientos_anteriores = conn.execute("SELECT id_seguimiento, fecha_sesion, tipo_intervencion FROM Seguimientos WHERE rut_estudiante = ? AND (es_correccion = 0 OR es_correccion IS NULL) ORDER BY fecha_sesion DESC", (rut_estudiante,)).fetchall()
        form.corrige_id_seguimiento.choices = [('', 'Seleccione si es una corrección...')] + [(s['id_seguimiento'], f"ID: {s['id_seguimiento']} ({s['fecha_sesion']}) - {s['tipo_intervencion']}") for s in seguimientos_anteriores]

        if form.validate_on_submit():
            try:
                valor_cambio_programa = form.nuevo_estado_programa.data or None
                valor_cambio_academico = form.nuevo_estado_academico.data or None
                creador = current_user.nombre_completo or current_user.username
                fecha_ext = date.today() if form.otorgar_extension_programa.data else None
                corrige_id = form.corrige_id_seguimiento.data if form.es_correccion.data else None

                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO Seguimientos (
                        rut_estudiante, trabajadora_social_sesion, psicologo_sesion, fecha_sesion,
                        estado_derivacion_cesfam_actual, tipo_intervencion, resultado_cita,
                        confirmacion_gestion_hora_cesfam, fechas_sesiones_cesfam, bitacora_sesion,
                        cambio_estado_programa_a, cambio_estado_academico_a, creado_por_usuario,
                        alta_mejora_animo, alta_disminucion_riesgo, alta_redes_apoyo,
                        alta_adherencia_tratamiento, alta_no_registrado, extension_programa_otorgada,
                        es_correccion, corrige_id_seguimiento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rut_estudiante, form.trabajadora_social_sesion.data, form.psicologo_sesion.data, form.fecha_sesion.data,
                    form.estado_derivacion_cesfam_actual.data, form.tipo_intervencion.data, form.resultado_cita.data,
                    form.confirmacion_gestion_hora_cesfam.data, form.fechas_sesiones_cesfam.data, form.bitacora_sesion.data,
                    valor_cambio_programa, valor_cambio_academico, creador, form.alta_mejora_animo.data,
                    form.alta_disminucion_riesgo.data, form.alta_redes_apoyo.data, form.alta_adherencia_tratamiento.data,
                    form.alta_no_registrado.data, fecha_ext, form.es_correccion.data, corrige_id
                ))

                if valor_cambio_programa:
                    cursor.execute('UPDATE Estudiantes SET estado_en_programa = ? WHERE rut = ?', (valor_cambio_programa, rut_estudiante))
                if valor_cambio_academico:
                    cursor.execute('UPDATE Estudiantes SET estado_academico = ? WHERE rut = ?', (valor_cambio_academico, rut_estudiante))
                if form.beneficio_arancel.data:
                    cursor.execute('UPDATE Estudiantes SET beneficio_arancel = ? WHERE rut = ?', (form.beneficio_arancel.data, rut_estudiante))
                if form.estado_derivacion_cesfam_actual.data:
                    cursor.execute('UPDATE Estudiantes SET estado_derivacion_maestro = ? WHERE rut = ?', (form.estado_derivacion_cesfam_actual.data, rut_estudiante))

                conn.commit()
                flash('Seguimiento agregado exitosamente.', 'success')
                return redirect(url_for('detalle_estudiante', rut_estudiante=rut_estudiante))

            except Exception as e:
                if conn: conn.rollback()
                print(f"Error al insertar seguimiento: {e}")
                flash(f"Error al guardar el seguimiento: {e}", 'danger')

        if request.method == 'GET':
            form.trabajadora_social_sesion.data = estudiante['trabajadora_social_asignada']
            form.psicologo_sesion.data = estudiante['psicologo_asignado']

        return render_template('nuevo_seguimiento.html',
                               form=form,
                               estudiante=estudiante,
                               alerta_derivacion_pendiente=alerta_derivacion_msg,
                               mostrar_seccion_derivacion=mostrar_seccion_derivacion)

    except Exception as e_main:
        print(f"Error general en nuevo_seguimiento para RUT {rut_estudiante}: {e_main}")
        flash("Ocurrió un error inesperado al procesar la solicitud de nuevo seguimiento.", 'danger')
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()

@app.route('/estudiante/<rut_estudiante>/editar', methods=['GET', 'POST'])
@login_required
def editar_estudiante(rut_estudiante):
    conn_inicial = get_db_connection()
    estudiante_obj = conn_inicial.execute("SELECT * FROM Estudiantes WHERE rut = ?", (rut_estudiante,)).fetchone()
    conn_inicial.close()

    if not estudiante_obj:
        flash('Estudiante no encontrado.', 'danger')
        return redirect(url_for('index'))

    tiene_permiso_para_editar = False
    if current_user.rol in ['admin', 'ingreso']:
        tiene_permiso_para_editar = True
    elif current_user.rol == 'profesional' and (estudiante_obj['trabajadora_social_asignada'] == current_user.nombre_completo or estudiante_obj['psicologo_asignado'] == current_user.nombre_completo):
        tiene_permiso_para_editar = True

    if not tiene_permiso_para_editar:
        flash('No tienes permiso para editar este estudiante.', 'danger')
        return redirect(url_for('index'))

    form = EditarEstudianteForm()

    form.genero.choices = [(g, g) for g in LISTA_GENERO]
    form.carrera_programa.choices = [(c, c) for c in LISTA_CARRERAS]
    form.trabajadora_social.choices = [(ts, ts) for ts in LISTA_TRABAJADORAS_SOCIALES]
    form.psicologo.choices = [(p, p) for p in LISTA_PSICOLOGOS]
    form.estado_programa.choices = [(e, e) for e in LISTA_ESTADO_PROGRAMA]
    form.cesfam.choices = [("NINGUNO", "NINGUNO")] + [(c, c) for c in LISTA_CESFAM if c.upper() != "NINGUNO"]
    form.tentativa_ideacion.choices = [(ti, ti) for ti in LISTA_TENTATIVA_IDEACION]
    form.estado_academico.choices = [('', 'Seleccione...')] + [(e, e) for e in LISTA_ESTADO_ACADEMICO]
    form.estado_civil.choices = [(ec, ec) for ec in LISTA_ESTADO_CIVIL]
    form.tiene_hijos.choices = [(h, h) for h in LISTA_TIENE_HIJOS]
    form.ocupacion_laboral.choices = [(ol, ol) for ol in LISTA_OCUPACION_LABORAL]
    form.nacionalidad.choices = [('', 'Seleccione...')] + [(n, n) for n in LISTA_NACIONALIDADES]
    form.fuente_derivacion.choices = [('', 'Seleccione...')] + [(f, f) for f in LISTA_FUENTE_DERIVACION]

    if form.validate_on_submit():
        conn_post = None
        try:
            nombres_amigables = { 'nombre': 'Nombre', 'apellido_paterno': 'Apellido Paterno', 'apellido_materno': 'Apellido Materno', 'genero': 'Género', 'fecha_nacimiento': 'Fecha de Nacimiento', 'nacionalidad': 'Nacionalidad', 'estado_civil': 'Estado Civil', 'tiene_hijos': 'Tiene Hijos/as', 'ocupacion_laboral': 'Ocupación Laboral', 'residencia_academica': 'Residencia Académica', 'residencia_familiar': 'Residencia Familiar', 'celular': 'Celular', 'carrera_programa': 'Carrera/Programa', 'estado_academico': 'Estado Académico', 'fecha_ingreso_programa': 'Fecha de Ingreso al Programa', 'fuente_derivacion': 'Fuente de Derivación', 'estado_en_programa': 'Estado en Programa', 'trabajadora_social_asignada': 'Trabajadora Social', 'psicologo_asignado': 'Psicólogo/a', 'fecha_derivacion_cesfam': 'Fecha Derivación CESFAM', 'cesfam_derivacion': 'CESFAM de Derivación', 'tentativa_ideacion': 'Tentativa o Ideación (al ingreso)', 'fecha_autorizacion_investigacion': 'Autorización para Investigación', 'beneficio_arancel': 'Beneficio de Arancel', 'estado_derivacion_maestro': 'Estado de Derivación' }
            campos_a_mapear = { 'nombre': 'nombre', 'apellido_paterno': 'apellido_paterno', 'apellido_materno': 'apellido_materno', 'genero': 'genero', 'fecha_nacimiento': 'fecha_nacimiento', 'nacionalidad': 'nacionalidad', 'estado_civil': 'estado_civil', 'tiene_hijos': 'tiene_hijos', 'ocupacion_laboral': 'ocupacion_laboral', 'residencia_academica': 'residencia_academica', 'residencia_familiar': 'residencia_familiar', 'celular': 'celular', 'carrera_programa': 'carrera_programa', 'estado_academico': 'estado_academico', 'fecha_ingreso_programa': 'fecha_ingreso', 'fuente_derivacion': 'fuente_derivacion', 'estado_en_programa': 'estado_programa', 'trabajadora_social_asignada': 'trabajadora_social', 'psicologo_asignado': 'psicologo', 'fecha_derivacion_cesfam': 'fecha_derivacion', 'cesfam_derivacion': 'cesfam', 'tentativa_ideacion': 'tentativa_ideacion', 'beneficio_arancel': 'beneficio_arancel', 'estado_derivacion_maestro': 'estado_derivacion_maestro' }
            detalles_cambios = []
            for columna_db, campo_form in campos_a_mapear.items():
                valor_anterior = estudiante_obj[columna_db]
                valor_nuevo = getattr(form, campo_form).data
                if str(valor_anterior) != str(valor_nuevo):
                    nombre_campo_bonito = nombres_amigables.get(columna_db, columna_db.replace("_", " ").title())
                    detalles_cambios.append(f"Cambió {nombre_campo_bonito} de '{valor_anterior or 'N/A'}' a '{valor_nuevo or 'N/A'}'.")

            conn_post = get_db_connection()
            cursor = conn_post.cursor()

            if detalles_cambios:
                texto_detalles = " | ".join(detalles_cambios)
                cursor.execute("INSERT INTO HistorialCambios (nombre_usuario, accion, modelo_afectado, id_registro_afectado, detalles) VALUES (?, ?, ?, ?, ?)", (current_user.nombre_completo, 'Edición de Estudiante', 'Estudiante', rut_estudiante, texto_detalles))

            fecha_autorizacion_investigacion = date.today() if form.autoriza_investigacion.data else None

            cursor.execute('''
                UPDATE Estudiantes SET
                    nombre = ?, apellido_paterno = ?, apellido_materno = ?, genero = ?, fecha_nacimiento = ?, nacionalidad = ?, estado_civil = ?, tiene_hijos = ?,
                    carrera_programa = ?, estado_academico = ?, ocupacion_laboral = ?, residencia_academica = ?, residencia_familiar = ?, celular = ?,
                    trabajadora_social_asignada = ?, psicologo_asignado = ?, fecha_ingreso_programa = ?, fuente_derivacion = ?, estado_en_programa = ?,
                    fecha_derivacion_cesfam = ?, cesfam_derivacion = ?, tentativa_ideacion = ?, fecha_autorizacion_investigacion = ?,
                    nombre_contacto_emergencia = ?, parentesco_contacto_emergencia = ?, telefono_contacto_emergencia = ?, beneficio_arancel = ?, estado_derivacion_maestro = ?
                WHERE rut = ?
            ''', (form.nombre.data, form.apellido_paterno.data, form.apellido_materno.data, form.genero.data, form.fecha_nacimiento.data, form.nacionalidad.data, form.estado_civil.data, form.tiene_hijos.data, form.carrera_programa.data, form.estado_academico.data, form.ocupacion_laboral.data, form.residencia_academica.data, form.residencia_familiar.data, form.celular.data, form.trabajadora_social.data, form.psicologo.data, form.fecha_ingreso.data, form.fuente_derivacion.data, form.estado_programa.data, form.fecha_derivacion.data, form.cesfam.data, form.tentativa_ideacion.data, fecha_autorizacion_investigacion,form.nombre_contacto_emergencia.data, form.parentesco_contacto_emergencia.data, form.telefono_contacto_emergencia.data, form.beneficio_arancel.data, form.estado_derivacion_maestro.data, rut_estudiante))
            conn_post.commit()
            flash('Datos del estudiante actualizados exitosamente.', 'success')
            return redirect(url_for('detalle_estudiante', rut_estudiante=rut_estudiante))
        except Exception as e:
            if conn_post: conn_post.rollback()
            print(f"Error al actualizar estudiante: {e}")
            flash('Ocurrió un error al guardar los cambios.', 'danger')
        finally:
            if conn_post: conn_post.close()

    if request.method == 'GET':
        form.nombre.data = estudiante_obj['nombre']
        form.apellido_paterno.data = estudiante_obj['apellido_paterno']
        form.apellido_materno.data = estudiante_obj['apellido_materno']
        form.genero.data = estudiante_obj['genero']
        form.nacionalidad.data = estudiante_obj['nacionalidad']
        form.estado_civil.data = estudiante_obj['estado_civil']
        form.tiene_hijos.data = estudiante_obj['tiene_hijos']
        form.carrera_programa.data = estudiante_obj['carrera_programa']
        form.estado_academico.data = estudiante_obj['estado_academico']
        form.ocupacion_laboral.data = estudiante_obj['ocupacion_laboral']
        form.residencia_academica.data = estudiante_obj['residencia_academica']
        form.residencia_familiar.data = estudiante_obj['residencia_familiar']
        form.celular.data = estudiante_obj['celular']
        form.trabajadora_social.data = estudiante_obj['trabajadora_social_asignada']
        form.psicologo.data = estudiante_obj['psicologo_asignado']
        form.fuente_derivacion.data = estudiante_obj['fuente_derivacion']
        form.estado_programa.data = estudiante_obj['estado_en_programa']
        form.cesfam.data = estudiante_obj['cesfam_derivacion']
        form.tentativa_ideacion.data = estudiante_obj['tentativa_ideacion']
        if estudiante_obj['fecha_nacimiento']: form.fecha_nacimiento.data = datetime.strptime(estudiante_obj['fecha_nacimiento'], '%Y-%m-%d').date()
        if estudiante_obj['fecha_ingreso_programa']: form.fecha_ingreso.data = datetime.strptime(estudiante_obj['fecha_ingreso_programa'], '%Y-%m-%d').date()
        if estudiante_obj['fecha_derivacion_cesfam']: form.fecha_derivacion.data = datetime.strptime(estudiante_obj['fecha_derivacion_cesfam'], '%Y-%m-%d').date()
        form.autoriza_investigacion.data = bool(estudiante_obj['fecha_autorizacion_investigacion'])
        form.nombre_contacto_emergencia.data = estudiante_obj['nombre_contacto_emergencia']
        form.parentesco_contacto_emergencia.data = estudiante_obj['parentesco_contacto_emergencia']
        form.telefono_contacto_emergencia.data = estudiante_obj['telefono_contacto_emergencia']
        form.beneficio_arancel.data = estudiante_obj['beneficio_arancel']
        form.estado_derivacion_maestro.data = estudiante_obj['estado_derivacion_maestro']

    return render_template('editar_estudiante.html', form=form, estudiante=estudiante_obj)

@app.route('/admin/usuarios')
@login_required
@admin_required
def admin_listar_usuarios():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, nombre_completo, rol, activo FROM Usuarios ORDER BY username")
        usuarios = cursor.fetchall()
        return render_template('admin_usuarios.html', usuarios=usuarios)
    except Exception as e:
        print(f"Error en admin_listar_usuarios: {e}")
        flash('Ocurrió un error al cargar la lista de usuarios.', 'danger')
        return redirect(url_for('index'))
    finally:
        if conn: conn.close()

@app.route('/admin/usuarios/crear', methods=['GET', 'POST'])
@login_required
def crear_usuario():
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('index'))
    lista_de_roles_posibles = ["admin", "profesional", "ingreso"]
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        nombre_completo = request.form.get('nombre_completo')
        rol = request.form.get('rol')
        activo = 1 if request.form.get('activo') == 'on' else 0
        if not username or not password or not rol:
            flash('Nombre de usuario, contraseña y rol son requeridos.', 'danger')
            return render_template('crear_usuario.html', username=username, nombre_completo=nombre_completo, rol_seleccionado=rol, activo_check=(activo == 1), lista_roles=lista_de_roles_posibles)
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('crear_usuario.html', username=username, nombre_completo=nombre_completo, rol_seleccionado=rol, activo_check=(activo == 1), lista_roles=lista_de_roles_posibles)
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Usuarios WHERE username = ?", (username,))
            if cursor.fetchone():
                flash('Ese nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
                return render_template('crear_usuario.html', username=username, nombre_completo=nombre_completo, rol_seleccionado=rol, activo_check=(activo == 1), lista_roles=lista_de_roles_posibles)
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute("INSERT INTO Usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)", (username, hashed_password, rol, nombre_completo, activo))
            conn.commit()
            flash(f'Usuario "{username}" creado exitosamente.', 'success')
            return redirect(url_for('admin_listar_usuarios'))
        except sqlite3.IntegrityError:
            if conn: conn.rollback()
            flash(f'Error de base de datos: Nombre de usuario "{username}" ya existe.', 'danger')
        except sqlite3.Error as e:
            if conn: conn.rollback()
            print(f"Error de BD al crear usuario: {e}")
            flash(f'Error de base de datos al crear usuario: {e}', 'danger')
        except Exception as e:
            if conn: conn.rollback()
            print(f"Error general al crear usuario: {e}")
            flash('Ocurrió un error al crear el usuario.', 'danger')
        finally:
            if conn: conn.close()
        return render_template('crear_usuario.html', username=username, nombre_completo=nombre_completo, rol_seleccionado=rol, activo_check=(activo == 1), lista_roles=lista_de_roles_posibles)
    return render_template('crear_usuario.html', lista_roles=lista_de_roles_posibles)

@app.route('/admin/usuarios/<int:id_usuario>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(id_usuario):
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('index'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Usuarios WHERE id = ?", (id_usuario,))
        usuario_a_editar_obj = cursor.fetchone()
        if not usuario_a_editar_obj:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('admin_listar_usuarios'))
        lista_de_roles_posibles = ["admin", "profesional", "ingreso"]
        if request.method == 'POST':
            nombre_completo_form = request.form.get('nombre_completo')
            rol_form = request.form.get('rol')
            activo_form = 1 if request.form.get('activo') == '1' else 0
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')
            if not nombre_completo_form or not rol_form:
                flash('El nombre completo y el rol son requeridos.', 'danger')
                return render_template('editar_usuario.html', usuario=usuario_a_editar_obj, lista_roles=lista_de_roles_posibles, nombre_completo_form_val=nombre_completo_form, rol_form_val=rol_form, activo_form_val=activo_form)
            password_hash_to_update = None
            if new_password:
                if new_password != confirm_new_password:
                    flash('Las nuevas contraseñas no coinciden. La contraseña no ha sido cambiada.', 'danger')
                    return render_template('editar_usuario.html', usuario=usuario_a_editar_obj, lista_roles=lista_de_roles_posibles, nombre_completo_form_val=nombre_completo_form, rol_form_val=rol_form, activo_form_val=activo_form)
                password_hash_to_update = generate_password_hash(new_password, method='pbkdf2:sha256')
            if password_hash_to_update:
                cursor.execute("UPDATE Usuarios SET nombre_completo = ?, rol = ?, activo = ?, password_hash = ? WHERE id = ?", (nombre_completo_form, rol_form, activo_form, password_hash_to_update, id_usuario))
            else:
                cursor.execute("UPDATE Usuarios SET nombre_completo = ?, rol = ?, activo = ? WHERE id = ?", (nombre_completo_form, rol_form, activo_form, id_usuario))
            conn.commit()
            flash(f'Usuario "{usuario_a_editar_obj["username"]}" actualizado exitosamente.', 'success')
            return redirect(url_for('admin_listar_usuarios'))
        return render_template('editar_usuario.html', usuario=usuario_a_editar_obj, lista_roles=lista_de_roles_posibles)
    except sqlite3.Error as e:
        if conn: conn.rollback()
        print(f"Error de BD en editar_usuario (ID: {id_usuario}): {e}")
        flash('Ocurrió un error de base de datos al actualizar el usuario.', 'danger')
        if 'usuario_a_editar_obj' in locals() and usuario_a_editar_obj:
             return render_template('editar_usuario.html', usuario=usuario_a_editar_obj, lista_roles=(lista_de_roles_posibles if 'lista_de_roles_posibles' in locals() else ["admin", "profesional"]))
        return redirect(url_for('admin_listar_usuarios'))
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error general en editar_usuario (ID: {id_usuario}): {e}")
        flash('Ocurrió un error al intentar procesar la solicitud.', 'danger')
        return redirect(url_for('admin_listar_usuarios'))
    finally:
        if conn: conn.close()


@app.route('/seguimiento/<int:id_seguimiento>/editar', methods=['GET', 'POST'])
@login_required
def editar_seguimiento(id_seguimiento):
    conn = get_db_connection()
    seguimiento = conn.execute("SELECT * FROM Seguimientos WHERE id_seguimiento = ?", (id_seguimiento,)).fetchone()
    if not seguimiento:
        conn.close()
        flash('Seguimiento no encontrado.', 'danger')
        return redirect(url_for('index'))
    estudiante = conn.execute("SELECT * FROM Estudiantes WHERE rut = ?", (seguimiento['rut_estudiante'],)).fetchone()
    conn.close()
    if not estudiante:
        flash('Estudiante asociado a este seguimiento no encontrado.', 'danger')
        return redirect(url_for('index'))
    if current_user.rol == 'profesional':
        nombre_profesional_actual = current_user.nombre_completo
        if not (estudiante['trabajadora_social_asignada'] == nombre_profesional_actual or estudiante['psicologo_asignado'] == nombre_profesional_actual):
            flash('No tienes permiso para editar seguimientos de este estudiante.', 'danger')
            return redirect(url_for('index'))
    elif current_user.rol not in ['admin']:
        flash('No tienes permiso para editar seguimientos.', 'danger')
        return redirect(url_for('detalle_estudiante', rut_estudiante=estudiante['rut']))

    estados_finalizados = ["Concretó la Derivación", "Gestiona apoyo privado", "Se rehúsa a gestionar"]
    mostrar_seccion_derivacion = estudiante['estado_derivacion_maestro'] not in estados_finalizados
    form = EditarSeguimientoForm()
    form.tipo_intervencion.choices = [(item, item) for item in LISTA_TIPO_INTERVENCION]
    form.resultado_cita.choices = [(item, item) for item in LISTA_RESULTADO_CITA]
    form.estado_derivacion_cesfam_actual.choices = [('', 'Seleccione...')] + [(item, item) for item in LISTA_ESTADO_DERIVACION_INICIAL]
    form.confirmacion_gestion_hora_cesfam.choices = [('', 'Seleccione...')] + [(item, item) for item in LISTA_ASISTENCIA_CONTROLES_CESFAM]

    if form.validate_on_submit():
        conn_post = None
        try:
            conn_post = get_db_connection()
            cursor = conn_post.cursor()
            nuevo_estado_derivacion = form.estado_derivacion_cesfam_actual.data
            if nuevo_estado_derivacion:
                cursor.execute('UPDATE Estudiantes SET estado_derivacion_maestro = ? WHERE rut = ?', (nuevo_estado_derivacion, estudiante['rut']))
            cursor.execute('''
                UPDATE Seguimientos SET
                    fecha_sesion = ?, trabajadora_social_sesion = ?, psicologo_sesion = ?,
                    tipo_intervencion = ?, resultado_cita = ?, estado_derivacion_cesfam_actual = ?,
                    confirmacion_gestion_hora_cesfam = ?, fechas_sesiones_cesfam = ?,
                    bitacora_sesion = ?
                WHERE id_seguimiento = ?
            ''', (form.fecha_sesion.data, form.trabajadora_social_sesion.data, form.psicologo_sesion.data, form.tipo_intervencion.data, form.resultado_cita.data, form.estado_derivacion_cesfam_actual.data, form.confirmacion_gestion_hora_cesfam.data, form.fechas_sesiones_cesfam.data, form.bitacora_sesion.data, id_seguimiento))
            conn_post.commit()
            flash('Seguimiento actualizado exitosamente.', 'success')
            return redirect(url_for('detalle_estudiante', rut_estudiante=seguimiento['rut_estudiante']))
        except Exception as e:
            if conn_post: conn_post.rollback()
            flash(f"Error al guardar los cambios del seguimiento: {e}", 'danger')
        finally:
            if conn_post: conn_post.close()

    if request.method == 'GET':
        form.fecha_sesion.data = datetime.strptime(seguimiento['fecha_sesion'], '%Y-%m-%d').date() if seguimiento['fecha_sesion'] else None
        form.trabajadora_social_sesion.data = seguimiento['trabajadora_social_sesion']
        form.psicologo_sesion.data = seguimiento['psicologo_sesion']
        form.tipo_intervencion.data = seguimiento['tipo_intervencion']
        form.resultado_cita.data = seguimiento['resultado_cita']
        form.estado_derivacion_cesfam_actual.data = seguimiento['estado_derivacion_cesfam_actual']
        form.confirmacion_gestion_hora_cesfam.data = seguimiento['confirmacion_gestion_hora_cesfam']
        form.fechas_sesiones_cesfam.data = seguimiento['fechas_sesiones_cesfam']
        form.bitacora_sesion.data = seguimiento['bitacora_sesion']

    return render_template('editar_seguimiento.html', form=form, seguimiento=seguimiento, estudiante=estudiante, mostrar_seccion_derivacion=mostrar_seccion_derivacion)

@app.route('/descargar/estudiantes_csv')
@login_required
def descargar_estudiantes_csv():
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('index'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Estudiantes ORDER BY apellido_paterno, apellido_materno, nombre")
        lista_estudiantes = cursor.fetchall()
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        if lista_estudiantes:
            column_names = [description[0] for description in cursor.description]
            writer.writerow(column_names)
            for estudiante_row in lista_estudiantes: writer.writerow(estudiante_row)
        else: writer.writerow(["No hay datos de estudiantes para descargar."])
        csv_data = output.getvalue().encode('utf-8-sig')
        return Response(csv_data, mimetype="text/csv; charset=utf-8-sig", headers={"Content-Disposition": "attachment;filename=estudiantes_seguimiento.csv"})
    except Exception as e:
        print(f"Error al generar CSV de estudiantes: {e}")
        return "Error al generar el archivo CSV de estudiantes.", 500
    finally:
        if conn: conn.close()

@app.route('/descargar/seguimientos_csv')
@login_required
def descargar_seguimientos_csv():
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('index'))

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query_avanzada = """
            SELECT s.*, e.fecha_ingreso_programa,
                (EXISTS (SELECT 1 FROM Seguimientos s2 WHERE s2.corrige_id_seguimiento = s.id_seguimiento) OR
                    (s.es_correccion = 1 AND EXISTS (
                        SELECT 1 FROM Seguimientos s2 WHERE s2.es_correccion = 1 AND
                        s2.corrige_id_seguimiento = s.corrige_id_seguimiento AND s2.id_seguimiento > s.id_seguimiento
                    ))) as fue_corregido
            FROM Seguimientos s
            INNER JOIN Estudiantes e ON s.rut_estudiante = e.rut
            ORDER BY s.rut_estudiante, s.fecha_sesion
        """
        cursor.execute(query_avanzada)
        lista_seguimientos = cursor.fetchall()
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        if lista_seguimientos:
            column_names = [description[0] for description in cursor.description]
            writer.writerow(column_names)
            for seguimiento_row in lista_seguimientos: writer.writerow(seguimiento_row)
        else: writer.writerow(["No hay datos de seguimientos para descargar."])
        csv_data = output.getvalue().encode('utf-8-sig')
        return Response(csv_data, mimetype="text/csv; charset=utf-8-sig", headers={"Content-Disposition": "attachment;filename=seguimientos_programa.csv"})
    except Exception as e:
        print(f"Error al generar CSV de seguimientos: {e}")
        return "Error al generar el archivo CSV de seguimientos.", 500
    finally:
        if conn: conn.close()

@app.route('/seguimiento/<int:id_seguimiento>/eliminar', methods=['POST'])
@login_required
def eliminar_seguimiento(id_seguimiento):
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('index'))
    conn = None
    rut_estudiante_para_redirigir = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rut_estudiante FROM Seguimientos WHERE id_seguimiento = ?", (id_seguimiento,))
        seguimiento_a_eliminar = cursor.fetchone()
        if not seguimiento_a_eliminar:
            flash('Seguimiento no encontrado.', 'danger')
            return redirect(request.referrer or url_for('index'))
        rut_estudiante_para_redirigir = seguimiento_a_eliminar['rut_estudiante']
        cursor.execute("DELETE FROM Seguimientos WHERE id_seguimiento = ?", (id_seguimiento,))
        conn.commit()
        flash('El seguimiento ha sido eliminado exitosamente.', 'success')
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error al eliminar seguimiento (ID: {id_seguimiento}): {e}")
        flash('Ocurrió un error al eliminar el seguimiento.', 'danger')
        if rut_estudiante_para_redirigir:
            return redirect(url_for('detalle_estudiante', rut_estudiante=rut_estudiante_para_redirigir))
        return redirect(url_for('index'))
    finally:
        if conn: conn.close()
    if rut_estudiante_para_redirigir:
        return redirect(url_for('detalle_estudiante', rut_estudiante=rut_estudiante_para_redirigir))
    return redirect(url_for('index'))

@app.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    form = CambiarPasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Tu contraseña actual es incorrecta.', 'danger')
            return redirect(url_for('cambiar_password'))
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            new_password_hash = generate_password_hash(form.new_password.data, method='pbkdf2:sha256')
            cursor.execute("UPDATE Usuarios SET password_hash = ? WHERE id = ?", (new_password_hash, current_user.id))
            conn.commit()
            flash('Tu contraseña ha sido actualizada exitosamente. Por favor, inicia sesión de nuevo.', 'success')
            logout_user()
            return redirect(url_for('login'))
        except Exception as e:
            if conn: conn.rollback()
            print(f"Error al cambiar contraseña para usuario ID {current_user.id}: {e}")
            flash('Ocurrió un error al intentar cambiar tu contraseña.', 'danger')
            return redirect(url_for('cambiar_password'))
        finally:
            if conn: conn.close()
    return render_template('cambiar_password.html', form=form)

@app.route('/dashboard')
@login_required
@roles_required('admin', 'profesional', 'ingreso')
def dashboard():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT estado_en_programa, COUNT(*) as total FROM Estudiantes GROUP BY estado_en_programa")
        datos_estados = cursor.fetchall()
        labels_estados = [row['estado_en_programa'] for row in datos_estados]
        data_estados = [row['total'] for row in datos_estados]

        cursor.execute("SELECT carrera_programa, COUNT(*) as total FROM Estudiantes GROUP BY carrera_programa ORDER BY total DESC LIMIT 10")
        datos_carreras = cursor.fetchall()
        labels_carreras = [row['carrera_programa'] for row in datos_carreras]
        data_carreras = [row['total'] for row in datos_carreras]

        cursor.execute("""
            SELECT strftime('%Y-%m', s.fecha_sesion) as mes, COUNT(s.id_seguimiento) as total
            FROM Seguimientos s
            WHERE s.fecha_sesion IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Seguimientos s2 WHERE s2.corrige_id_seguimiento = s.id_seguimiento)
            GROUP BY mes ORDER BY mes
        """)
        datos_seguimientos = cursor.fetchall()
        labels_seguimientos = [row['mes'] for row in datos_seguimientos]
        data_seguimientos = [row['total'] for row in datos_seguimientos]

        cursor.execute("""
            SELECT strftime('%Y', fecha_ingreso_programa) as anio, tentativa_ideacion
            FROM Estudiantes
            WHERE tentativa_ideacion IN ('Ideación', 'Tentativa')
        """)
        datos_ideacion_raw = cursor.fetchall()
        datos_pivot = {}
        for row in datos_ideacion_raw:
            anio = row['anio']
            tipo = row['tentativa_ideacion']
            if anio not in datos_pivot:
                datos_pivot[anio] = {'Ideación': 0, 'Tentativa': 0}
            if tipo in datos_pivot[anio]:
                datos_pivot[anio][tipo] += 1
        labels_ideacion_anio = sorted(datos_pivot.keys())
        data_ideacion = [datos_pivot.get(anio, {}).get('Ideación', 0) for anio in labels_ideacion_anio]
        data_tentativa = [datos_pivot.get(anio, {}).get('Tentativa', 0) for anio in labels_ideacion_anio]

        return render_template(
            'dashboard.html',
            labels_estados=json.dumps(labels_estados), data_estados=json.dumps(data_estados),
            labels_carreras=json.dumps(labels_carreras), data_carreras=json.dumps(data_carreras),
            labels_seguimientos=json.dumps(labels_seguimientos), data_seguimientos=json.dumps(data_seguimientos),
            labels_ideacion_anio=json.dumps(labels_ideacion_anio), data_ideacion=json.dumps(data_ideacion), data_tentativa=json.dumps(data_tentativa)
        )
    except Exception as e:
        print(f"Error CRÍTICO en el dashboard: {e}")
        import traceback
        traceback.print_exc()
        flash('Ocurrió un error muy grave al generar los datos del dashboard. Revisa los logs.', 'danger')
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        username_form = form.username.data
        password_form = form.password.data
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Usuarios WHERE username = ?", (username_form,))
            user_data = cursor.fetchone()
            if user_data:
                user_obj = User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'], rol=user_data['rol'], nombre_completo=user_data['nombre_completo'], activo=user_data['activo'])
                if user_obj.activo and user_obj.check_password(password_form):
                    login_user(user_obj)
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('index')
                    return redirect(next_page)
        except Exception as e:
            print(f"Error durante el login: {e}")
            flash("Ocurrió un error durante el inicio de sesión.", "danger")
        finally:
            if conn:
                conn.close()
        flash('Nombre de usuario o contraseña incorrectos, o la cuenta está inactiva.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
