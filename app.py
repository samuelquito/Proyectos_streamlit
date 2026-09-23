import streamlit as st
import pandas as pd
import numpy as np
import datetime

# --- Configuración de la página ---
st.set_page_config(
    page_title="Portal de Proyectos - Samuel Quito",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos personalizados ---
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Barra lateral ---
with st.sidebar:
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=60)
    st.title("Panel de Control")
    st.markdown("**Desarrollador:** Samuel Quito")
    st.markdown("[Ver Perfil GitHub](https://github.com/samuelquito)")
    
    st.divider()
    
    seccion = st.radio(
        "Navegación:",
        ["📊 Dashboard Resumen", "📈 Análisis Interactivo", "ℹ️ Acerca del Proyecto"]
    )
    
    st.divider()
    st.info("💡 App conectada y desplegada en Streamlit Community Cloud.")

# --- Vista 1: Dashboard Resumen ---
if seccion == "📊 Dashboard Resumen":
    st.markdown('<div class="main-title">🚀 Dashboard Principal de Proyectos</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Bienvenido a la aplicación Streamlit de Samuel Quito.</div>', unsafe_allow_html=True)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Proyectos", value="12", delta="+2 este mes")
    with col2:
        st.metric(label="Usuarios Activos", value="1,450", delta="+15%")
    with col3:
        st.metric(label="Tasa de Éxito", value="98.5%", delta="+0.8%")
    with col4:
        st.metric(label="Estado del Servidor", value="Operativo 🟢")
        
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    fechas = pd.date_range(datetime.date.today() - datetime.timedelta(days=29), periods=30)
    np.random.seed(42)
    datos_tendencia = pd.DataFrame({
        "Fecha": fechas,
        "Consultas": np.random.randint(100, 300, size=30).cumsum() / 10,
        "Actividad": np.random.randint(40, 150, size=30)
    }).set_index("Fecha")
    
    with col_chart1:
        st.subheader("📈 Crecimiento de Actividad")
        st.line_chart(datos_tendencia["Consultas"], use_container_width=True)
        
    with col_chart2:
        st.subheader("📊 Registros Diarios")
        st.bar_chart(datos_tendencia["Actividad"], use_container_width=True)

# --- Vista 2: Análisis Interactivo ---
elif seccion == "📈 Análisis Interactivo":
    st.markdown('<div class="main-title">🧪 Explorador de Datos Interactivo</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Filtra parámetros y genera visualizaciones en tiempo real.</div>', unsafe_allow_html=True)
    
    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    
    with col_ctrl1:
        st.subheader("⚙️ Parámetros")
        n_puntos = st.slider("Cantidad de registros:", min_value=10, max_value=500, value=100, step=10)
        categoria = st.selectbox("Seleccionar Categoría:", ["Ventas", "Operaciones", "Soporte", "Marketing"])
        mostrar_tabla = st.checkbox("Mostrar tabla de datos", value=True)
        
    with col_ctrl2:
        st.subheader(f"📊 Distribución para: {categoria}")
        np.random.seed(len(categoria))
        df_simulado = pd.DataFrame({
            "Muestra": [f"ID-{i+1:03d}" for i in range(n_puntos)],
            "Valor": np.random.normal(loc=100, scale=15, size=n_puntos).round(2),
            "Puntuación": np.random.uniform(1, 10, size=n_puntos).round(1)
        })
        st.area_chart(df_simulado["Valor"], use_container_width=True)
        
    if mostrar_tabla:
        st.subheader("📋 Datos Generados")
        st.dataframe(df_simulado, use_container_width=True)

# --- Vista 3: Acerca del Proyecto ---
else:
    st.markdown('<div class="main-title">ℹ️ Acerca de este Proyecto</div>', unsafe_allow_html=True)
    st.markdown("""
    Esta aplicación fue creada como punto de partida para proyectos desarrollados con **Streamlit** y Python.
    
    - **Streamlit**: Framework web interactivo.
    - **Pandas y NumPy**: Análisis y procesamiento de datos.
    - **Repositorio:** [samuelquito/Proyectos_streamlit](https://github.com/samuelquito/Proyectos_streamlit)
    """)

st.markdown("---")
st.markdown("<center style='color: gray; font-size: 0.85rem;'>Desarrollado con ❤️ por Samuel Quito | Streamlit Cloud</center>", unsafe_allow_html=True)
