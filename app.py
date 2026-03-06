import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import plotly.express as px

# =========================================================
# CONFIGURACIÓN DE PÁGINA (ESTILO JOBS: PERFECCIÓN RADICAL)
# =========================================================
st.set_page_config(
    page_title="DataLogix | Control",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
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

    .apple-card {
        background: #FFFFFF;
        border-radius: 18px;
        border: 1px solid #D2D2D7;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        height: 100%;
    }
    
    .main-title {
        font-weight: 700;
        font-size: 2.8rem;
        letter-spacing: -1.5px;
        color: #1D1D1F;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #86868B;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }

    /* Botón Ejecutar */
    .stButton > button {
        background: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 14px 40px !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #007AFF !important;
        transform: scale(1.01);
    }

    .section-label {
        font-weight: 600;
        color: #1D1D1F;
        font-size: 1.2rem;
        margin: 2.5rem 0 1rem 0;
    }
    
    .insight-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #86868B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .insight-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1D1D1F;
    }

    /* Eliminar espacios vacíos de Streamlit */
    .block-container { padding-top: 2rem; }
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

def extraer_analisis_premium(archivo):
    df_new = pd.read_excel(archivo, sheet_name="NUEVO")
    df_norm = normalizar_columnas(df_new.copy())
    
    # Métricas
    impactos = len(df_new)
    refs_unicas = df_norm["codigo"].nunique() if "codigo" in df_norm.columns else 0
    col_plan = next((c for c in ["pleaneador", "planeador"] if c in df_norm.columns), None)
    top_p = df_norm[col_plan].value_counts().idxmax() if col_plan else "N/A"
    
    # Top 5 Referencias por suma de Numero Pedidos
    col_ped = "numero pedidos"
    if "codigo" in df_norm.columns and col_ped in df_norm.columns:
        df_norm[col_ped] = pd.to_numeric(df_norm[col_ped], errors='coerce').fillna(0)
        top_5 = df_norm.groupby("codigo")[col_ped].sum().nlargest(5).reset_index()
        top_5["codigo"] = top_5["codigo"].str.upper()
    else:
        top_5 = pd.DataFrame()

    return {"total": impactos, "refs": refs_unicas, "plan": top_p, "top_5": top_5}

def transformar_informe(archivo_excel):
    df_nuevo = pd.read_excel(archivo_excel, sheet_name="NUEVO")
    df_anterior = pd.read_excel(archivo_excel, sheet_name="ANTERIOR")
    
    df_nuevo = normalizar_columnas(df_nuevo)
    df_anterior = normalizar_columnas(df_anterior)
    
    # IDs
    df_nuevo["ID"] = df_nuevo["bodega"].apply(limpiar_valor) + df_nuevo["codigo"].apply(limpiar_valor)
    df_anterior["ID"] = df_anterior["bod"].apply(limpiar_valor) + df_anterior["codigo"].apply(limpiar_valor)

    # Novedades
    col_f = "fecha novedad"
    df_nuevo[col_f] = pd.to_datetime(df_nuevo[col_f], dayfirst=True, errors="coerce")
    df_nuevo["Tipo Novedad"] = np.nan
    df_nuevo.loc[df_nuevo[col_f] == pd.Timestamp("6000-01-01"), "Tipo Novedad"] = "Invima"
    df_nuevo.loc[df_nuevo[col_f] == pd.Timestamp("3000-01-01"), "Tipo Novedad"] = "Descontinuado"
    df_nuevo.loc[(df_nuevo[col_f].notna() & df_nuevo["Tipo Novedad"].isna()), "Tipo Novedad"] = "Agotado"
    
    # Merge
    col_hist = ["ID", "abastecimiento", "dispensacion", "aliados", "responsable", "cuenta"]
    df_hist = df_anterior[[c for c in col_hist if c in df_anterior.columns]].copy()
    df_final = df_nuevo.merge(df_hist, on="ID", how="left")
    
    return df_final, df_hist

def procesar_bodega(file, num):
    if file is None: return {}
    df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, encoding='latin1')
    df.columns = [str(c).strip().title() for c in df.columns]
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().str.upper()
    df["ID"] = str(num) + df["Codigo"]
    return df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).to_dict()

# =========================================================
# INTERFAZ DE USUARIO
# =========================================================

st.markdown("<h1 class='main-title'>Informe de Faltantes de Dispensación</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Consolidación de datos y cruce de cuentas maestro.</p>", unsafe_allow_html=True)

# 1. INFORME MAESTRO
st.markdown("<div class='section-label'>1. Archivo Maestro</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Subir Excel (Pestañas NUEVO / ANTERIOR)", type=["xlsx"])

if archivo_principal:
    res = extraer_analisis_premium(archivo_principal)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='apple-card'><p class='insight-label'>Impactos Totales</p><p class='insight-value'>{res['total']}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='apple-card'><p class='insight-label'>Refs. Únicas</p><p class='insight-value'>{res['refs']}</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='apple-card'><p class='insight-label'>Planeador Crítico</p><p class='insight-value' style='font-size:1.4rem;'>{res['plan']}</p></div>", unsafe_allow_html=True)

    # Gráfico Top 5 Referencias
    if not res['top_5'].empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='apple-card'>", unsafe_allow_html=True)
        st.markdown("<p class='insight-label'>Top 5 Referencias con más Pedidos</p>", unsafe_allow_html=True)
        fig = px.bar(res['top_5'], x='numero pedidos', y='codigo', orientation='h', text='numero pedidos')
        fig.update_traces(marker_color='#1D1D1F', textposition='outside')
        fig.update_layout(margin=dict(t=10, b=10, l=0, r=40), height=300, xaxis_visible=False, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# 2. BODEGAS (SIN EXPANDIR)
st.markdown("<div class='section-label'>2. Reportes de Bodega</div>", unsafe_allow_html=True)
col_a, col_b = st.columns(2)
with col_a:
    b1 = st.file_uploader("Bodega 1", type=["xlsx","csv"])
    b7 = st.file_uploader("Bodega 7", type=["xlsx","csv"])
with col_b:
    b5 = st.file_uploader("Bodega 5", type=["xlsx","csv"])
    b6 = st.file_uploader("Bodega 6", type=["xlsx","csv"])

# 3. EJECUTAR
st.markdown("<br>", unsafe_allow_html=True)
if st.button("Ejecutar"):
    if not archivo_principal:
        st.error("Falta el archivo maestro.")
    else:
        with st.spinner("Procesando..."):
            df_final, df_hist = transformar_informe(archivo_principal)
            d1 = procesar_bodega(b1, 1); d7 = procesar_bodega(b7, 7)
            d5 = procesar_bodega(b5, 5); d6 = procesar_bodega(b6, 6)
            hist_dict = dict(zip(df_hist["ID"], df_hist.get("cuenta", "")))

            def asignar(row):
                bod = str(limpiar_valor(row.get("bodega", "")))
                id_v = row["ID"]
                if bod == "21": return "EPM"
                if bod == "19": return "UDEA"
                if bod == "16": return "HMUA"
                return d1.get(id_v, d7.get(id_v, d5.get(id_v, d6.get(id_v, hist_dict.get(id_v, "")))))

            df_final["CUENTA"] = df_final.apply(asignar, axis=1)
            
            output = io.BytesIO()
            df_final.to_excel(output, index=False)
            st.success("Proceso completado.")
            st.download_button("Descargar Reporte Final", output.getvalue(), "Reporte_Faltantes.xlsx", use_container_width=True)
