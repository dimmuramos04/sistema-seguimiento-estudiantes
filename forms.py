# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, EqualTo
from database import LISTA_BENEFICIO_ARANCEL, LISTA_PARENTESCO, LISTA_ESTADO_DERIVACION_INICIAL, LISTA_ASISTENCIA_CONTROLES_CESFAM, LISTA_CARRERAS, LISTA_FACULTADES, LISTA_ESTADO_ACADEMICO

class LoginForm(FlaskForm):
    """Formulario para el inicio de sesión de usuarios."""

    # Cada atributo de la clase representa un campo <input> en el formulario.

    # StringField para el nombre de usuario.
    # El primer argumento es la etiqueta (label) del campo.
    # 'validators' es una lista de reglas. DataRequired significa que el campo no puede estar vacío.
    username = StringField('Nombre de Usuario',
                           validators=[DataRequired(message="El nombre de usuario es requerido.")])

    # PasswordField para la contraseña.
    password = PasswordField('Contraseña',
                             validators=[DataRequired(message="La contraseña es requerida.")])

    # SubmitField para el botón de envío.
    submit = SubmitField('Iniciar Sesión')

class NuevoEstudianteForm(FlaskForm):
    """Formulario para registrar un nuevo estudiante."""
    rut = StringField('RUT (con guión, ej: 12345678-9)',
                      validators=[DataRequired(message="El RUT es obligatorio.")])
    nombre = StringField('Nombre',
                         validators=[DataRequired(message="El nombre es obligatorio.")])
    apellido_paterno = StringField('Apellido Paterno',
                                   validators=[DataRequired(message="El apellido paterno es obligatorio.")])
    apellido_materno = StringField('Apellido Materno',
                                   validators=[DataRequired(message="El apellido materno es obligatorio.")])

    # Para los menús desplegables (SelectField), las opciones (choices)
    # se las daremos desde la ruta en app.py, por eso aquí no las definimos.
    genero = SelectField('Género',
                         validators=[DataRequired(message="Debe seleccionar un género.")])
    sexo = SelectField('Sexo', validators=[DataRequired(message="Debe seleccionar un sexo.")])
    fecha_nacimiento = DateField('Fecha de Nacimiento',
                                 validators=[DataRequired(message="La fecha de nacimiento es requerida.")])

    nacionalidad = SelectField('Nacionalidad',
                           validators=[DataRequired(message="La nacionalidad es requerida.")])

    estado_civil = SelectField('Estado Civil',
                               validators=[DataRequired(message="Debe seleccionar un estado civil.")])

    tiene_hijos = SelectField('¿Tiene Hijos/as?',
                              validators=[DataRequired(message="Debe seleccionar una opción.")])

    ocupacion_laboral = SelectField('Ocupación Laboral',
                                    validators=[DataRequired(message="Debe seleccionar una ocupación.")])

    residencia_academica = StringField('Residencia Académica (Comuna)',
                                       validators=[DataRequired(message="La residencia académica es requerida.")])

    residencia_familiar = StringField('Residencia Familiar (Comuna)',
                                      validators=[DataRequired(message="La residencia familiar es requerida.")])
    carrera_programa = SelectField('Carrera/Programa',
                                   validators=[DataRequired(message="Debe seleccionar una carrera.")])
    facultad = SelectField('Facultad o Programa de Postgrado', validators=[DataRequired(message="Debe seleccionar una Facultad o Programa de Postgrado.")])

    celular = StringField('Celular', validators=[Optional()])

    trabajadora_social = SelectField('Trabajadora Social Asignada',
                                     validators=[DataRequired(message="Debe asignar una trabajadora social.")])
    psicologo = SelectField('Psicólogo/a Asignado/a',
                            validators=[DataRequired(message="Debe asignar un psicólogo/a.")])
    fecha_ingreso = DateField('Fecha de Ingreso al Programa',
                              validators=[DataRequired(message="La fecha de ingreso es obligatoria.")])
    fuente_derivacion = SelectField('Fuente de Derivación / Motivo de Ingreso',
                                validators=[DataRequired(message="Este campo es obligatorio.")])
    estado_programa = SelectField('Estado en Programa (al ingresar)',
                                  validators=[DataRequired(message="Debe seleccionar un estado.")])

    # Campos de Derivación CESFAM
    fecha_derivacion = DateField('Fecha Derivación CESFAM (generada por doctora)',
                                 validators=[DataRequired(message="La fecha de derivación es obligatoria.")])
    cesfam = SelectField('CESFAM Derivación',
                         validators=[DataRequired(message="Debe seleccionar un CESFAM.")])
    tentativa_ideacion = SelectField('Evaluación Inicial (Tentativa o Ideación)',
                                     validators=[DataRequired(message="Este campo es obligatorio.")])
    estado_academico = SelectField('Estado Académico', validators=[DataRequired(message="Debe seleccionar un estado académico.")])

    autoriza_investigacion = BooleanField(
        'El estudiante autoriza el uso de sus datos (debidamente anonimizados) para fines institucionales y mejoras del programa.')
    nombre_contacto_emergencia = StringField('Nombre Contacto de Emergencia', validators=[Optional()])
    parentesco_contacto_emergencia = SelectField('Parentesco del Contacto', choices=[('', 'Seleccione...')] + [(p, p) for p in LISTA_PARENTESCO], validators=[Optional()])
    telefono_contacto_emergencia = StringField('Teléfono del Contacto', validators=[Optional()])

    nota_importante = TextAreaField('Nota Rápida / Alerta (opcional)', validators=[Optional()])

    submit = SubmitField('Registrar Estudiante')

