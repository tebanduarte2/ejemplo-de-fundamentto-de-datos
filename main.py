import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="COVID-19 Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# -----------------------------------------------------------------------------
# TAREA 1: Simulación de datos sintéticos (1000 registros, 8 columnas)
# -----------------------------------------------------------------------------
@st.cache_data
def generar_datos_covid():
    np.random.seed(42)  # Semilla para consistencia
    n_registros = 1000
    
    # 1. ID de Paciente (Entero/String)
    id_paciente = [f"PAC-{i:04d}" for i in range(1, n_registros + 1)]
    
    # 2. Fecha de Diagnóstico (Datetime)
    fecha_inicio = datetime(2023, 1, 1)
    fechas = [fecha_inicio + timedelta(days=int(np.random.randint(0, 365))) for _ in range(n_registros)]
    
    # 3. Edad (Entero)
    edad = np.random.randint(1, 90, size=n_registros)
    
    # 4. Género (Categoría)
    genero = np.random.choice(["Masculino", "Femenino", "Otro"], size=n_registros, p=[0.48, 0.49, 0.03])
    
    # 5. Variante Detectada (Categoría)
    variantes = np.random.choice(["Ómicron", "Delta", "XBB.1.5", "JN.1"], size=n_registros, p=[0.40, 0.15, 0.25, 0.20])
    
    # 6. Estado Actual (Categoría)
    estado = np.random.choice(["Recuperado", "Activo", "Fallecido"], size=n_registros, p=[0.85, 0.12, 0.03])
    
    # 7. Días de Hospitalización (Entero / Simulado con sesgo)
    dias_hosp = np.random.negative_binomial(n=2, p=0.15, size=n_registros) 
    
    # 8. Carga Viral Logarítmica (Flotante)
    carga_viral = np.round(np.random.normal(loc=5.5, scale=1.5, size=n_registros), 2)
    carga_viral = np.clip(carga_viral, 1.0, 10.0) # Limitar rangos lógicos
    
    df = pd.DataFrame({
        "ID_Paciente": id_paciente,
        "Fecha_Diagnostico": fechas,
        "Edad": edad,
        "Genero": genero,
        "Variante": variantes,
        "Estado": estado,
        "Dias_Hospitalizacion": dias_hosp,
        "Carga_Viral": carga_viral
    })
    return df

df = generar_datos_covid()

# Título de la app
st.title("📊 Dashboard Interactivo de Análisis COVID-19")
st.markdown("Datos sintéticos generados en tiempo real para análisis epidemiológico.")

# Sidebar para filtros globales de datos
st.sidebar.header("Filtros Globales")
variante_filter = st.sidebar.multiselect("Filtrar por Variante:", options=df["Variante"].unique(), default=df["Variante"].unique())
estado_filter = st.sidebar.multiselect("Filtrar por Estado Clínico:", options=df["Estado"].unique(), default=df["Estado"].unique())

df_filtrado = df[(df["Variante"].isin(variante_filter)) & (df["Estado"].isin(estado_filter))]

# Visualización rápida de los datos mutados
with st.expander("👀 Ver registros simulados (Primeras 5 filas)"):
    st.dataframe(df_filtrado.head(), use_container_width=True)

# -----------------------------------------------------------------------------
# TAREA 2: Esquema de Métricas Estadísticas
# -----------------------------------------------------------------------------
st.header("📈 Esquema de Métricas")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Análisis Cuantitativo")
    # Métricas numéricas puras
    edad_promedio = int(df_filtrado["Edad"].mean()) if not df_filtrado.empty else 0
    promedio_hosp = round(df_filtrado["Dias_Hospitalizacion"].mean(), 1) if not df_filtrado.empty else 0
    
    st.metric(label="Edad Promedio de Pacientes", value=f"{edad_promedio} años")
    st.metric(label="Promedio Días Hospitalización", value=f"{promedio_hosp} días")

with col2:
    st.subheader("Análisis Cualitativo")
    # Métricas basadas en conteos/proporciones de texto
    if not df_filtrado.empty:
        variante_top = df_filtrado["Variante"].mode()[0]
        pct_recuperados = round((df_filtrado["Estado"] == "Recuperado").sum() / len(df_filtrado) * 100, 1)
    else:
        variante_top = "N/A"
        pct_recuperados = 0
        
    st.metric(label="Variante Más Frecuente", value=variante_top)
    st.metric(label="Tasa de Recuperación", value=f"{pct_recuperados}%")

