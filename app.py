import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import time
from streamlit_lottie import st_lottie
import requests

# Configuración de página con estilo moderno
st.set_page_config(
    page_title="DataFlow | Procesador de Faltantes",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- FUNCIÓN PARA CARGAR ANIMACIONES ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_upload = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_v7bx9pva.json") # Animación de carga
lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_5tkzkblw.json") # Animación éxito

# --- CSS PERSONALIZADO (EL "MÁGICO") ---
st.markdown("""
    <style>
    /* Fondo y fuente */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Estilo de los contenedores de carga */
    .stFileUploader {
        border: 2px dashed #4F46E5;
        border-radius: 15px;
        padding: 20px;
        background-color: #f8fafc;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #818CF8;
        background-color: #eff6ff;
        transform: translateY(-2px);
    }

    /* Botón principal estilo Glassmorphism */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white !important;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6);
    }

    /* Títulos animados */
    .main-title {
        background: -webkit-linear-gradient(#4F46E5, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
    }
    
    .sub-text {
        color: #64748b;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Card de éxito */
    .success-card {
        padding: 20px;
        border-radius: 15px;
        background-color: #f0fdf4;
        border-left: 5px solid #22c55e;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LÓGICA DE PROCESAMIENTO (TU CÓDIGO ORIGINAL)
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
    if file.name.endswith(".xlsx"): return pd.read_excel(file, engine="openpyxl")
    elif file.name.endswith(".xls"): return pd.read_excel(file)
    elif file.name.endswith(".csv"):
        for encoding in ["utf-8", "latin1", "cp1252"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=encoding)
            except: continue
    raise ValueError("Formato no soportado.")

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
    columnas_hist = ["ID", "abastecimiento", "dispensacion", "aliados", "responsable", "cuenta"]
    df_hist = df_anterior[columnas_hist].copy()
    
    df_final = df_nuevo.merge(df_hist, on="ID", how="left")
    df_final["CUENTA"] = ""
    columnas_finales = [
        "ID","PRIORITARIO","Bod","Codigo","Fecha Novedad","Producto","Generico","División",
        "Planeador","Fecha Entrega Pedido","Numero Pedidos","Pendiente","Traslados",
        "Solicitud Traslados","Tipo Novedad","abastecimiento","dispensacion","aliados","CUENTA","responsable"
    ]
    return df_final[columnas_finales], df_hist

def procesar_bodega(file, numero_bodega):
    if file is None: return {}
    df = leer_archivo(file)
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().upper()
    df["Nombres"] = df["Nombres"].apply(lambda x: str(x).strip().upper() if pd.notna(x) else "")
    df["ID"] = str(numero_bodega) + df["Codigo"]
    consolidado = df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
    return dict(zip(consolidado["ID"], consolidado["Nombres"]))

def asignar_cuenta(df_final, df_hist, dict_b1, dict_b7, dict_b5, dict_b6):
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
    return df_final

# =========================================================
# INTERFAZ DE USUARIO (EL NUEVO LOOK)
# =========================================================

st.markdown('<p class="main-title">DataFlow Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Inteligencia de Datos para Gestión de Dispensación</p>', unsafe_allow_html=True)

# Layout de columnas para organizar el espacio
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📄 Informe Base")
    archivo_principal = st.file_uploader("Arrastra aquí el reporte principal (.xlsx)", type=["xlsx"], key="main")
    if lottie_upload:
        st_lottie(lottie_upload, height=150, key="anim_upload")

with col2:
    st.markdown("### 📦 Pedidos de Bodegas")
    # Usamos pestañas para limpiar la UI
    tab1, tab2, tab3, tab4 = st.tabs(["Bodega 1", "Bodega 7", "Bodega 5", "Bodega 6"])
    with tab1: b1 = st.file_uploader("Cargar B1", type=["xlsx","xls","csv"], key="b1")
    with tab2: b7 = st.file_uploader("Cargar B7", type=["xlsx","xls","csv"], key="b7")
    with tab3: b5 = st.file_uploader("Cargar B5", type=["xlsx","xls","csv"], key="b5")
    with tab4: b6 = st.file_uploader("Cargar B6", type=["xlsx","xls","csv"], key="b6")

st.markdown("---")

# Botón de Procesar centrado
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("🚀 PROCESAR Y GENERAR INFORME"):
        if archivo_principal is None:
            st.error("⚠️ Por favor, sube el informe principal antes de continuar.")
        else:
            with st.spinner('Analizando datos y cruzando cuentas...'):
                # Simular un poco de tiempo para la experiencia de usuario
                time.sleep(1)
                
                df_final, df_hist = transformar_informe(archivo_principal)
                dict_b1 = procesar_bodega(b1, 1)
                dict_b7 = procesar_bodega(b7, 7)
                dict_b5 = procesar_bodega(b5, 5)
                dict_b6 = procesar_bodega(b6, 6)
                
                df_final = asignar_cuenta(df_final, df_hist, dict_b1, dict_b7, dict_b5, dict_b6)
                df_final = df_final.drop_duplicates()
                
                # Preparar descarga
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                output.seek(0)
                
                # Mostrar éxito
                st.balloons()
                st.markdown("""
                    <div class="success-card">
                        <h3>✅ ¡Proceso Exitoso!</h3>
                        <p>Se han consolidado todas las cuentas y novedades correctamente.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.download_button(
                    label="📥 DESCARGAR RESULTADO FINAL",
                    data=output,
                    file_name="INFORME_CONSOLIDADO_PRO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
