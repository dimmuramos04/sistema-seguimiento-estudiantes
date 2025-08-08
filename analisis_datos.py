# Nombre del archivo: analisis_datos.py
# VERSIÓN FINAL: Lee desde un CSV y utiliza una paleta de colores "magma"
# consistente para los meses, garantizando un estilo profesional.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# --- Configuración ---
CSV_FILENAME = 'estudiantes_seguimiento.csv' 
OUTPUT_FOLDER = 'graficos_generados'

# --- Rutas de Archivos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, CSV_FILENAME)
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_FOLDER)

if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)
    print(f"Carpeta '{OUTPUT_FOLDER}' creada para guardar los gráficos.")

# --- MAPA DE COLORES CONSISTENTE PARA LOS MESES ---
nombres_meses_lista = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# *** CAMBIO DE ESTILO: Usar la paleta 'magma' para los meses ***
colores_meses_cmap = plt.colormaps.get('magma') 
# Se toman 12 colores espaciados uniformemente de la paleta 'magma'
mapa_colores_meses = {mes: colores_meses_cmap(i/11) for i, mes in enumerate(nombres_meses_lista)}


# --- Funciones de Carga y Preparación de Datos ---

def cargar_y_preparar_datos():
    if not os.path.exists(CSV_PATH):
        print(f"Error: No se encontró el archivo '{CSV_FILENAME}'.")
        return None
    try:
        df = pd.read_csv(CSV_PATH)
        print("Archivo CSV cargado exitosamente.")
        
        df['fecha_ingreso_programa'] = pd.to_datetime(df['fecha_ingreso_programa'], errors='coerce')
        df.dropna(subset=['fecha_ingreso_programa'], inplace=True)
        df = df[df['fecha_ingreso_programa'] != pd.Timestamp('2000-01-01')]

        df['Año'] = df['fecha_ingreso_programa'].dt.year
        df['Mes_Nombre'] = df['fecha_ingreso_programa'].dt.strftime('%B').str.capitalize()
        
        print(f"Se analizarán {len(df)} registros con fechas válidas.")
        return df
    except Exception as e:
        print(f"Ocurrió un error al cargar o procesar el archivo: {e}")
        return None

# --- Funciones de Graficación ---

def plot_columna_categorica(df, nombre_columna):
    if nombre_columna not in df.columns:
        print(f"\nError: La columna '{nombre_columna}' no existe.")
        return

    df_plot = df.copy()
    df_plot[nombre_columna] = df_plot[nombre_columna].fillna('No registrado')

    plt.figure(figsize=(14, 8))
    sns.set_theme(style="whitegrid")
    ax = sns.countplot(y=df_plot[nombre_columna], order=df_plot[nombre_columna].value_counts().index, palette='viridis', hue=df_plot[nombre_columna], legend=False)
    ax.set_title(f'Distribución por "{nombre_columna}"', fontsize=18, weight='bold')
    ax.set_xlabel('Cantidad de Registros', fontsize=12)
    ax.set_ylabel(nombre_columna, fontsize=12)

    for p in ax.patches:
        width = p.get_width()
        ax.text(width + (ax.get_xlim()[1] * 0.01), p.get_y() + p.get_height() / 2, f'{int(width)}', va='center')

    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_PATH, f'grafico_{nombre_columna}_{timestamp}.png')
    plt.savefig(filename)
    print(f"¡Gráfico guardado exitosamente como '{filename}'!")
    plt.show()
    plt.close()