class CambiarPasswordForm(FlaskForm):
    """Formulario para que un usuario cambie su propia contraseña."""

    current_password = PasswordField('Contraseña Actual',
                                     validators=[DataRequired(message="Debes ingresar tu contraseña actual.")])

    new_password = PasswordField('Nueva Contraseña',
                                 validators=[
                                     DataRequired(message="Debes ingresar una nueva contraseña."),
                                     Length(min=6, message="La nueva contraseña debe tener al menos 6 caracteres.")
                                 ])

    confirm_new_password = PasswordField('Confirmar Nueva Contraseña',
                                         validators=[
                                             DataRequired(message="Debes confirmar la nueva contraseña."),
                                             EqualTo('new_password', message='Las contraseñas no coinciden.')
                                         ])

    submit = SubmitField('Cambiar Contraseña')

class EditarEstudianteForm(FlaskForm):
    """Formulario para editar un estudiante existente."""
    # Nota: Omitimos el campo 'rut' porque no se debe editar.

    nombre = StringField('Nombre',
                         validators=[DataRequired(message="El nombre es obligatorio.")])
    apellido_paterno = StringField('Apellido Paterno',
                                   validators=[DataRequired(message="El apellido paterno es obligatorio.")])
    apellido_materno = StringField('Apellido Materno',
                                   validators=[DataRequired(message="El apellido materno es obligatorio.")])
    sexo = SelectField('Sexo', validators=[DataRequired(message="Debe seleccionar un sexo.")])

    genero = SelectField('Género',
                         validators=[DataRequired(message="Debe seleccionar un género.")])

    fecha_nacimiento = DateField('Fecha de Nacimiento',
                                 validators=[DataRequired(message="La fecha de nacimiento es requerida.")])

    nacionalidad = SelectField('Nacionalidad',
                           validators=[DataRequired(message="La nacionalidad es requerida.")])

    estado_civil = SelectField('Estado Civil',
                               validators=[DataRequired(message="Debe seleccionar un estado civil.")])

    tiene_hijos = SelectField('¿Tiene Hijos/as?',
                              validators=[DataRequired(message="Debe seleccionar una opción.")])

    ocupacion_laboral = SelectField('Ocupación Laboral',
                                    validators=[DataRequired(message="Debe seleccionar una ocupación.")])

    residencia_academica = StringField('Residencia Académica (Ciudad)',
                                       validators=[DataRequired(message="La residencia académica es requerida.")])

    residencia_familiar = StringField('Residencia Familiar (Ciudad)',
                                      validators=[DataRequired(message="La residencia familiar es requerida.")])

    carrera_programa = SelectField('Carrera/Programa',
                                   validators=[DataRequired(message="Debe seleccionar una carrera.")])

    facultad = SelectField('Facultad o Programa de Postgrado', validators=[DataRequired(message="Debe seleccionar una Facultad o Programa de Postgrado.")])

    celular = StringField('Celular', validators=[Optional()])

    trabajadora_social = SelectField('Trabajadora Social Asignada',
                                     validators=[DataRequired(message="Debe asignar una trabajadora social.")])
    psicologo = SelectField('Psicólogo/a Asignado/a',
                            validators=[DataRequired(message="Debe asignar un psicólogo/a.")])

    fecha_ingreso = DateField('Fecha de Ingreso al Programa',
                              validators=[DataRequired(message="La fecha de ingreso es obligatoria.")])
    fuente_derivacion = SelectField('Fuente de Derivación / Motivo de Ingreso',
                                validators=[DataRequired(message="Este campo es obligatorio.")])
    estado_programa = SelectField('Estado en Programa',
                                  validators=[DataRequired(message="Debe seleccionar un estado.")])

    # Campos de Derivación CESFAM
    fecha_derivacion = DateField('Fecha Derivación CESFAM (generada por doctora)', validators=[Optional()])
    cesfam = SelectField('CESFAM Derivación', validators=[Optional()])
    tentativa_ideacion = SelectField('Evaluación Inicial (Tentativa o Ideación)',
                                     validators=[DataRequired(message="Este campo es obligatorio.")])
    estado_academico = SelectField('Estado Académico', validators=[DataRequired(message="Debe seleccionar un estado académico.")])

    autoriza_investigacion = BooleanField(
        'El estudiante autoriza el uso de sus datos (debidamente anonimizados) para fines institucionales y mejoras del programa.')
    nombre_contacto_emergencia = StringField('Nombre Contacto de Emergencia', validators=[Optional()])
    parentesco_contacto_emergencia = SelectField('Parentesco del Contacto', choices=[('', 'Seleccione...')] + [(p, p) for p in LISTA_PARENTESCO], validators=[Optional()])
    telefono_contacto_emergencia = StringField('Teléfono del Contacto', validators=[Optional()])
    beneficio_arancel = SelectField('Beneficio de Arancel', choices=[('', 'No especificado')] + [(b, b) for b in LISTA_BENEFICIO_ARANCEL], validators=[Optional()])
    estado_derivacion_maestro = SelectField(
        'Estado Maestro de la Derivación',
        choices=[(opcion, opcion) for opcion in LISTA_ESTADO_DERIVACION_INICIAL],
        validators=[Optional()]
    )

    nota_importante = TextAreaField('Nota Rápida / Alerta Importante (Visible para todos los profesionales)', validators=[Optional()])


    submit = SubmitField('Guardar Cambios')

