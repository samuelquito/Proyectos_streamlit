"""MVP Radar de Precios - Mercado Libre Perú.

Aplicación de análisis transversal de precios y detección de oportunidades
reales sobre muestras de Mercado Libre Perú, ignorando los precios tachados
del frontend y evaluando el descuento contra la mediana de mercado.
"""

from typing import Optional
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
import streamlit as st


# ==============================================================================
# CONFIGURACIÓN GENERAL Y CONSTANTES DE RED
# ==============================================================================
BASE_URL: str = "https://listado.mercadolibre.com.pe/"
DEFAULT_HEADERS: dict[str, str] = {
    # User-Agent moderno Chrome/Windows con compatibilidad de rastreo para evitar bloqueos por WAF CloudFront/Tengine
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36 "
        "(compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-PE,es-419;q=0.9,es;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}
REQUEST_TIMEOUT: int = 15


# ==============================================================================
# MÓDULO 1 Y 2: EXTRACCIÓN Y PERSISTENCIA EN MEMORIA
# ==============================================================================
@st.cache_data(ttl=300)
def fetch_meli_data(query: str) -> pd.DataFrame:
    """Extrae productos de Mercado Libre Perú mediante scraping HTTP directo.

    Realiza una solicitud HTTP GET con headers de navegador moderno y analiza el
    HTML resultante con BeautifulSoup para extraer títulos, precios actuales (sin
    precios tachados ni cuotas) y enlaces de productos.

    Args:
        query: Término de búsqueda introducido por el usuario.

    Returns:
        pd.DataFrame con columnas:
            - 'Título' (str): Nombre del producto publicado.
            - 'Precio_Actual' (float): Precio actual de venta en Soles (S/).
            - 'URL' (str): Enlace directo a la publicación.
    """
    clean_query = query.strip()
    if not clean_query:
        return pd.DataFrame(columns=["Título", "Precio_Actual", "URL"])

    # Normalización del endpoint: reemplazo de espacios consecutivos por guiones
    formatted_slug = re.sub(r"\s+", "-", clean_query)
    encoded_slug = urllib.parse.quote(formatted_slug, safe="-")
    target_url = f"{BASE_URL}{encoded_slug}"

    try:
        response = requests.get(target_url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            return pd.DataFrame(columns=["Título", "Precio_Actual", "URL"])
    except requests.RequestException:
        return pd.DataFrame(columns=["Título", "Precio_Actual", "URL"])

    soup = BeautifulSoup(response.text, "html.parser")

    # Localización de nodos de productos en el grid de resultados
    raw_nodes = soup.select(".ui-search-layout__item, .ui-search-result__wrapper, .poly-card")

    # Deduplicar nodos jerárquicos anidados (preservar los contenedores principales)
    item_nodes: list[Tag] = []
    seen_ids: set[int] = set()
    for node in raw_nodes:
        if not isinstance(node, Tag):
            continue
        node_id = id(node)
        if node_id not in seen_ids:
            seen_ids.add(node_id)
            if not any(node in parent.descendants for parent in item_nodes):
                item_nodes.append(node)

    records: list[dict[str, object]] = []

    for node in item_nodes:
        try:
            # 1. Extracción de Título
            title_elem = node.select_one(
                ".ui-search-item__title, .poly-component__title, .poly-component__title-wrapper, h2, h3"
            )
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            if not title or len(title) < 2:
                continue

            # 2. Extracción de URL del producto
            link_elem = node.select_one("a[href]")
            if not link_elem:
                continue

            href = str(link_elem["href"]).strip()
            if not href:
                continue

            if href.startswith("/"):
                product_url = f"https://www.mercadolibre.com.pe{href}"
            else:
                product_url = href

            # 3. Extracción de Precio Actual
            # Priorizamos el contenedor de precio actual para evitar precios tachados (andes-money-amount--previous)
            # o cuotas (installments).
            price_container = node.select_one(".poly-price__current, .ui-search-price__second-line")
            if not price_container:
                price_container = node.select_one(
                    ".andes-money-amount:not(.andes-money-amount--previous)"
                )

            if not price_container:
                continue

            fraction_elem = price_container.select_one(".andes-money-amount__fraction")
            if not fraction_elem:
                continue

            raw_fraction = fraction_elem.get_text(strip=True)
            cents_elem = price_container.select_one(".andes-money-amount__cents")
            raw_cents = cents_elem.get_text(strip=True) if cents_elem else "00"

            # Limpieza de caracteres S/, $, comas y puntos separadores de miles
            clean_fraction = (
                raw_fraction.replace("S/", "")
                .replace("$", "")
                .replace(".", "")
                .replace(",", "")
                .strip()
            )
            clean_cents = re.sub(r"\D", "", raw_cents.strip()) or "00"

            if not clean_fraction.isdigit():
                continue

            price_float = float(f"{clean_fraction}.{clean_cents}")
            if price_float <= 0.0:
                continue

            records.append({
                "Título": title,
                "Precio_Actual": price_float,
                "URL": product_url,
            })
        except Exception:
            # Resiliencia: omitir elementos anómalos o anuncios patrocinados sin precio legible
            continue

    if not records:
        return pd.DataFrame(columns=["Título", "Precio_Actual", "URL"])

    return pd.DataFrame(records)


# ==============================================================================
# MÓDULO 3: LÓGICA ANALÍTICA CROSS-SECTIONAL
# ==============================================================================
def process_discount_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula métricas de descuento real respecto a la mediana del mercado.

    Añade columnas de varianza absoluta contra la mediana, porcentaje de
    descuento real y clasificación dicotómica entre Oportunidad y
    Sobreprecio / Inflado.

    Args:
        df: DataFrame original que contiene al menos la columna 'Precio_Actual'.

    Returns:
        pd.DataFrame con las columnas adicionales:
            - 'Varianza_vs_Mediana_S/': Diferencia aritmética (Precio_Actual - mediana_mercado).
            - 'Descuento_Real_%': Porcentaje de descuento relativo a la mediana.
            - 'Clasificación': 'Oportunidad' si Precio_Actual < mediana, sino 'Sobreprecio / Inflado'.
    """
    if df.empty or "Precio_Actual" not in df.columns:
        res = df.copy()
        res["Varianza_vs_Mediana_S/"] = pd.Series(dtype=float)
        res["Descuento_Real_%"] = pd.Series(dtype=float)
        res["Clasificación"] = pd.Series(dtype=str)
        return res

    processed_df = df.copy()

    # Cálculo de la mediana global de los precios extraídos
    mediana_mercado = float(processed_df["Precio_Actual"].median())

    # Varianza aritmética vs mediana: Precio_Actual - mediana_mercado
    processed_df["Varianza_vs_Mediana_S/"] = (
        processed_df["Precio_Actual"] - mediana_mercado
    ).round(2)

    # Descuento real porcentual: ((mediana_mercado - Precio_Actual) / mediana_mercado) * 100
    if mediana_mercado > 0:
        processed_df["Descuento_Real_%"] = (
            ((mediana_mercado - processed_df["Precio_Actual"]) / mediana_mercado) * 100.0
        ).round(2)
    else:
        processed_df["Descuento_Real_%"] = 0.0

    # Clasificación: 'Oportunidad' si Precio_Actual < mediana_mercado, sino 'Sobreprecio / Inflado'
    processed_df["Clasificación"] = processed_df["Precio_Actual"].apply(
        lambda precio: "Oportunidad" if precio < mediana_mercado else "Sobreprecio / Inflado"
    )

    return processed_df


# ==============================================================================
# MÓDULO 4: UI Y DASHBOARD (STREAMLIT)
# ==============================================================================
def main() -> None:
    """Punto de entrada principal para el dashboard de Radar de Precios en Streamlit."""
    st.set_page_config(
        page_title="Radar de Precios - Mercado Libre Perú",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("🎯 Radar de Precios - Mercado Libre Perú")
    st.markdown(
        "Identifica **descuentos reales** calculados sobre una muestra transversal del mercado, "
        "ignorando los precios tachados ficticios del frontend."
    )

    # Componentes de entrada
    col_input, col_btn = st.columns([4, 1], vertical_alignment="bottom")
    with col_input:
        query_input = st.text_input(
            label="Término de búsqueda",
            value="audifonos bluetooth",
            placeholder="Ej: laptop gamer, teclado mecanico, monitor 144hz, iphone 13...",
            help="Ingresa el producto a escanear en Mercado Libre Perú.",
        )
    with col_btn:
        scan_button = st.button("Escanear Mercado", type="primary", use_container_width=True)

    # Manejo de estado de consulta en session_state
    if "active_query" not in st.session_state:
        st.session_state.active_query = "audifonos bluetooth"

    if scan_button and query_input.strip():
        st.session_state.active_query = query_input.strip()

    current_query: str = st.session_state.active_query

    if not current_query:
        st.info("💡 Ingresa un producto y haz clic en **Escanear Mercado** para iniciar el análisis.")
        return

    with st.spinner(f"Escaneando y analizando datos en vivo para: '{current_query}'..."):
        raw_df = fetch_meli_data(current_query)

    if raw_df.empty:
        st.warning(
            f"No se pudieron encontrar productos o extraer precios legibles para '{current_query}'. "
            "Por favor, intenta con otro término de búsqueda."
        )
        return

    # Procesamiento analítico
    df_metrics = process_discount_metrics(raw_df)

    # Ordenamiento predeterminado por Descuento_Real_% de mayor a menor
    df_sorted = df_metrics.sort_values(by="Descuento_Real_%", ascending=False).reset_index(drop=True)

    # Métricas rápidas
    mediana = float(df_sorted["Precio_Actual"].median())
    precio_min = float(df_sorted["Precio_Actual"].min())
    total_oportunidades = int((df_sorted["Clasificación"] == "Oportunidad").sum())
    total_productos = len(df_sorted)

    st.markdown("---")
    st.subheader("📊 Métricas Rápidas del Mercado")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="Mediana del Mercado",
            value=f"S/ {mediana:,.2f}",
            help="Mediana global de la muestra. Punto de referencia insensible a valores atípicos.",
        )
    with m2:
        ahorro_max = ((mediana - precio_min) / mediana * 100) if mediana > 0 else 0
        st.metric(
            label="Precio Más Bajo Encontrado",
            value=f"S/ {precio_min:,.2f}",
            delta=f"{ahorro_max:.1f}% vs mediana" if ahorro_max > 0 else None,
            delta_color="normal",
        )
    with m3:
        st.metric(
            label="Total de Oportunidades",
            value=f"{total_oportunidades}",
            help="Cantidad de registros con Precio_Actual estrictamente inferior a la mediana.",
        )
    with m4:
        pct_oportunidades = (total_oportunidades / total_productos) * 100 if total_productos > 0 else 0
        st.metric(
            label="Muestra Analizada",
            value=f"{total_productos} productos",
            delta=f"{pct_oportunidades:.1f}% oportunidades",
            delta_color="off",
        )

    st.markdown("---")

    # Dispersión Visual: Precio vs Índice para detectar outliers
    st.subheader("📈 Dispersión Visual de Precios (Detección de Outliers)")
    st.caption("Visualización de la distribución de precios en la muestra: Precio vs Índice de producto.")

    df_chart = df_sorted.copy()
    df_chart["Índice"] = range(1, len(df_chart) + 1)

    st.scatter_chart(
        data=df_chart,
        x="Índice",
        y="Precio_Actual",
        color="Clasificación",
        use_container_width=True,
    )

    # Tabla de Datos Interactiva
    st.subheader("📋 Muestra Transversal de Precios")
    st.caption("Haz clic en cualquier encabezado para ordenar interactivamente la tabla (ej. por Descuento Real %).")

    st.dataframe(
        df_sorted,
        column_config={
            "Título": st.column_config.TextColumn(
                label="Título",
                width="large",
            ),
            "Precio_Actual": st.column_config.NumberColumn(
                label="Precio Actual",
                format="S/ %.2f",
            ),
            "Varianza_vs_Mediana_S/": st.column_config.NumberColumn(
                label="Varianza vs Mediana (S/)",
                format="S/ %.2f",
                help="Varianza aritmética respecto a la mediana (Precio_Actual - mediana).",
            ),
            "Descuento_Real_%": st.column_config.NumberColumn(
                label="Descuento Real %",
                format="%.2f %%",
                help="Descuento real calculado contra la mediana transversal.",
            ),
            "Clasificación": st.column_config.TextColumn(
                label="Clasificación",
            ),
            "URL": st.column_config.LinkColumn(
                label="URL del Producto",
                display_text="Ver en Mercado Libre ↗",
                width="medium",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# PUNTO DE ENTRADA ESTÁNDAR
# ==============================================================================
if __name__ == "__main__":
    main()
