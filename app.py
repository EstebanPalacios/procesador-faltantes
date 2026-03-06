import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io

# =========================================================
# CONFIGURACIÓN DE PÁGINA (ESTILO PREMIUM APPLE)
# =========================================================
st.set_page_config(
    page_title="DataLogix | Inteligencia Logística",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE DISEÑO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        background-color: #F5F5F7;
        color: #1D1D1F;
    }

    .gradient-text {
        background: linear-gradient(135deg, #007AFF 0%, #34C759 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem;
        letter-spacing: -1px;
    }

    .apple-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
        padding: 20px;
        transition: all 0.3s ease;
    }

    .metric-title { font-size: 0.75rem; color: #86868B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #1D1D1F; margin-top: 5px; }

    /* Estilo del botón de descarga */
    .stDownloadButton > button {
        background: linear-gradient(180deg, #34C759 0%, #28A745 100%) !important;
        color: white !important;
        border-radius: 999px !important;
        padding: 10px 30px !important;
        border: none !important;
        font-weight: 600 !important;
    }

    .section-label {
        font-weight: 600;
        font-size: 1.1rem;
        margin: 1.5rem 0 1rem 0;
        color: #1D1D1F;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# FUNCIONES DE LÓGICA (TU LÓGICA REFORZADA)
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

def limpiar_texto_simple(texto):
    if pd.isna(texto): return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in texto if not unicodedata.combining(c))

def crear_id(df, col_bodega, col_codigo):
    df[col_bodega] = df[col_bodega].apply(limpiar_valor)
    df[col_codigo] = df[col_codigo].apply(limpiar_valor)
    df["ID"] = df[col_bodega] + df[col_codigo]
    return df

def calcular_tipo_novedad(df, columna_fecha):
    df[columna_fecha] = pd.to_datetime(df[columna_fecha], dayfirst=True, errors="coerce")
    df["Tipo Novedad"] = np.nan
    df.loc[df[columna_fecha] == pd.Timestamp("6000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("5000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("3000-01-01"), "Tipo Novedad"] = "Descontinuado"
    df.loc[(df[columna_fecha].notna() & df["Tipo Novedad"].isna()), "Tipo Novedad"] = "Agotado"
    return df

def leer_archivo(file):
    file.seek(0)
    ext = file.name.split('.')[-1].lower()
    if ext == "xlsx": return pd.read_excel(file, engine="openpyxl")
    elif ext == "xls": return pd.read_excel(file)
    elif ext == "csv":
        for enc in ["utf-8", "latin1", "cp1252"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=enc)
            except: continue
    return None

def transformar_informe(archivo_excel):
    df_nuevo = pd.read_excel(archivo_excel, sheet_name="NUEVO")
    df_anterior = pd.read_excel(archivo_excel, sheet_name="ANTERIOR")
    
    df_nuevo = normalizar_columnas(df_nuevo)
    df_anterior = normalizar_columnas(df_anterior)
    
    # Mapeo basado en tus nombres normalizados
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
    for c in col_finales:
        if c not in df_final.columns: df_final[c] = ""
        
    return df_final[col_finales], df_hist

def procesar_bodega(file, num):
    if file is None: return {}
    df = leer_archivo(file)
    if df is None: return {}
    
    # Buscamos las columnas sin importar si dicen "Codigo", "CODIGO" o "codigo"
    df.columns = [str(c).strip().title() for c in df.columns]
    
    if "Codigo" not in df.columns or "Nombres" not in df.columns:
        st.warning(f"⚠️ La Bodega {num} no tiene columnas 'Codigo' y 'Nombres'.")
        return {}

    # AQUÍ ESTABA EL ERROR: Se agregó .str antes de .upper()
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().str.upper()
    df["Nombres"] = df["Nombres"].apply(limpiar_texto_simple)
    df["ID"] = str(num) + df["Codigo"]
    
    consolidado = df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
    return dict(zip(consolidado["ID"], consolidado["Nombres"]))

# =========================================================
# INTERFAZ DE USUARIO
# =========================================================

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=50)
    st.markdown("### DataLogix Pro")
    st.caption("v3.5 | Clean Design")
    st.markdown("---")
    st.info("💡 Tip: El sistema cruza automáticamente los datos del informe anterior para recuperar cuentas históricas.")

st.markdown("<div class='gradient-text'>Logística de Faltantes</div>", unsafe_allow_html=True)

# BLOQUE 1
st.markdown("<div class='section-label'>1️⃣ Informe Maestro (Pestañas NUEVO / ANTERIOR)</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Subir archivo Excel principal", type=["xlsx"])

# DATO GANADOR: ANÁLISIS RÁPIDO
if archivo_principal:
    try:
        df_p = pd.read_excel(archivo_principal, sheet_name="NUEVO")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="apple-card"><div class="metric-title">Faltantes Totales</div><div class="metric-value">{len(df_p):,}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="apple-card"><div class="metric-title">Estado Archivo</div><div class="metric-value" style="color:#007AFF;">Cargado ✓</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="apple-card"><div class="metric-title">Acción</div><div class="metric-value" style="font-size:1rem; padding-top:10px;">Listo para procesar</div></div>', unsafe_allow_html=True)
    except:
        st.error("❌ El archivo no tiene la pestaña 'NUEVO'.")

# BLOQUE 2
st.markdown("<div class='section-label'>2️⃣ Cruce de Bodegas (Opcional)</div>", unsafe_allow_html=True)
c_a, c_b = st.columns(2)
with c_a:
    b1 = st.file_uploader("Bodega 1", type=["xlsx","xls","csv"])
    b7 = st.file_uploader("Bodega 7", type=["xlsx","xls","csv"])
with c_b:
    b5 = st.file_uploader("Bodega 5", type=["xlsx","xls","csv"])
    b6 = st.file_uploader("Bodega 6", type=["xlsx","xls","csv"])

# PROCESAMIENTO
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 INICIAR PROCESAMIENTO INTELIGENTE", use_container_width=True):
    if not archivo_principal:
        st.error("Falta el informe principal.")
    else:
        with st.spinner("Procesando..."):
            df_final, df_hist = transformar_informe(archivo_principal)
            
            # Procesar diccionarios
            d1 = procesar_bodega(b1, 1)
            d7 = procesar_bodega(b7, 7)
            d5 = procesar_bodega(b5, 5)
            d6 = procesar_bodega(b6, 6)
            
            hist_dict = dict(zip(df_hist["ID"], df_hist["cuenta"]))
            
            # Asignación
            for i, row in df_final.iterrows():
                bod = int(row["Bod"])
                cod = str(limpiar_valor(row["Codigo"])).strip().upper()
                id_val = str(bod) + cod
                cuenta = ""
                
                if bod == 21: cuenta = "EPM"
                elif bod == 19: cuenta = "UDEA"
                elif bod == 16: cuenta = "HMUA"
                elif bod == 1: cuenta = d1.get(id_val, "")
                elif bod == 7: cuenta = d7.get(id_val, "")
                elif bod == 5: cuenta = d5.get(id_val, "")
                elif bod == 6: cuenta = d6.get(id_val, "")
                
                if not cuenta or cuenta == "":
                    cuenta = hist_dict.get(id_val, "")
                
                df_final.at[i, "CUENTA"] = cuenta

            df_final = df_final.drop_duplicates()
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.success("✅ ¡Análisis completado!")
            st.download_button(
                label="📥 Descargar Reporte Consolidado",
                data=output.getvalue(),
                file_name="Reporte_Final_DataLogix.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