def analizar_ingresos_por_año_y_mes(df):
    df_clean = df.copy()
    # 1. Gráfico de ingresos por AÑO
    plt.figure(figsize=(12, 7))
    sns.set_theme(style="whitegrid")
    
    ax_año = sns.countplot(x=df_clean['Año'], palette='plasma', hue=df_clean['Año'], legend=False)
    ax_año.set_title('Total de Ingresos al Programa por Año', fontsize=16, weight='bold')
    ax_año.set_xlabel('Año', fontsize=12)
    ax_año.set_ylabel('Cantidad de Ingresos', fontsize=12)

    for p in ax_año.patches:
        height = p.get_height()
        ax_año.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2., height), ha='center', va='bottom', xytext=(0,5), textcoords='offset points')

    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_año = os.path.join(OUTPUT_PATH, f'ingresos_por_año_{timestamp}.png')
    plt.savefig(filename_año)
    print(f"Gráfico de ingresos por año guardado como '{filename_año}'.")
    plt.show()
    plt.close()

    # 2. Pedir al usuario un año para el desglose mensual
    available_years = sorted(df_clean['Año'].unique())
    print(f"\nAños con datos disponibles: {available_years}")
    try:
        año_elegido = int(input(f"Ingresa un año de la lista para analizar en detalle: "))
    except ValueError:
        print("Entrada no válida.")
        return

    df_año = df_clean[df_clean['Año'] == año_elegido].copy()
    if df_año.empty:
        print(f"No se encontraron datos de ingresos para el año {año_elegido}.")
        return

    plt.figure(figsize=(12, 7))
    sns.set_theme(style="whitegrid")
    
    # Se usa el mapa de colores consistente
    ax_mes = sns.countplot(x=df_año['Mes_Nombre'], order=nombres_meses_lista, palette=mapa_colores_meses, hue=df_año['Mes_Nombre'], legend=False)
    ax_mes.set_title(f'Ingresos Mensuales al Programa en el Año {año_elegido}', fontsize=16, weight='bold')
    ax_mes.set_xlabel('Mes', fontsize=12)
    ax_mes.set_ylabel('Cantidad de Ingresos', fontsize=12)
    plt.xticks(rotation=45)
    
    for p in ax_mes.patches:
        height = p.get_height()
        ax_mes.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2., height), ha='center', va='bottom', xytext=(0,5), textcoords='offset points')

    plt.tight_layout()
    filename_mes = os.path.join(OUTPUT_PATH, f'ingresos_mensuales_{año_elegido}_{timestamp}.png')
    plt.savefig(filename_mes)
    print(f"Gráfico de ingresos para el año {año_elegido} guardado como '{filename_mes}'.")
    plt.show()
    plt.close()

def plot_ingresos_totales_por_mes(df):
    if df.empty:
        print("No hay datos para generar el gráfico.")
        return

    plt.figure(figsize=(12, 7))
    sns.set_theme(style="whitegrid")
    
    # Se usa el mapa de colores consistente
    ax = sns.countplot(x=df['Mes_Nombre'], order=nombres_meses_lista, palette=mapa_colores_meses, hue=df['Mes_Nombre'], legend=False)
    ax.set_title('Total de Ingresos al Programa por Mes (Todos los Años)', fontsize=16, weight='bold')
    ax.set_xlabel('Mes', fontsize=12)
    ax.set_ylabel('Cantidad Total de Ingresos', fontsize=12)
    plt.xticks(rotation=45)
    
    for p in ax.patches:
        height = p.get_height()
        ax.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2., height), ha='center', va='bottom', xytext=(0,5), textcoords='offset points')

    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_PATH, f'ingresos_totales_por_mes_{timestamp}.png')
    plt.savefig(filename)
    print(f"¡Gráfico guardado exitosamente como '{filename}'!")
    plt.show()
    plt.close()

# --- Menú Principal ---
def main_menu():
    df_estudiantes = cargar_y_preparar_datos()
    if df_estudiantes is None:
        input("\nPresiona Enter para salir.")
        return

    while True:
        print("\n" + "="*20 + " Menú de Análisis " + "="*20)
        print("1. Graficar una columna específica (ej: carrera_programa, genero)")
        print("2. Analizar ingresos al programa por Año y Mes")
        print("3. Analizar ingresos TOTALES al programa por Mes (sumando todos los años)")
        print("4. Salir")
        print("="*58)
        
        opcion = input("Elige una opción: ")

        if opcion == '1':
            print("\n--- Columnas Disponibles ---")
            print(", ".join(df_estudiantes.columns))
            columna_elegida = input("Escribe el nombre exacto de la columna que quieres graficar: ")
            plot_columna_categorica(df_estudiantes, columna_elegida)
        
        elif opcion == '2':
            analizar_ingresos_por_año_y_mes(df_estudiantes)
            
        elif opcion == '3':
            plot_ingresos_totales_por_mes(df_estudiantes)

        elif opcion == '4':
            print("Saliendo del programa. ¡Hasta luego!")
            break
        
        else:
            print("Opción no válida. Por favor, elige 1, 2, 3 o 4.")

if __name__ == '__main__':
    # Configurar el locale para que los nombres de los meses salgan en español
    try:
        import locale
        # Intentar varias configuraciones comunes para español
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish')
        except locale.Error:
            print("Advertencia: No se pudo configurar el locale a español. Los meses podrían aparecer en inglés.")
            
    main_menu()