class NuevoSeguimientoForm(FlaskForm):
    """Formulario para agregar un nuevo seguimiento."""

    fecha_sesion = DateField('Fecha de la Sesión',
                             validators=[DataRequired(message="La fecha de la sesión es obligatoria.")])

    # Estos campos se precargarán, pero el usuario puede editarlos. Son opcionales.
    trabajadora_social_sesion = StringField('Trabajadora Social (Sesión)', validators=[Optional()])
    psicologo_sesion = StringField('Psicólogo/a (Sesión)', validators=[Optional()])

    tipo_intervencion = SelectField('Tipo de entrevista de Acompañamiento y Seguimiento realizada',
                                     validators=[DataRequired(message="Debe seleccionar el tipo de Acompañamiento y Seguimiento Realizado.")])
    resultado_cita = SelectField('Resultado de la entrevista de Acompañamiento y Seguimiento agendada',
                                 validators=[DataRequired(message="Debe seleccionar el resultado de la entrevista.")])

    # Campos de Derivación CESFAM
    estado_derivacion_cesfam_actual = SelectField('Estado de la Derivación Inicial', choices=[('', 'Seleccione...')] + [(item, item) for item in LISTA_ESTADO_DERIVACION_INICIAL], validators=[Optional()])
    confirmacion_gestion_hora_cesfam = SelectField('¿Estudiante ha asistido a sus controles en CESFAM?', choices=[('', 'Seleccione...')] + [(item, item) for item in LISTA_ASISTENCIA_CONTROLES_CESFAM], validators=[Optional()])
    fechas_sesiones_cesfam = StringField('Fechas de los controles a los que ha asistido (si aplica)', validators=[Optional()])

    # La bitácora es obligatoria para registrar la sesión
    bitacora_sesion = TextAreaField('Bitácora de la Sesión / Observaciones',
                                    validators=[DataRequired(message="La bitácora no puede estar vacía.")])

    # Este campo es para cambiar el estado general del estudiante (opcional)
    nuevo_estado_programa = SelectField('Actualizar Estado del Estudiante en el Programa (si cambia)', validators=[Optional()])

    nuevo_estado_academico = SelectField('Actualizar Estado Académico del Estudiante (si cambia)', validators=[Optional()])
    nota_importante = TextAreaField('Actualizar Nota Rápida / Alerta del Estudiante (opcional)', validators=[Optional()])

    alta_mejora_animo = BooleanField('Mejora en el estado anímico, aspecto físico y salud en general.')
    alta_disminucion_riesgo = BooleanField('Disminución del riesgo suicida en el estudiante.')
    alta_redes_apoyo = BooleanField('Cuenta con redes de apoyo intra y/o extrafamiliar.')
    alta_adherencia_tratamiento = BooleanField('Ha adherido a tratamiento en la red de salud pública o privada.')
    alta_no_registrado = BooleanField('Criterio de alta no registrado (2023 y 2024)')
    otorgar_extension_programa = BooleanField('Otorgar extensión de 3 meses al programa')
    es_correccion = BooleanField('Marcar si este seguimiento es para corregir un error en un registro anterior')
    corrige_id_seguimiento = SelectField('Corregir el seguimiento de la fecha:', validators=[Optional()])
    beneficio_arancel = SelectField('Actualizar Beneficio de Arancel del Estudiante (si no está registrado)', choices=[('', 'No modificar')] + [(b, b) for b in LISTA_BENEFICIO_ARANCEL], validators=[Optional()])

    submit = SubmitField('Guardar Seguimiento')

