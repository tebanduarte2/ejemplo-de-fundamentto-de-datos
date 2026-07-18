"""
Dashboard COVID-19 (datos sintéticos)
Streamlit + Plotly
--------------------------------------------------
Genera un dataset sintético de 1000 registros / 8 columnas
con tipos de datos mixtos (fecha, texto, categórico, entero, float)
y permite explorarlo con métricas cuantitativas/cualitativas
y gráficas dinámicas totalmente personalizables por el usuario.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# Configuración general de la página
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard COVID-19 (datos sintéticos)",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAISES = ["Colombia", "México", "Argentina", "Chile", "Perú",
          "España", "Brasil", "Ecuador", "Uruguay", "Paraguay"]
SEXO = ["Masculino", "Femenino"]
GRAVEDAD = ["Leve", "Moderado", "Grave", "Crítico"]
ESTADO = ["Activo", "Recuperado", "Fallecido"]
SINTOMATICO = ["Sí", "No"]


# ----------------------------------------------------------------------
# 1. Generación de datos sintéticos (1000 registros x 8 columnas)
# ----------------------------------------------------------------------
def generar_datos(n_registros: int, seed: int) -> pd.DataFrame:
    """Simula un dataset tipo 'casos COVID' con tipos de datos variados."""
    rng = np.random.default_rng(seed)

    fecha_inicio = datetime(2022, 1, 1)
    dias_rango = (datetime(2023, 12, 31) - fecha_inicio).days
    fechas = [fecha_inicio + timedelta(days=int(d))
              for d in rng.integers(0, dias_rango, n_registros)]

    pais = rng.choice(PAISES, n_registros, p=_pesos(len(PAISES), rng))
    edad = rng.integers(0, 95, n_registros)
    sexo = rng.choice(SEXO, n_registros)

    # probabilidad de ser sintomático aumenta levemente con la edad
    prob_sintoma = np.clip(0.35 + edad / 250, 0.2, 0.9)
    sintomatico = np.where(rng.random(n_registros) < prob_sintoma, "Sí", "No")

    gravedad = rng.choice(GRAVEDAD, n_registros, p=[0.55, 0.25, 0.15, 0.05])

    # días de hospitalización correlacionados con la gravedad
    base_dias = {"Leve": 0, "Moderado": 3, "Grave": 8, "Crítico": 15}
    dias_hosp = np.array([
        max(0, int(rng.normal(base_dias[g], 2.5))) for g in gravedad
    ])

    # estado correlacionado con gravedad
    estado = []
    for g in gravedad:
        if g == "Crítico":
            p = [0.55, 0.30, 0.15]
        elif g == "Grave":
            p = [0.35, 0.58, 0.07]
        elif g == "Moderado":
            p = [0.20, 0.78, 0.02]
        else:
            p = [0.10, 0.895, 0.005]
        estado.append(rng.choice(ESTADO, p=p))

    df = pd.DataFrame({
        "fecha_diagnostico": pd.to_datetime(fechas),
        "pais": pd.Categorical(pais),
        "edad": edad.astype(int),
        "sexo": pd.Categorical(sexo),
        "sintomatico": pd.Categorical(sintomatico),
        "gravedad": pd.Categorical(gravedad, categories=GRAVEDAD, ordered=True),
        "dias_hospitalizacion": dias_hosp.astype(int),
        "estado": pd.Categorical(estado, categories=ESTADO),
    })
    return df.sort_values("fecha_diagnostico").reset_index(drop=True)


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
    st.caption("Los datos se simulan dentro de la plataforma.")

    n_registros = st.number_input(
        "Número de registros", min_value=200, max_value=5000,
        value=1000, step=100,
    )

    if st.button("🔄 Regenerar datos sintéticos", use_container_width=True):
        st.session_state.seed = np.random.randint(0, 1_000_000)

    st.caption(f"Semilla actual: `{st.session_state.seed}`")

df = generar_datos(int(n_registros), st.session_state.seed)

# ----------------------------------------------------------------------
# Filtros interactivos (sidebar)
# ----------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.subheader("🔎 Filtros")

    fecha_min, fecha_max = df["fecha_diagnostico"].min(), df["fecha_diagnostico"].max()
    rango_fechas = st.date_input(
        "Rango de fechas", value=(fecha_min.date(), fecha_max.date()),
        min_value=fecha_min.date(), max_value=fecha_max.date(),
    )

    paises_sel = st.multiselect("País", options=sorted(df["pais"].unique()),
                                 default=sorted(df["pais"].unique()))
    sexo_sel = st.multiselect("Sexo", options=SEXO, default=SEXO)
    gravedad_sel = st.multiselect("Gravedad", options=GRAVEDAD, default=GRAVEDAD)
    estado_sel = st.multiselect("Estado", options=ESTADO, default=ESTADO)
    rango_edad = st.slider("Rango de edad", 0, 94, (0, 94))

# aplicar filtros
if len(rango_fechas) == 2:
    f_ini, f_fin = rango_fechas
else:
    f_ini, f_fin = fecha_min.date(), fecha_max.date()

df_filtrado = df[
    (df["fecha_diagnostico"].dt.date >= f_ini) &
    (df["fecha_diagnostico"].dt.date <= f_fin) &
    (df["pais"].isin(paises_sel)) &
    (df["sexo"].isin(sexo_sel)) &
    (df["gravedad"].isin(gravedad_sel)) &
    (df["estado"].isin(estado_sel)) &
    (df["edad"].between(rango_edad[0], rango_edad[1]))
].copy()

st.title("🦠 Dashboard COVID-19 — Datos Sintéticos")
st.caption(
    "Dataset simulado con 8 variables (fecha, texto, categóricas, enteras) "
    "para exploración estadística e interactiva."
)

if df_filtrado.empty:
    st.warning("No hay registros con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

# ----------------------------------------------------------------------
# 2. Esquema de métricas: cuantitativas, cualitativas y gráficas
# ----------------------------------------------------------------------
col_numericas = ["edad", "dias_hospitalizacion"]
col_categoricas = ["pais", "sexo", "sintomatico", "gravedad", "estado"]

tab_resumen, tab_cuant, tab_cual, tab_graficas, tab_datos = st.tabs(
    ["📌 Resumen", "🔢 Cuantitativo", "🔤 Cualitativo", "📊 Gráficas dinámicas", "🗂️ Datos"]
)

# --- TAB RESUMEN --------------------------------------------------------
with tab_resumen:
    st.subheader("Indicadores clave (KPIs)")
    total = len(df_filtrado)
    fallecidos = (df_filtrado["estado"] == "Fallecido").sum()
    recuperados = (df_filtrado["estado"] == "Recuperado").sum()
    activos = (df_filtrado["estado"] == "Activo").sum()
    pct_sintomaticos = (df_filtrado["sintomatico"] == "Sí").mean() * 100
    edad_prom = df_filtrado["edad"].mean()
    dias_hosp_prom = df_filtrado["dias_hospitalizacion"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de registros", f"{total:,}")
    c2.metric("Tasa de letalidad", f"{(fallecidos/total*100):.1f}%",
              help="Fallecidos / Total de registros filtrados")
    c3.metric("Tasa de recuperación", f"{(recuperados/total*100):.1f}%")
    c4.metric("Casos activos", f"{activos:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Edad promedio", f"{edad_prom:.1f} años")
    c6.metric("% Sintomáticos", f"{pct_sintomaticos:.1f}%")
    c7.metric("Días hosp. promedio", f"{dias_hosp_prom:.1f}")
    c8.metric("Países representados", f"{df_filtrado['pais'].nunique()}")

    st.divider()
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Casos por estado**")
        fig = px.pie(df_filtrado, names="estado", hole=0.45,
                     color="estado",
                     color_discrete_map={"Activo": "#f2c744", "Recuperado": "#2ecc71", "Fallecido": "#e74c3c"})
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        st.markdown("**Evolución diaria de casos**")
        serie = df_filtrado.groupby(df_filtrado["fecha_diagnostico"].dt.date).size().reset_index(name="casos")
        fig2 = px.area(serie, x="fecha_diagnostico", y="casos")
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

    todas_columnas = col_numericas + col_categoricas + ["fecha_diagnostico"]

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
                              color_discrete_sequence=secuencia_color,
                              size="dias_hospitalizacion" if "dias_hospitalizacion" not in (var_x, y_scatter) else None,
                              opacity=0.7)
        elif tipo_grafico == "Línea temporal":
            serie = df_filtrado.groupby(
                [df_filtrado["fecha_diagnostico"].dt.to_period("W").dt.start_time] +
                ([color_arg] if color_arg else []), observed=True
            ).size().reset_index(name="casos")
            fig = px.line(serie, x="fecha_diagnostico", y="casos", color=color_arg,
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
                        file_name="covid_datos_sinteticos.csv", mime="text/csv")

    with st.expander("Tipos de datos por columna"):
        st.write(df_filtrado.dtypes.astype(str))
