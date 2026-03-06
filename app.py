import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io

# =========================================================
# CONFIGURACIÓN DE PÁGINA (ESTILO BRUTALISTA)
# =========================================================
st.set_page_config(
    page_title="DATALOGIX | Core",
    page_icon="⬛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE DISEÑO INSPIRADO EN MATTELSA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;700;900&display=swap');

    /* Reset y Variables */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #FFFFFF;
        color: #000000;
    }

    /* Tipografía Pesada (Headers) */
    h1, h2, h3 {
        font-family: 'Archivo Black', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: -1.5px;
        color: #000000;
    }

    /* Líneas separadoras industriales */
    hr {
        border: 0;
        border-top: 4px solid #000000;
        margin: 2rem 0;
    }

    /* Estilo de los Uploaders (Cajas sólidas) */
    [data-testid="stFileUploader"] {
        border: 3px solid #000000 !important;
        background-color: #F8F8F8 !important;
        padding: 1.5rem !important;
        border-radius: 0px !important;
        transition: 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        background-color: #000000 !important;
    }
    [data-testid="stFileUploader"]:hover * {
        color: #FFFFFF !important;
    }

    /* Botones Brutalistas */
    [data-testid="baseButton-secondary"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 0px !important;
        font-family: 'Archivo Black', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 1.5rem !important;
        font-size: 1.2rem !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    [data-testid="baseButton-secondary"]:hover {
        background-color: #FF3E00 !important; /* Acento Naranja Mattelsa */
        transform: translate(-4px, -4px);
        box-shadow: 4px 4px 0px 0px #000000;
    }

    /* Sidebar minimalista */
    [data-testid="stSidebar"] {
        background-color: #F4F4F4;
        border-right: 4px solid #000000;
    }

    /* Tarjetas de Métricas (HTML Custom) */
    .brutal-metric {
        border: 3px solid #000000;
        background-color: #FFFFFF;
        padding: 20px;
        text-align: left;
        margin-bottom: 20px;
        box-shadow: 6px 6px 0px 0px #000000;
    }
    .brutal-metric-title {
        font-size: 0.8rem;
        font-weight: 900;
        text-transform: uppercase;
        color: #666666;
        margin-bottom: 5px;
    }
    .brutal-metric-value {
        font-family: 'Archivo Black', sans-serif;
        font-size: 2.2rem;
        line-height: 1;
        color: #000000;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .brutal-metric-sub {
        font-size: 0.75rem;
        font-weight: 700;
        color: #FF3E00;
        margin-top: 5px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# MOTOR LÓGICO
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
    """Extrae datos vitales para mostrar antes de procesar"""
    try:
        df_preview = pd.read_excel(archivo, sheet_name="NUEVO")
        df_preview = normalizar_columnas(df_preview)
        
        impactos = len(df_preview)
        
        # Buscar el producto más repetido (manejando variaciones de nombre de columna)
        col_prod = "producto" if "producto" in df_preview.columns else None
        top_producto = df_preview[col_prod].value_counts().idxmax() if col_prod and not df_preview[col_prod].empty else "N/D"
        
        # Buscar el planeador más afectado
        col_plan = "pleaneador" if "pleaneador" in df_preview.columns else ("planeador" if "planeador" in df_preview.columns else None)
        top_planeador = df_preview[col_plan].value_counts().idxmax() if col_plan and not df_preview[col_plan].empty else "N/D"
        lineas_planeador = df_preview[col_plan].value_counts().max() if col_plan else 0
        
        return impactos, str(top_producto).title(), str(top_planeador).title(), lineas_planeador
    except Exception as e:
        return 0, "Error de lectura", "Error de lectura", 0

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
    if df is None or "Codigo" not in df.columns or "Nombres" not in df.columns: return {}
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().upper()
    df["Nombres"] = df["Nombres"].fillna("").astype(str).str.strip().upper()
    df["ID"] = str(num) + df["Codigo"]
    return df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).to_dict()

# =========================================================
# INTERFAZ DE USUARIO (EL LIENZO BRUTALISTA)
# =========================================================

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1>DATALOGIX</h1>", unsafe_allow_html=True)
    st.markdown("<b>v3.1 // CORE ENGINE</b>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### STATUS")
    st.markdown("🟢 ONLINE")
    st.markdown("### PROTOCOLO")
    st.write("1. INGESTA DE MAESTRO")
    st.write("2. LECTURA DE MÉTRICAS")
    st.write("3. MAPEO DE BODEGAS")
    st.write("4. EJECUCIÓN TOTAL")

# --- MAIN ---
st.markdown("<h1>CENTRO DE MANDO</h1>", unsafe_allow_html=True)
st.write("PROCESADOR DE FALTANTES / ALTO RENDIMIENTO")
st.markdown("<hr>", unsafe_allow_html=True)

# BLOQUE 1: INGESTA
st.markdown("<h3>01. INGESTA MAESTRA</h3>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("CARGAR INFORME PRINCIPAL (.XLSX)", type=["xlsx"])

# SI SE SUBE EL ARCHIVO -> MOSTRAR MÉTRICAS INMEDIATAMENTE
if archivo_principal is not None:
    # Mostramos un spinner técnico mientras lee
    with st.spinner("ANALIZANDO ESTRUCTURA..."):
        impactos, top_prod, top_plan, lineas_plan = extraer_metricas_rapidas(archivo_principal)
    
    st.markdown("<h3>📊 ANÁLISIS PRELIMINAR</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="brutal-metric">
            <div class="brutal-metric-title">TOTAL IMPACTOS (LÍNEAS)</div>
            <div class="brutal-metric-value">{impactos}</div>
            <div class="brutal-metric-sub">REGISTROS IDENTIFICADOS</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="brutal-metric">
            <div class="brutal-metric-title">PRODUCTO MÁS CRÍTICO</div>
            <div class="brutal-metric-value" style="font-size: 1.5rem;" title="{top_prod}">{top_prod[:20]}...</div>
            <div class="brutal-metric-sub">MAYOR FRECUENCIA</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="brutal-metric">
            <div class="brutal-metric-title">PLANEADOR MÁS IMPACTADO</div>
            <div class="brutal-metric-value" style="font-size: 1.5rem;">{top_plan[:15]}</div>
            <div class="brutal-metric-sub">{lineas_plan} LÍNEAS ASIGNADAS</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# BLOQUE 2: BODEGAS
st.markdown("<h3>02. MAPEO DE BODEGAS</h3>", unsafe_allow_html=True)
col_a, col_b = st.columns(2)
with col_a:
    b1 = st.file_uploader("BODEGA 1", type=["xlsx","xls","csv"])
    b7 = st.file_uploader("BODEGA 7", type=["xlsx","xls","csv"])
with col_b:
    b5 = st.file_uploader("BODEGA 5", type=["xlsx","xls","csv"])
    b6 = st.file_uploader("BODEGA 6", type=["xlsx","xls","csv"])

st.markdown("<hr>", unsafe_allow_html=True)

# BLOQUE 3: EJECUCIÓN
if st.button("INICIAR PROCESAMIENTO CORE"):
    if archivo_principal is None:
        st.error("ERROR FATAL: REQUIERE INFORME MAESTRO.")
    else:
        with st.status("EJECUTANDO ALGORITMOS...", expanded=True) as status:
            st.write(">> TRANSFORMANDO INFORME BASE...")
            df_final, df_hist = transformar_informe(archivo_principal)
            
            st.write(">> INDEXANDO BODEGAS...")
            dict_b1 = procesar_bodega(b1, 1)
            dict_b7 = procesar_bodega(b7, 7)
            dict_b5 = procesar_bodega(b5, 5)
            dict_b6 = procesar_bodega(b6, 6)
            
            st.write(">> CRUZANDO CUENTAS E HISTÓRICOS...")
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
            status.update(label="OPERACIÓN COMPLETADA", state="complete")

        # Generar Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
        output.seek(0)
        
        st.markdown("<h3>✅ PROCESO EXITOSO</h3>", unsafe_allow_html=True)
        
        st.download_button(
            label="DESCARGAR DATA CONSOLIDADA (.XLSX)",
            data=output,
            file_name="CONSOLIDADO_FALTANTES_PRO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
