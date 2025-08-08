# Nombre del archivo: reportes_visuales.py
# Este script se especializa en crear informes visuales complejos,
# como gráficos de torta y dashboards de varios gráficos en una sola imagen.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# --- Configuración ---
CSV_FILENAME = 'estudiantes_seguimiento.csv' 
OUTPUT_FOLDER = 'reportes_visuales_generados' # Nueva carpeta para estos reportes

# --- Rutas de Archivos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, CSV_FILENAME)
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_FOLDER)

if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)
    print(f"Carpeta '{OUTPUT_FOLDER}' creada para guardar los reportes.")

# --- Funciones de Carga y Preparación de Datos ---

def cargar_y_preparar_datos():
    """Carga y prepara el DataFrame desde el archivo CSV."""
    if not os.path.exists(CSV_PATH):
        print(f"Error: No se encontró el archivo '{CSV_FILENAME}'.")
        return None
    try:
        df = pd.read_csv(CSV_PATH)
        print("Archivo CSV cargado exitosamente.")
        
        # Procesamiento de fechas robusto
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

def generar_reporte_demografico(df):
    """
    Crea una sola imagen con dos gráficos de torta: uno para Género y otro para Estado en Programa.
    """
    print("\nGenerando reporte demográfico...")
    df_plot = df.copy()
    
    # Preparar datos para ambos gráficos
    df_plot['genero'] = df_plot['genero'].fillna('No registrado')
    df_plot['estado_en_programa'] = df_plot['estado_en_programa'].fillna('No registrado')
    
    conteo_genero = df_plot['genero'].value_counts()
    conteo_estado = df_plot['estado_en_programa'].value_counts()
    
    # Crear una figura con dos subplots, uno al lado del otro
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    sns.set_theme(style="whitegrid")

    # Gráfico 1: Género
    colores_genero = plt.cm.get_cmap('Pastel1')(range(len(conteo_genero)))
    ax1.pie(conteo_genero, labels=conteo_genero.index, autopct='%1.1f%%', startangle=140, colors=colores_genero,
            wedgeprops=dict(width=0.4)) # El 'width' crea el efecto de "dona"
    ax1.set_title('Distribución por Género', fontsize=16, weight='bold')
    ax1.axis('equal') # Asegura que la torta sea un círculo

    # Gráfico 2: Estado en Programa
    colores_estado = plt.cm.get_cmap('Pastel2')(range(len(conteo_estado)))
    ax2.pie(conteo_estado, labels=conteo_estado.index, autopct='%1.1f%%', startangle=140, colors=colores_estado,
            wedgeprops=dict(width=0.4))
    ax2.set_title('Distribución por Estado en Programa', fontsize=16, weight='bold')
    ax2.axis('equal')

    fig.suptitle('Reporte Demográfico de Estudiantes', fontsize=22, weight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Ajustar para que el título principal no se solape
    
    # Guardar el reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_PATH, f'reporte_demografico_{timestamp}.png')
    plt.savefig(filename, dpi=300)
    print(f"¡Reporte guardado exitosamente como '{filename}'!")
    plt.show()
    plt.close()

def generar_dashboard_ingresos(df):
    """
    Crea un dashboard 2x2 en una sola imagen con el análisis de ingresos.
    Muestra el total por año y el desglose de los 3 años más recientes.
    """
    print("\nGenerando dashboard de ingresos...")
    df_clean = df.copy()
    nombres_meses_lista = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # Crear la figura y la grilla de subplots 2x2
    fig, axs = plt.subplots(2, 2, figsize=(20, 14))
    sns.set_theme(style="whitegrid")

    # --- Gráfico 1 (Superior Izquierda): Total de Ingresos por Año ---
    ax_total_año = axs[0, 0]
    sns.countplot(x=df_clean['Año'], ax=ax_total_año, palette='plasma', hue=df_clean['Año'], legend=False)
    ax_total_año.set_title('Total de Ingresos por Año', fontsize=14, weight='bold')
    ax_total_año.set_xlabel(None)
    ax_total_año.set_ylabel('Cantidad de Ingresos')
    for p in ax_total_año.patches:
        height = p.get_height()
        ax_total_año.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2., height), ha='center', va='bottom', xytext=(0,5), textcoords='offset points')

    # --- Gráficos de Desglose Mensual para los 3 años más recientes ---
    años_recientes = sorted(df_clean['Año'].unique(), reverse=True)[:3]
    posiciones = [(0, 1), (1, 0), (1, 1)] # Posiciones en la grilla para los gráficos de desglose

    for i, año in enumerate(años_recientes):
        ax_mes = axs[posiciones[i]] # Seleccionar el subplot correcto
        df_año = df_clean[df_clean['Año'] == año]
        
        # Crear un mapa de colores consistente para los meses
        colores_cmap = plt.colormaps.get('magma') 
        mapa_colores = {mes: colores_cmap(j/11) for j, mes in enumerate(nombres_meses_lista)}

        sns.countplot(x=df_año['Mes_Nombre'], order=nombres_meses_lista, ax=ax_mes, palette=mapa_colores, hue=df_año['Mes_Nombre'], legend=False)
        ax_mes.set_title(f'Desglose de Ingresos - Año {año}', fontsize=14, weight='bold')
        ax_mes.set_xlabel(None)
        ax_mes.set_ylabel('Cantidad de Ingresos')
        ax_mes.tick_params(axis='x', rotation=45)
        for p in ax_mes.patches:
            height = p.get_height()
            if height > 0: # Solo añadir etiqueta si hay datos
                ax_mes.annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2., height), ha='center', va='bottom', xytext=(0,5), textcoords='offset points')

    # Si hay menos de 3 años, ocultar los subplots sobrantes
    for i in range(len(años_recientes), 3):
        axs[posiciones[i]].axis('off')

    fig.suptitle('Dashboard de Análisis de Ingresos', fontsize=24, weight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Guardar el dashboard
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_PATH, f'dashboard_ingresos_{timestamp}.png')
    plt.savefig(filename, dpi=300)
    print(f"¡Dashboard guardado exitosamente como '{filename}'!")
    plt.show()
    plt.close()


# --- Menú Principal ---
def main_menu():
    df_estudiantes = cargar_y_preparar_datos()
    if df_estudiantes is None:
        input("\nPresiona Enter para salir.")
        return

    while True:
        print("\n" + "="*20 + " Menú de Reportes Visuales " + "="*20)
        print("1. Generar Reporte Demográfico (Gráficos de Torta)")
        print("2. Generar Dashboard de Ingresos por Tiempo")
        print("3. Salir")
        print("="*62)
        
        opcion = input("Elige una opción: ")

        if opcion == '1':
            generar_reporte_demografico(df_estudiantes)
        
        elif opcion == '2':
            generar_dashboard_ingresos(df_estudiantes)
            
        elif opcion == '3':
            print("Saliendo del programa. ¡Hasta luego!")
            break
        
        else:
            print("Opción no válida. Por favor, elige 1, 2 o 3.")

if __name__ == '__main__':
    # Configurar el locale para que los nombres de los meses salgan en español
    try:
        import locale
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish')
        except locale.Error:
            print("Advertencia: No se pudo configurar el locale a español. Los meses podrían aparecer en inglés.")
            
    main_menu()
