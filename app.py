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

# --- SISTEMA DE DISEÑO ESTILO APPLE / MODERN UI ---
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
        font-size: 2.8rem;
        letter-spacing: -1px;
    }

    .apple-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 22px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
        padding: 24px;
        transition: transform 0.3s ease;
        height: 100%;
    }
    
    .apple-card:hover {
        transform: translateY(-5px);
    }

    .metric-title { font-size: 0.8rem; color: #86868B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #1D1D1F; margin-top: 8px; }

    [data-testid="stFileUploader"] {
        border: 2px dashed #D2D2D7 !important;
        border-radius: 16px !important;
        padding: 1rem !important;
    }

    [data-testid="baseButton-secondary"] {
        background: linear-gradient(180deg, #007AFF 0%, #0066CC 100%) !important;
        color: white !important;
        border-radius: 999px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        width: 100%;
        border: none !important;
    }

    .section-label {
        font-weight: 600;
        font-size: 1.2rem;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LÓGICA EXACTA DE TU CÓDIGO (NO TOCAR FUNCIONALIDAD)
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

def limpiar_texto(texto):
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
    if file.name.endswith(".xlsx"): return pd.read_excel(file, engine="openpyxl")
    elif file.name.endswith(".xls"): return pd.read_excel(file)
    elif file.name.endswith(".csv"):
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
    df_hist = df_anterior[col_hist].copy()
    
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
    # Aquí usamos las columnas exactas: "Codigo" y "Nombres"
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().upper()
    df["Nombres"] = df["Nombres"].apply(limpiar_texto)
    df["ID"] = str(numero_bodega) + df["Codigo"]
    consolidado = df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
    return dict(zip(consolidado["ID"], consolidado["Nombres"]))

# =========================================================
# INTERFAZ DE USUARIO (EL "TRAJE" DE APPLE)
# =========================================================

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=60)
    st.markdown("## DataLogix Pro")
    st.markdown("---")
    st.info("💡 Sube el informe principal para ver el análisis de impacto instantáneo.")

# --- MAIN ---
st.markdown("<div class='gradient-text'>Procesador de Faltantes</div>", unsafe_allow_html=True)
st.markdown("<p style='color:#86868B; margin-bottom:2rem;'>Herramienta de consolidación logística inteligente.</p>", unsafe_allow_html=True)

# 1. INFORME PRINCIPAL
st.markdown("<div class='section-label'>📄 1. Informe de Dispensación</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Arrastra el archivo con pestañas NUEVO y ANTERIOR", type=["xlsx"])

# ANÁLISIS PRELIMINAR (DATO GANADOR)
if archivo_principal:
    try:
        # Mini proceso rápido para métricas
        df_pre = pd.read_excel(archivo_principal, sheet_name="NUEVO")
        impactos = len(df_pre)
        # Buscar columna de producto (puede variar el nombre por normalización)
        nom_cols = [str(c).lower() for c in df_pre.columns]
        idx_prod = nom_cols.index('producto') if 'producto' in nom_cols else -1
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="apple-card"><div class="metric-title">Impactos Totales</div><div class="metric-value">{impactos:,}</div></div>', unsafe_allow_html=True)
        with c2:
            if idx_prod != -1:
                top_p = df_pre.iloc[:, idx_prod].value_counts().idxmax()
                st.markdown(f'<div class="apple-card"><div class="metric-title">Producto más crítico</div><div class="metric-value" style="font-size:1.1rem;">{top_p}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="apple-card"><div class="metric-title">Estado</div><div class="metric-value" style="color:#34C759;">Listo</div></div>', unsafe_allow_html=True)
    except:
        st.warning("No se pudo generar el análisis previo. Asegúrate de tener la pestaña 'NUEVO'.")

# 2. BODEGAS
st.markdown("<div class='section-label'>🏢 2. Búsqueda de Cuentas (Bodegas)</div>", unsafe_allow_html=True)
col_l, col_r = st.columns(2)
with col_l:
    b1 = st.file_uploader("Bodega 1 (Central)", type=["xlsx","xls","csv"])
    b7 = st.file_uploader("Bodega 7", type=["xlsx","xls","csv"])
with col_r:
    b5 = st.file_uploader("Bodega 5", type=["xlsx","xls","csv"])
    b6 = st.file_uploader("Bodega 6", type=["xlsx","xls","csv"])

# 3. PROCESO
st.markdown("<br>", unsafe_allow_html=True)
if st.button("GENERAR CONSOLIDADO INTELIGENTE"):
    if archivo_principal is None:
        st.error("Debes cargar el informe principal.")
    else:
        with st.status("Ejecutando algoritmos de cruce...", expanded=True) as status:
            # Lógica pura
            df_final, df_hist = transformar_informe(archivo_principal)
            
            dict_b1 = procesar_bodega(b1, 1)
            dict_b7 = procesar_bodega(b7, 7)
            dict_b5 = procesar_bodega(b5, 5)
            dict_b6 = procesar_bodega(b6, 6)
            
            hist_dict = dict(zip(df_hist["ID"], df_hist["cuenta"]))
            
            # Asignación de cuenta
            for i, row in df_final.iterrows():
                bod = int(row["Bod"])
                codigo = str(limpiar_valor(row["Codigo"])).strip().upper()
                id_val = str(bod) + codigo
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
            status.update(label="¡Proceso Completado!", state="complete")

        # Descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
        output.seek(0)
        
        st.balloons()
        st.download_button(
            label="✨ Descargar Resultado Final",
            data=output,
            file_name="CONSOLIDADO_CUENTAS_DATALOGIX.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