class EditarSeguimientoForm(FlaskForm):
    """Formulario para editar un seguimiento existente."""

    fecha_sesion = DateField('Fecha de la Sesión',
                             validators=[DataRequired(message="La fecha de la sesión es obligatoria.")])

    trabajadora_social_sesion = StringField('Trabajadora Social (Sesión)', validators=[Optional()])
    psicologo_sesion = StringField('Psicólogo/a (Sesión)', validators=[Optional()])

    tipo_intervencion = SelectField('Tipo de entrevista de Acompañamiento y Seguimiento realizada',
                                     validators=[DataRequired(message="Debe seleccionar el tipo de Acompañamiento y Seguimiento Realizado.")])
    resultado_cita = SelectField('Resultado de la entrevista de Acompañamiento y Seguimiento agendada',
                                 validators=[DataRequired(message="Debe seleccionar el resultado del Acompañamiento y Seguimiento agendado.")])

    estado_derivacion_cesfam_actual = SelectField('Estado de la Derivación Inicial', choices=[('', 'Seleccione...')] + [(item, item) for item in LISTA_ESTADO_DERIVACION_INICIAL], validators=[Optional()])
    confirmacion_gestion_hora_cesfam = SelectField('¿Estudiante ha asistido a sus controles en CESFAM?', choices=[('', 'Seleccione...')] + [(item, item) for item in LISTA_ASISTENCIA_CONTROLES_CESFAM], validators=[Optional()])
    fechas_sesiones_cesfam = StringField('Fechas de los controles a los que ha asistido (si aplica)', validators=[Optional()])

    bitacora_sesion = TextAreaField('Bitácora de la Sesión / Observaciones',
                                    validators=[DataRequired(message="La bitácora no puede estar vacía.")])

    submit = SubmitField('Guardar Cambios en Seguimiento')

class ReingresoForm(FlaskForm):
    fecha_reingreso = DateField('Fecha de Reingreso', validators=[DataRequired()], format='%Y-%m-%d')
    motivo_reingreso = SelectField('Motivo del Reingreso', choices=[('Ideación', 'Ideación'), ('Tentativa', 'Tentativa')], validators=[DataRequired()])
    carrera = SelectField('Carrera/Programa (al momento del reingreso)', validators=[DataRequired()])
    facultad = SelectField('Facultad (al momento del reingreso)', validators=[DataRequired()])
    estado_academico = SelectField('Estado Académico (al momento del reingreso)', validators=[DataRequired()])
    submit = SubmitField('Registrar Reingreso')