import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io

# =========================================================
# CONFIGURACIÓN DE PÁGINA (ESTILO PREMIUM)
# =========================================================
st.set_page_config(
    page_title="DataLogix | Inteligencia Logística",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE DISEÑO ESTILO APPLE / AI MODERNA ---
st.markdown("""
    <style>
    /* Tipografía limpia y moderna (Inter imita el estilo San Francisco de Apple) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        background-color: #F5F5F7; /* Fondo sutilmente gris de Apple */
        color: #1D1D1F; /* Gris oscuro para menor fatiga visual */
    }

    /* Títulos con gradientes elegantes */
    .gradient-text {
        background: linear-gradient(135deg, #007AFF 0%, #34C759 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    .sub-title {
        color: #86868B;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 30px;
    }

    /* Efecto Glassmorphism para las tarjetas de métricas */
    .apple-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
        padding: 24px;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        height: 100%;
    }
    .apple-card:hover {
        box-shadow: 0 15px 35px rgba(0, 122, 255, 0.1);
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.9);
    }

    .metric-icon { font-size: 1.8rem; margin-bottom: 12px; }
    .metric-title { font-size: 0.85rem; color: #86868B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
    .metric-value { font-size: 2rem; font-weight: 700; color: #1D1D1F; margin: 8px 0; }
    .metric-sub { font-size: 0.8rem; color: #007AFF; font-weight: 500; }

    /* Contenedores de carga amigables */
    [data-testid="stFileUploader"] {
        border: 2px dashed #D2D2D7 !important;
        border-radius: 16px !important;
        background-color: #FFFFFF !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #007AFF !important;
        background-color: #F4F9FF !important;
    }

    /* Botones vibrantes y redondeados */
    [data-testid="baseButton-secondary"] {
        background: linear-gradient(180deg, #007AFF 0%, #0066CC 100%) !important;
        color: #FFFFFF !important;
        border-radius: 999px !important; /* Totalmente redondeado */
        border: none !important;
        padding: 16px 32px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(0, 122, 255, 0.3);
        width: 100%;
    }
    [data-testid="baseButton-secondary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0, 122, 255, 0.5);
    }

    /* Sidebar limpio */
    [data-testid="stSidebar"] {
        background-color: rgba(245, 245, 247, 0.8);
        backdrop-filter: blur(20px);
        border-right: 1px solid #E5E5EA;
    }
    
    .section-label {
        font-weight: 600;
        color: #1D1D1F;
        font-size: 1.2rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# MOTOR LÓGICO Y DE EXTRACCIÓN
# =========================================================

def normalizar_texto(texto):
    if not isinstance(texto, str): return texto
    texto = texto.strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^a-z0-9 ]', '', texto)
    return re.sub(r'\s+', ' ', texto).strip()

def normalizar_columnas(df):
    df.columns = [normalizar_texto(col) for col in df.columns]
    return df

def limpiar_valor(valor):
    if pd.isna(valor): return ""
    return str(valor).replace(".0", "").strip()

def crear_id(df, col_bodega, col_codigo):
    df[col_bodega] = df[col_bodega].apply(limpiar_valor)
    df[col_codigo] = df[col_codigo].apply(limpiar_valor)
    df["ID"] = df[col_bodega] + df[col_codigo]
    return df

def calcular_tipo_novedad(df, columna_fecha):
    texto_original = df[columna_fecha].astype(str).str.lower()
    df[columna_fecha] = pd.to_datetime(df[columna_fecha], dayfirst=True, errors="coerce")
    df["Tipo Novedad"] = np.nan
    df.loc[texto_original.str.contains("descontinuado", na=False), "Tipo Novedad"] = "Descontinuado"
    df.loc[df[columna_fecha] == pd.Timestamp("6000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("5000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("3000-01-01"), "Tipo Novedad"] = "Descontinuado"
    df.loc[(df[columna_fecha].notna() & df["Tipo Novedad"].isna()), "Tipo Novedad"] = "Agotado"
    return df

def leer_archivo(file):
    file.seek(0)
    ext = file.name.split('.')[-1]
    if ext == "xlsx": return pd.read_excel(file, engine="openpyxl")
    elif ext == "xls": return pd.read_excel(file)
    elif ext == "csv":
        for enc in ["utf-8", "latin1", "cp1252"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=enc)
            except: continue
    return None

def extraer_metricas_rapidas(archivo):
    """Extrae datos vitales premium para el panel de control"""
    try:
        df_preview = pd.read_excel(archivo, sheet_name="NUEVO")
        df_preview = normalizar_columnas(df_preview)
        
        impactos = len(df_preview)
        
        col_prod = "producto" if "producto" in df_preview.columns else None
        top_producto = df_preview[col_prod].value_counts().idxmax() if col_prod and not df_preview[col_prod].empty else "N/D"
        refs_unicas = df_preview[col_prod].nunique() if col_prod else 0
        
        col_plan = "pleaneador" if "pleaneador" in df_preview.columns else ("planeador" if "planeador" in df_preview.columns else None)
        top_planeador = df_preview[col_plan].value_counts().idxmax() if col_plan and not df_preview[col_plan].empty else "N/D"
        
        return impactos, refs_unicas, str(top_producto).title(), str(top_planeador).title()
    except Exception as e:
        return 0, 0, "Error", "Error"

def transformar_informe(archivo_excel):
    df_nuevo = pd.read_excel(archivo_excel, sheet_name="NUEVO")
    df_anterior = pd.read_excel(archivo_excel, sheet_name="ANTERIOR")
    
    df_nuevo = normalizar_columnas(df_nuevo)
    df_anterior = normalizar_columnas(df_anterior)
    df_nuevo = crear_id(df_nuevo, "bodega", "codigo")
    df_anterior = crear_id(df_anterior, "bod", "codigo")
    
    mapeo = {
        "prioritario": "PRIORITARIO", "bodega": "Bod", "codigo": "Codigo",
        "fecha novedad": "Fecha Novedad", "producto": "Producto",
        "generico": "Generico", "proveedor": "División", "pleaneador": "Planeador",
        "fechaentrega antigua": "Fecha Entrega Pedido", "num pedidos": "Numero Pedidos",
        "pendiente": "Pendiente", "traslado": "Traslados", "solicitud traslado": "Solicitud Traslados",
    }
    df_nuevo = df_nuevo.rename(columns=mapeo)
    df_nuevo = calcular_tipo_novedad(df_nuevo, "Fecha Novedad")
    
    if "cuenta" not in df_anterior.columns: df_anterior["cuenta"] = ""
    col_hist = ["ID", "abastecimiento", "dispensacion", "aliados", "responsable", "cuenta"]
    df_hist = df_anterior[[c for c in col_hist if c in df_anterior.columns]].copy()
    
    df_final = df_nuevo.merge(df_hist, on="ID", how="left")
    df_final["CUENTA"] = ""
    
    col_finales = [
        "ID","PRIORITARIO","Bod","Codigo","Fecha Novedad","Producto","Generico","División",
        "Planeador","Fecha Entrega Pedido","Numero Pedidos","Pendiente","Traslados",
        "Solicitud Traslados","Tipo Novedad","abastecimiento","dispensacion","aliados","CUENTA","responsable"
    ]
    for col in col_finales:
        if col not in df_final.columns: df_final[col] = ""
        
    return df_final[col_finales], df_hist

def procesar_bodega(file, num):
    if file is None: return {}
    df = leer_archivo(file)
    
    # --- MEJORA PRO: Normalización de columnas de bodega ---
    if df is not None:
        df = normalizar_columnas(df) # Esto convierte "Código" o "CODIGO" en "codigo"
        
        # Verificamos los nombres normalizados
        col_cod = "codigo" 
        col_nom = "nombres"
        
        if col_cod not in df.columns or col_nom not in df.columns:
            # Si no encuentra las columnas, intentamos buscarlas por aproximación
            # (Útil si el archivo de bodega cambia de formato)
            st.warning(f"⚠️ La Bodega {num} no tiene el formato estándar (Columnas esperadas: Codigo, Nombres)")
            return {}
            
        # Procesamiento ultra-seguro
        df[col_cod] = df[col_cod].astype(str).apply(limpiar_valor).str.strip().upper()
        df[col_nom] = df[col_nom].fillna("").astype(str).str.strip().upper()
        df["ID"] = str(num) + df[col_cod]
        
        return df.groupby("ID")[col_nom].apply(lambda x: ", ".join(sorted(set(x)))).to_dict()
    
    return {}

# --- DATO GANADOR EXTRA: Contador de Novedades ---
# (Agrégalo en la sección de extraer_metricas_rapidas)
def extraer_metricas_rapidas(archivo):
    try:
        df_preview = pd.read_excel(archivo, sheet_name="NUEVO")
        df_preview = normalizar_columnas(df_preview)
        
        impactos = len(df_preview)
        
        # Producto más crítico
        col_prod = "producto" if "producto" in df_preview.columns else None
        top_producto = df_preview[col_prod].value_counts().idxmax() if col_prod and not df_preview[col_prod].empty else "N/D"
        refs_unicas = df_preview[col_prod].nunique() if col_prod else 0
        
        # DATO GANADOR: Porcentaje de Agotados vs Otros
        df_preview = calcular_tipo_novedad(df_preview, "fecha novedad" if "fecha novedad" in df_preview.columns else "fecha_novedad")
        agotados_count = len(df_preview[df_preview["Tipo Novedad"] == "Agotado"])
        porcentaje_agotado = f"{(agotados_count / impactos * 100):.1f}%" if impactos > 0 else "0%"
        
        col_plan = "pleaneador" if "pleaneador" in df_preview.columns else ("planeador" if "planeador" in df_preview.columns else None)
        top_planeador = df_preview[col_plan].value_counts().idxmax() if col_plan and not df_preview[col_plan].empty else "N/D"
        
        return impactos, refs_unicas, str(top_producto).title(), porcentaje_agotado
    except:
        return 0, 0, "Error", "0%"

# =========================================================
# INTERFAZ DE USUARIO (EL LIENZO INSPIRADOR)
# =========================================================

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=60)
    st.markdown("<h2 style='font-weight:700; color:#1D1D1F; margin-top:10px;'>DataLogix</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#86868B;'>Versión 3.2 • Entorno Inteligente</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 💡 Tip Pro")
    st.info("Sube primero el informe principal. El sistema detectará automáticamente las métricas clave antes de que tengas que cruzar las bodegas.")

# --- MAIN ---
st.markdown("<div class='gradient-text'>Procesador de Faltantes</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Consolida, cruza y analiza la dispensación en segundos.</div>", unsafe_allow_html=True)

# BLOQUE 1: INGESTA MAESTRA
st.markdown("<div class='section-label'>📄 1. Informe Principal</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Arrastra tu reporte de faltantes (.xlsx)", type=["xlsx"])

# ANÁLISIS PRELIMINAR (MAGIA VISUAL)
if archivo_principal is not None:
    with st.spinner("Extrayendo insights inteligentes..."):
        impactos, refs_unicas, top_prod, top_plan = extraer_metricas_rapidas(archivo_principal)
    
    st.markdown("<div class='section-label'>✨ Análisis Preliminar</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="apple-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-title">Total Impactos</div>
            <div class="metric-value">{impactos}</div>
            <div class="metric-sub">Líneas de registro</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="apple-card">
            <div class="metric-icon">📦</div>
            <div class="metric-title">Ref. Únicas</div>
            <div class="metric-value">{refs_unicas}</div>
            <div class="metric-sub">Productos distintos</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="apple-card">
            <div class="metric-icon">⚠️</div>
            <div class="metric-title">Mayor Impacto</div>
            <div class="metric-value" style="font-size: 1.3rem; margin-top: 15px;" title="{top_prod}">{top_prod[:20]}...</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="apple-card">
            <div class="metric-icon">👤</div>
            <div class="metric-title">Planeador Top</div>
            <div class="metric-value" style="font-size: 1.5rem; margin-top: 12px;">{top_plan[:15]}</div>
        </div>
        """, unsafe_allow_html=True)

# BLOQUE 2: BODEGAS
st.markdown("<div class='section-label'>🏢 2. Red de Bodegas</div>", unsafe_allow_html=True)
st.markdown("<p style='color:#86868B; font-size:0.9rem;'>Carga los reportes satélites para iniciar el cruce de cuentas.</p>", unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    b1 = st.file_uploader("Bodega 1 (Central)", type=["xlsx","xls","csv"])
    b7 = st.file_uploader("Bodega 7 (Satélite)", type=["xlsx","xls","csv"])
with col_b:
    b5 = st.file_uploader("Bodega 5 (Especializada)", type=["xlsx","xls","csv"])
    b6 = st.file_uploader("Bodega 6 (Regional)", type=["xlsx","xls","csv"])

st.markdown("<br><br>", unsafe_allow_html=True)

# BLOQUE 3: EJECUCIÓN
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("Generar Consolidado Inteligente"):
        if archivo_principal is None:
            st.error("Por favor, sube el informe principal para continuar.")
        else:
            with st.status("Procesando datos con el motor heurístico...", expanded=True) as status:
                st.write("Estructurando y limpiando datos base...")
                df_final, df_hist = transformar_informe(archivo_principal)
                
                st.write("Mapeando y cruzando inventarios de bodegas...")
                dict_b1 = procesar_bodega(b1, 1)
                dict_b7 = procesar_bodega(b7, 7)
                dict_b5 = procesar_bodega(b5, 5)
                dict_b6 = procesar_bodega(b6, 6)
                
                st.write("Asignando cuentas e históricos...")
                hist_dict = dict(zip(df_hist["ID"], df_hist["cuenta"]))
                
                for i, row in df_final.iterrows():
                    bod = int(row["Bod"])
                    id_val = str(bod) + str(row["Codigo"]).strip().upper()
                    cuenta = ""
                    
                    if bod == 21: cuenta = "EPM"
                    elif bod == 19: cuenta = "UDEA"
                    elif bod == 16: cuenta = "HMUA"
                    elif bod == 1: cuenta = dict_b1.get(id_val, "")
                    elif bod == 7: cuenta = dict_b7.get(id_val, "")
                    elif bod == 5: cuenta = dict_b5.get(id_val, "")
                    elif bod == 6: cuenta = dict_b6.get(id_val, "")
                    
                    if not cuenta: cuenta = hist_dict.get(id_val, "")
                    df_final.at[i, "CUENTA"] = cuenta

                df_final = df_final.drop_duplicates()
                status.update(label="Procesamiento completado con éxito", state="complete")

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            output.seek(0)
            
            st.balloons()
            st.markdown("<h3 style='text-align:center; color:#34C759; margin-top:20px;'>¡Reporte Listo!</h3>", unsafe_allow_html=True)
            
            st.download_button(
                label="Descargar Reporte Final (.xlsx)",
                data=output,
                file_name="DataLogix_Consolidado_Pro.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