with col3:
    st.subheader("Resumen de Población")
    st.metric(label="Total Casos Filtrados", value=len(df_filtrado), delta=len(df_filtrado) - len(df))

st.markdown("---")

# -----------------------------------------------------------------------------
# TAREA 3: Gráficas Dinámicas y Personalización (Plotly)
# -----------------------------------------------------------------------------
st.header("🎛️ Centro de Gráficos Personalizables")

if df_filtrado.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados en la barra lateral.")
else:
    # Controles de personalización del usuario
    layout_controles = st.columns(4)
    
    with layout_controles[0]:
        tipo_grafico = st.selectbox(
            "1. Tipo de Gráfico:",
            ["Dispersión (Scatter)", "Histograma de Distribución", "Evolución Temporal"]
        )
        
    with layout_controles[1]:
        # Variables numéricas disponibles
        vars_numericas = ["Edad", "Carga_Viral", "Dias_Hospitalizacion"]
        var_x = st.selectbox("2. Variable Eje X:", vars_numericas, index=0)
        
    with layout_controles[2]:
        # Variable de color/segmentación
        var_color = st.selectbox("3. Segmentar por (Color):", ["Variante", "Genero", "Estado"])
        
    with layout_controles[3]:
        # Selector de color de Plotly
        paleta_color = st.selectbox("4. Paleta de Colores:", ["Viridis", "Plasma", "Prism", "Safe"])

    # Barra para umbrales interactiva
    st.markdown("#### Ajuste de Umbral Crítico")
    umbral_activado = st.checkbox("Habilitar línea de umbral en el gráfico")
    
    valor_umbral = 0.0
    if umbral_activado:
        min_val = float(df_filtrado[var_x].min())
        max_val = float(df_filtrado[var_x].max())
        valor_umbral = st.slider(f"Definir línea de alerta para {var_x}:", min_value=min_val, max_value=max_val, value=(min_val + max_val)/2)

    # Renderizado dinámico del gráfico según la selección
    paletas_dict = {"Viridis": px.colors.sequential.Viridis, "Plasma": px.colors.sequential.Plasma, "Prism": px.colors.qualitative.Prism, "Safe": px.colors.qualitative.Safe}
    color_scale = paletas_dict[paleta_color]

    if tipo_grafico == "Dispersión (Scatter)":
        var_y = st.selectbox("Selecciona Eje Y (solo para Scatter):", [v for v in vars_numericas if v != var_x])
        fig = px.scatter(
            df_filtrado, x=var_x, y=var_y, color=var_color,
            color_discrete_sequence=color_scale if paleta_color in ["Prism", "Safe"] else None,
            color_continuous_scale=color_scale if paleta_color in ["Viridis", "Plasma"] else None,
            title=f"Relación entre {var_x} y {var_y}",
            template="plotly_white"
        )
        if umbral_activado:
            fig.add_vline(x=valor_umbral, line_dash="dash", line_color="red", annotation_text="Umbral X")

    elif tipo_grafico == "Histograma de Distribución":
        fig = px.histogram(
            df_filtrado, x=var_x, color=var_color, barmode="overlay",
            color_discrete_sequence=color_scale if paleta_color in ["Prism", "Safe"] else None,
            title=f"Distribución de la variable: {var_x}",
            template="plotly_white"
        )
        if umbral_activado:
            fig.add_vline(x=valor_umbral, line_dash="dash", line_color="red", annotation_text="Umbral Alerta")

    elif tipo_grafico == "Evolución Temporal":
        # Agrupar por fecha y por la variable cualitativa seleccionada
        df_tiempo = df_filtrado.groupby(["Fecha_Diagnostico", var_color]).size().reset_index(name="Casos")
        fig = px.line(
            df_tiempo, x="Fecha_Diagnostico", y="Casos", color=var_color,
            color_discrete_sequence=color_scale if paleta_color in ["Prism", "Safe"] else None,
            title="Nuevos casos registrados a lo largo del tiempo",
            template="plotly_white"
        )

    # Mostrar gráfico en Streamlit de forma responsiva
    st.plotly_chart(fig, use_container_width=True)
