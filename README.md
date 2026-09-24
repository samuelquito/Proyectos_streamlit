# 🎯 Radar de Precios - Mercado Libre Perú (MVP)

Aplicación analítica desarrollada con **Streamlit** y **Python** para identificar **descuentos reales** en Mercado Libre Perú a partir de una muestra transversal de datos en vivo, omitiendo los precios tachados ficticios del frontend y contrastando cada publicación contra la **mediana estadística del mercado**.

---

## 📋 Requisitos Previos

- **Sistema Operativo**: Windows 10/11 (o Linux / macOS).
- **Python**: Versión 3.10 o superior (verificado con Python 3.13 en el entorno).

---

## 🚀 Guía de Inicio Rápido (Paso a Paso)

### Paso 1: Abrir la Terminal en la Carpeta del Proyecto

Abre PowerShell o el Símbolo del sistema (CMD) en la carpeta del proyecto:

```powershell
cd "c:\Users\PcBan\Desktop\Radar de Precios"
```

### Paso 2: Instalar Dependencias Requeridas

Instala las bibliotecas autorizadas ejecutando:

```powershell
py -m pip install streamlit pandas requests beautifulsoup4
```

> **Nota:** Si usas un comando `python` estándar en lugar del launcher `py`, puedes ejecutar:
> ```bash
> python -m pip install streamlit pandas requests beautifulsoup4
> ```

### Paso 3: Ejecutar la Aplicación

Inicia el servidor local de Streamlit con el siguiente comando:

```powershell
py -m streamlit run app.py
```

Streamlit iniciará el servidor local y abrirá automáticamente tu navegador web predeterminado en:
```
http://localhost:8501
```

---

## 🖥️ Cómo Utilizar la Herramienta

1. **Ingresar Término de Búsqueda**:
   - En el campo de texto superior, escribe el producto que deseas auditar (por ejemplo: `audifonos bluetooth`, `laptop gamer`, `teclado mecanico`, `monitor 144hz`, `silla gamer`).
2. **Escanear Mercado**:
   - Haz clic en el botón azul **"Escanear Mercado"**.
   - El sistema realizará una petición HTTP directa con headers optimizados contra el WAF de Mercado Libre y extraerá la muestra en vivo.
3. **Analizar las Métricas Rápidas**:
   - **Mediana del Mercado**: El precio central real de la muestra, inmune a valores inflados o publicaciones atípicas.
   - **Precio Más Bajo Encontrado**: El menor precio detectado y su porcentaje de ahorro respecto a la mediana.
   - **Total de Oportunidades**: Cantidad de productos cuyo precio de venta está estrictamente por debajo de la mediana del mercado.
4. **Inspeccionar la Dispersión Visual**:
   - Revisa el gráfico **Precio vs Índice** para detectar visualmente anomalías de precios, ofertas extremas y productos sobrevalorados.
5. **Explorar y Filtrar en la Tabla**:
   - La tabla viene pre-ordenada por la columna **Descuento Real %** de mayor a menor.
   - Puedes hacer clic en cualquier encabezado de columna para reordenar los resultados según tu interés.
   - Haz clic en **"Ver en Mercado Libre ↗"** para acceder directamente a la publicación oficial.

---

## 🏗️ Arquitectura y Funcionamiento Interno

El proyecto se concentra en un único archivo modular [`app.py`](app.py):

| Módulo | Función / Componente | Descripción Técnica |
| :--- | :--- | :--- |
| **Módulo 1: Extracción** | `fetch_meli_data(query)` | Scraping HTTP directo mediante `requests.get` y `BeautifulSoup`. Descarta precios tachados (`.andes-money-amount--previous`) y cuotas bancarias para capturar exclusivamente el precio de venta actual en Soles (S/). |
| **Módulo 2: Caché** | `@st.cache_data(ttl=300)` | Persistencia en memoria durante 5 minutos para evitar saturación de peticiones y bloqueos de IP, manteniendo la fluidez de la interfaz. |
| **Módulo 3: Analítica** | `process_discount_metrics(df)` | Cálculo de la mediana de mercado, varianza aritmética (`Precio_Actual - Mediana`), descuento real porcentual y etiquetado dicotómico (`Oportunidad` vs `Sobreprecio / Inflado`). |
| **Módulo 4: UI / Dashboard** | `main()` | Renderizado interactivo con métricas en columnas, gráfico `st.scatter_chart` y tabla de datos configurable con enlaces directos. |

---

## ❓ Preguntas Frecuentes y Solución de Problemas

- **¿Por qué la tabla muestra 0 productos para una búsqueda?**
  Verifica que el término de búsqueda no contenga caracteres especiales inválidos y que cuente con publicaciones activas en Mercado Libre Perú (`mercadolibre.com.pe`).
- **¿Cómo detener la aplicación?**
  En la terminal donde ejecutaste `streamlit run`, presiona `Ctrl + C`.
