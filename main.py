"""
Dashboard de Estadísticas de Salud Pública — Suicidio en China (datos sintéticos)
Streamlit + Plotly
--------------------------------------------------
IMPORTANTE: Todos los datos son 100% sintéticos y se generan dentro de la
plataforma con fines estadísticos/educativos. No representan personas ni
casos reales. El dataset se enfoca en variables demográficas y de contexto
epidemiológico (sin ningún detalle de método), apto para análisis de
prevención en salud pública.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# Configuración general de la página
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Salud Pública — China (datos sintéticos)",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# 0. Control de acceso por clave
# ----------------------------------------------------------------------
CLAVE_DASHBOARD = "4477"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Dashboard protegido")
    st.write("Ingresa la clave de acceso para continuar.")
    clave_ingresada = st.text_input("Clave", type="password")
    col1, _ = st.columns([1, 4])
    with col1:
        if st.button("Ingresar", use_container_width=True):
            if clave_ingresada == CLAVE_DASHBOARD:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta.")
    st.stop()

# ----------------------------------------------------------------------
# Catálogos de variables
# ----------------------------------------------------------------------
PROVINCIAS = [
    "Guangdong", "Shandong", "Henan", "Sichuan", "Jiangsu",
    "Hebei", "Hunan", "Anhui", "Zhejiang", "Yunnan",
]
SEXO = ["Masculino", "Femenino"]
AREA = ["Urbana", "Rural"]
ESTADO_CIVIL = ["Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)"]
CONTACTO_SALUD_MENTAL = ["Sí", "No"]


# ----------------------------------------------------------------------
# 1. Generación de datos sintéticos (1000 registros x 8 columnas)
# ----------------------------------------------------------------------
def generar_datos(n_registros: int, seed: int) -> pd.DataFrame:
    """Simula un dataset agregado de contexto epidemiológico (sin datos
    de método ni información clínica sensible), útil para prácticas de
    análisis de salud pública."""
    rng = np.random.default_rng(seed)

    fecha_inicio = datetime(2022, 1, 1)
    dias_rango = (datetime(2023, 12, 31) - fecha_inicio).days
    fechas = [fecha_inicio + timedelta(days=int(d))
              for d in rng.integers(0, dias_rango, n_registros)]

    provincia = rng.choice(PROVINCIAS, n_registros, p=_pesos(len(PROVINCIAS), rng))
    edad = rng.integers(15, 90, n_registros)
    sexo = rng.choice(SEXO, n_registros, p=[0.58, 0.42])
    area = rng.choice(AREA, n_registros, p=[0.45, 0.55])
    estado_civil = rng.choice(ESTADO_CIVIL, n_registros, p=[0.30, 0.45, 0.15, 0.10])

    # probabilidad de contacto previo con servicios de salud mental
    prob_contacto = np.clip(0.20 + (edad < 30) * 0.08 + (area == "Urbana") * 0.10, 0.1, 0.6)
    contacto_salud_mental = np.where(rng.random(n_registros) < prob_contacto, "Sí", "No")

    # tasa por 100,000 habitantes (indicador agregado, no un dato individual)
    tasa_100k = np.round(rng.normal(9.5, 3.2, n_registros).clip(0.5, 25), 2)

    df = pd.DataFrame({
        "fecha_registro": pd.to_datetime(fechas),
        "provincia": pd.Categorical(provincia),
        "edad": edad.astype(int),
        "sexo": pd.Categorical(sexo),
        "area": pd.Categorical(area),
        "estado_civil": pd.Categorical(estado_civil),
        "contacto_previo_salud_mental": pd.Categorical(contacto_salud_mental),
        "tasa_por_100k": tasa_100k.astype(float),
    })
    return df.sort_values("fecha_registro").reset_index(drop=True)


def _pesos(n, rng):
    w = rng.random(n)
    return w / w.sum()


# ----------------------------------------------------------------------
# Estado de sesión: semilla / regeneración de datos desde la app
# ----------------------------------------------------------------------
if "seed" not in st.session_state:
    st.session_state.seed = 42

with st.sidebar:
    st.title("⚙️ Panel de control")
    st.caption("Los datos se simulan dentro de la plataforma (100% sintéticos).")

    n_registros = st.number_input(
        "Número de registros", min_value=200, max_value=5000,
        value=1000, step=100,
    )

    if st.button("🔄 Regenerar datos sintéticos", use_container_width=True):
        st.session_state.seed = np.random.randint(0, 1_000_000)

    st.caption(f"Semilla actual: `{st.session_state.seed}`")

    if st.button("🔒 Cerrar sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

df = generar_datos(int(n_registros), st.session_state.seed)

# ----------------------------------------------------------------------
# Filtros interactivos (sidebar)
# ----------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.subheader("🔎 Filtros")

    fecha_min, fecha_max = df["fecha_registro"].min(), df["fecha_registro"].max()
    rango_fechas = st.date_input(
        "Rango de fechas", value=(fecha_min.date(), fecha_max.date()),
        min_value=fecha_min.date(), max_value=fecha_max.date(),
    )

    provincias_sel = st.multiselect("Provincia", options=sorted(df["provincia"].unique()),
                                     default=sorted(df["provincia"].unique()))
    sexo_sel = st.multiselect("Sexo", options=SEXO, default=SEXO)
    area_sel = st.multiselect("Área", options=AREA, default=AREA)
    estado_civil_sel = st.multiselect("Estado civil", options=ESTADO_CIVIL, default=ESTADO_CIVIL)
    rango_edad = st.slider("Rango de edad", 15, 89, (15, 89))

# aplicar filtros
if len(rango_fechas) == 2:
    f_ini, f_fin = rango_fechas
else:
    f_ini, f_fin = fecha_min.date(), fecha_max.date()

df_filtrado = df[
    (df["fecha_registro"].dt.date >= f_ini) &
    (df["fecha_registro"].dt.date <= f_fin) &
    (df["provincia"].isin(provincias_sel)) &
    (df["sexo"].isin(sexo_sel)) &
    (df["area"].isin(area_sel)) &
    (df["estado_civil"].isin(estado_civil_sel)) &
    (df["edad"].between(rango_edad[0], rango_edad[1]))
].copy()

st.title("📊 Dashboard de Salud Pública — China (Datos Sintéticos)")
st.caption(
    "Dataset simulado con 8 variables demográficas y de contexto epidemiológico "
    "para práctica de análisis estadístico. No contiene datos reales ni de método."
)
st.info(
    "Este panel usa datos **completamente simulados** con fines educativos/estadísticos. "
    "No representa casos reales ni información clínica.",
    icon="ℹ️",
)

if df_filtrado.empty:
    st.warning("No hay registros con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

# ----------------------------------------------------------------------
# 2. Esquema de métricas: cuantitativas, cualitativas y gráficas
# ----------------------------------------------------------------------
col_numericas = ["edad", "tasa_por_100k"]
col_categoricas = ["provincia", "sexo", "area", "estado_civil", "contacto_previo_salud_mental"]

tab_resumen, tab_cuant, tab_cual, tab_graficas, tab_datos = st.tabs(
    ["📌 Resumen", "🔢 Cuantitativo", "🔤 Cualitativo", "📊 Gráficas dinámicas", "🗂️ Datos"]
)

# --- TAB RESUMEN --------------------------------------------------------
with tab_resumen:
    st.subheader("Indicadores clave (KPIs)")
    total = len(df_filtrado)
    tasa_prom = df_filtrado["tasa_por_100k"].mean()
    edad_prom = df_filtrado["edad"].mean()
    pct_contacto = (df_filtrado["contacto_previo_salud_mental"] == "Sí").mean() * 100
    pct_rural = (df_filtrado["area"] == "Rural").mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de registros", f"{total:,}")
    c2.metric("Tasa promedio (x100k hab.)", f"{tasa_prom:.2f}")
    c3.metric("Edad promedio", f"{edad_prom:.1f} años")
    c4.metric("% Área rural", f"{pct_rural:.1f}%")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("% Con contacto previo a salud mental", f"{pct_contacto:.1f}%")
    c6.metric("Provincias representadas", f"{df_filtrado['provincia'].nunique()}")
    c7.metric("Tasa máxima registrada", f"{df_filtrado['tasa_por_100k'].max():.2f}")
    c8.metric("Tasa mínima registrada", f"{df_filtrado['tasa_por_100k'].min():.2f}")

    st.divider()
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Distribución por provincia**")
        conteo_prov = df_filtrado["provincia"].value_counts().reset_index()
        conteo_prov.columns = ["provincia", "registros"]
        fig = px.bar(conteo_prov, x="provincia", y="registros", color="provincia")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        st.markdown("**Tasa promedio mensual (x100k hab.)**")
        serie = df_filtrado.groupby(df_filtrado["fecha_registro"].dt.to_period("M").dt.start_time)[
            "tasa_por_100k"].mean().reset_index()
        fig2 = px.line(serie, x="fecha_registro", y="tasa_por_100k", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

# --- TAB CUANTITATIVO ----------------------------------------------------
with tab_cuant:
    st.subheader("Estadística descriptiva — variables cuantitativas")
    stats = df_filtrado[col_numericas].describe().T
    stats["mediana"] = df_filtrado[col_numericas].median()
    stats["varianza"] = df_filtrado[col_numericas].var()
    stats = stats.rename(columns={
        "count": "n", "mean": "media", "std": "desv_estándar",
        "min": "mínimo", "max": "máximo",
        "25%": "p25", "50%": "p50", "75%": "p75",
    })
    st.dataframe(stats.style.format("{:.2f}"), use_container_width=True)

    st.markdown("**Distribución de variables numéricas**")
    var_num = st.selectbox("Variable numérica", col_numericas, key="var_num_cuant")
    fig = px.histogram(df_filtrado, x=var_num, nbins=30, marginal="box",
                        color_discrete_sequence=["#3498db"])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Matriz de correlación**")
    corr = df_filtrado[col_numericas].corr()
    fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
    st.plotly_chart(fig_corr, use_container_width=True)

# --- TAB CUALITATIVO ------------------------------------------------------
with tab_cual:
    st.subheader("Estadística descriptiva — variables cualitativas")
    resumen_cual = pd.DataFrame({
        "moda": df_filtrado[col_categoricas].agg(lambda s: s.mode().iat[0]),
        "n_categorías": df_filtrado[col_categoricas].nunique(),
        "frecuencia_moda": df_filtrado[col_categoricas].agg(
            lambda s: (s == s.mode().iat[0]).sum()),
    })
    resumen_cual["%_moda"] = (resumen_cual["frecuencia_moda"] / len(df_filtrado) * 100).round(1)
    st.dataframe(resumen_cual, use_container_width=True)

    var_cat = st.selectbox("Variable categórica", col_categoricas, key="var_cat_cual")
    conteo = df_filtrado[var_cat].value_counts().reset_index()
    conteo.columns = [var_cat, "conteo"]
    fig_cat = px.bar(conteo, x=var_cat, y="conteo", color=var_cat, text="conteo")
    st.plotly_chart(fig_cat, use_container_width=True)

# --- TAB GRÁFICAS DINÁMICAS ------------------------------------------------
with tab_graficas:
    st.subheader("Constructor de gráficas dinámicas")
    st.caption("Elige variables, tipo de gráfico, colores y umbrales de referencia.")

    todas_columnas = col_numericas + col_categoricas + ["fecha_registro"]

    c1, c2, c3 = st.columns(3)
    with c1:
        tipo_grafico = st.selectbox(
            "Tipo de gráfico",
            ["Histograma", "Barras", "Dispersión (scatter)", "Línea temporal",
             "Boxplot", "Violín", "Pastel"],
        )
    with c2:
        var_x = st.selectbox("Variable eje X", todas_columnas, index=0)
    with c3:
        opciones_y = ["(ninguna)"] + col_numericas
        var_y = st.selectbox(
            "Variable eje Y (si aplica)", opciones_y,
            index=1 if tipo_grafico in ("Dispersión (scatter)", "Boxplot", "Violín", "Barras") else 0,
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        var_color = st.selectbox("Colorear por", ["(ninguna)"] + col_categoricas)
    with c5:
        paleta = st.selectbox(
            "Paleta de colores",
            ["Plotly", "Viridis", "Bold", "Pastel", "Set2", "Vivid"],
        )
    with c6:
        titulo_custom = st.text_input("Título del gráfico", value="Análisis de variable")

    color_arg = None if var_color == "(ninguna)" else var_color
    y_arg = None if var_y == "(ninguna)" else var_y

    paletas_map = {
        "Plotly": px.colors.qualitative.Plotly,
        "Viridis": px.colors.sequential.Viridis,
        "Bold": px.colors.qualitative.Bold,
        "Pastel": px.colors.qualitative.Pastel,
        "Set2": px.colors.qualitative.Set2,
        "Vivid": px.colors.qualitative.Vivid,
    }
    secuencia_color = paletas_map[paleta]

    # --- Umbral de referencia (solo si hay variable numérica involucrada) ---
    mostrar_umbral = st.checkbox("Mostrar línea de umbral de referencia", value=False)
    valor_umbral = None
    if mostrar_umbral:
        var_umbral_candidata = y_arg if y_arg else (var_x if var_x in col_numericas else None)
        if var_umbral_candidata:
            min_v = float(df_filtrado[var_umbral_candidata].min())
            max_v = float(df_filtrado[var_umbral_candidata].max())
            valor_umbral = st.slider(
                f"Valor de umbral para '{var_umbral_candidata}'",
                min_value=min_v, max_value=max_v,
                value=float((min_v + max_v) / 2),
            )
        else:
            st.info("Selecciona una variable numérica en X o Y para aplicar un umbral.")

    fig = None
    try:
        if tipo_grafico == "Histograma":
            fig = px.histogram(df_filtrado, x=var_x, color=color_arg,
                                color_discrete_sequence=secuencia_color, barmode="overlay",
                                opacity=0.8)
        elif tipo_grafico == "Barras":
            if y_arg:
                agg = df_filtrado.groupby([var_x] + ([color_arg] if color_arg else []), observed=True)[y_arg].mean().reset_index()
                fig = px.bar(agg, x=var_x, y=y_arg, color=color_arg,
                             color_discrete_sequence=secuencia_color, barmode="group")
            else:
                conteo = df_filtrado.groupby(var_x, observed=True).size().reset_index(name="conteo")
                fig = px.bar(conteo, x=var_x, y="conteo", color=var_x,
                             color_discrete_sequence=secuencia_color)
        elif tipo_grafico == "Dispersión (scatter)":
            y_scatter = y_arg or col_numericas[0]
            fig = px.scatter(df_filtrado, x=var_x, y=y_scatter, color=color_arg,
                              color_discrete_sequence=secuencia_color, opacity=0.7)
        elif tipo_grafico == "Línea temporal":
            serie = df_filtrado.groupby(
                [df_filtrado["fecha_registro"].dt.to_period("W").dt.start_time] +
                ([color_arg] if color_arg else []), observed=True
            ).size().reset_index(name="registros")
            fig = px.line(serie, x="fecha_registro", y="registros", color=color_arg,
                           color_discrete_sequence=secuencia_color, markers=True)
        elif tipo_grafico == "Boxplot":
            y_box = y_arg or col_numericas[0]
            fig = px.box(df_filtrado, x=var_x, y=y_box, color=color_arg,
                         color_discrete_sequence=secuencia_color)
        elif tipo_grafico == "Violín":
            y_vio = y_arg or col_numericas[0]
            fig = px.violin(df_filtrado, x=var_x, y=y_vio, color=color_arg,
                            color_discrete_sequence=secuencia_color, box=True)
        elif tipo_grafico == "Pastel":
            fig = px.pie(df_filtrado, names=var_x, color_discrete_sequence=secuencia_color)

        if fig is not None:
            fig.update_layout(title=titulo_custom, template="plotly_white", height=520)
            if mostrar_umbral and valor_umbral is not None and tipo_grafico != "Pastel":
                fig.add_hline(y=valor_umbral, line_dash="dash", line_color="red",
                               annotation_text=f"Umbral = {valor_umbral:.1f}",
                               annotation_position="top left")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"No fue posible generar el gráfico con esta combinación de variables: {e}")

# --- TAB DATOS --------------------------------------------------------------
with tab_datos:
    st.subheader("Explorador de datos filtrados")
    st.dataframe(df_filtrado, use_container_width=True, height=450)
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV filtrado", data=csv,
                        file_name="datos_sinteticos_salud_publica.csv", mime="text/csv")

    with st.expander("Tipos de datos por columna"):
        st.write(df_filtrado.dtypes.astype(str))
