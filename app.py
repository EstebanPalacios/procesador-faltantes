import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import plotly.express as px

# =========================================================
# CONFIGURACIÓN PREMIUM (ALTO NIVEL)
# =========================================================
st.set_page_config(
    page_title="DataLogix Pro | Dashboard",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE DISEÑO: GLASSMORPHISM & CRYSTAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #F8FAFC;
    }

    .main-title {
        background: linear-gradient(135deg, #007AFF 0%, #34C759 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -1.5px;
        margin-bottom: 0px;
        text-align: center;
    }
    
    .sub-title {
        color: #64748B;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 40px;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .section-label {
        color: #1E293B;
        font-size: 1rem;
        font-weight: 700;
        margin: 30px 0 15px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-label::before {
        content: "";
        width: 4px;
        height: 20px;
        background: #007AFF;
        border-radius: 10px;
    }

    .stButton>button {
        background: linear-gradient(135deg, #007AFF 0%, #00CFFF 100%);
        color: white !important;
        border-radius: 12px;
        padding: 15px;
        font-weight: 700;
        border: none;
        box-shadow: 0 10px 20px rgba(0, 122, 255, 0.15);
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# MOTOR LÓGICO (BLINDADO)
# =========================================================

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = texto.strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', '', texto).strip()

def limpiar_valor(valor):
    if pd.isna(valor) or valor == "": return ""
    return str(valor).replace(".0", "").strip()

def procesar_bodega(file, num):
    if file is None: return {}
    try:
        df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, encoding='latin1')
        df.columns = [str(c).strip().title() for c in df.columns]
        df["ID"] = str(num) + df["Codigo"].apply(limpiar_valor).astype(str).str.strip().upper()
        df["Nombres"] = df["Nombres"].astype(str).replace(['nan', 'None', ''], np.nan)
        
        def join_seguro(x):
            limpios = [str(n).strip().upper() for n in x if pd.notna(n) and str(n).strip() != ""]
            return ", ".join(sorted(list(set(limpios))))

        return df.groupby("ID")["Nombres"].apply(join_seguro).to_dict()
    except: return {}

# =========================================================
# INTERFAZ DE USUARIO
# =========================================================

st.markdown('<p class="main-title">Informe   Faltantes   de   Dispensación</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Consolidación & Visualización de Impacto</p>', unsafe_allow_html=True)

# 1. CARGA Y VISUALIZACIÓN
st.markdown('<div class="section-label">01 // INFORME DE FALTANTES DISPENSACIÓN </div>', unsafe_allow_html=True)
archivo_principal = st.file_uploader("Subir Informe Maestro (.xlsx)", type=["xlsx"], label_visibility="collapsed")

if archivo_principal:
    # --- LÓGICA DE DASHBOARD ---
    df_n = pd.read_excel(archivo_principal, sheet_name="NUEVO")
    df_n_norm = df_n.copy()
    df_n_norm.columns = [normalizar_texto(c) for c in df_n_norm.columns]

    # KPIs de Cabecera
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="glass-card"><p class="metric-label">Líneas en Novedad</p><p class="metric-value">{len(df_n):,}</p></div>', unsafe_allow_html=True)
    with c2:
        refs = df_n_norm['codigo'].nunique() if 'codigo' in df_n_norm.columns else 0
        st.markdown(f'<div class="glass-card"><p class="metric-label">SKUs Únicos</p><p class="metric-value">{refs:,}</p></div>', unsafe_allow_html=True)
    with c3:
        ped_col = "num pedidos" if "num pedidos" in df_n_norm.columns else "numero pedidos"
        total_p = pd.to_numeric(df_n_norm[ped_col], errors='coerce').sum() if ped_col in df_n_norm.columns else 0
        st.markdown(f'<div class="glass-card"><p class="metric-label">Impacto Pedidos</p><p class="metric-value">{int(total_p):,}</p></div>', unsafe_allow_html=True)

    # GRÁFICOS ANALÍTICOS
    g1, g2 = st.columns(2)
    
    with g1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Top 5 Planeadores (Volumen)</p>', unsafe_allow_html=True)
        plan_col = next((c for c in ["pleaneador", "planeador"] if c in df_n_norm.columns), None)
        if plan_col:
            top_p = df_n_norm[plan_col].value_counts().nlargest(5).reset_index()
            fig1 = px.bar(top_p, x='count', y=plan_col, orientation='h', text_auto=True,
                          color_discrete_sequence=['#007AFF'])
            fig1.update_layout(margin=dict(t=10,b=10,l=0,r=10), height=300, xaxis_visible=False, 
                              yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with g2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Top 5 SKUs (Más Pedidos Afectados)</p>', unsafe_allow_html=True)
        if 'codigo' in df_n_norm.columns and ped_col in df_n_norm.columns:
            df_n_norm[ped_col] = pd.to_numeric(df_n_norm[ped_col], errors='coerce').fillna(0)
            top_sku = df_n_norm.groupby('codigo')[ped_col].sum().nlargest(5).reset_index()
            fig2 = px.bar(top_sku, x=ped_col, y='codigo', orientation='h', text_auto=True,
                          color_discrete_sequence=['#34C759'])
            fig2.update_layout(margin=dict(t=10,b=10,l=0,r=10), height=300, xaxis_visible=False, 
                              yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

# 2. BODEGAS
st.markdown('<div class="section-label">02 // Pedidos de Bodegas (Opcional/ Cuentas Afectadas)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    bl, br = st.columns(2)
    with bl:
        f1 = st.file_uploader("Bodega 1", type=["xlsx","csv"])
        f7 = st.file_uploader("Bodega 7", type=["xlsx","csv"])
    with br:
        f5 = st.file_uploader("Bodega 5", type=["xlsx","csv"])
        f6 = st.file_uploader("Bodega 6", type=["xlsx","csv"])
    st.markdown('</div>', unsafe_allow_html=True)

# 3. EJECUCIÓN
if st.button("🚀 PROCESAR INFORME"):
    if not archivo_principal:
        st.error("Falta el archivo maestro.")
    else:
        with st.spinner("Consolidando bases de datos..."):
            # Re-leer para transformación
            df_nuevo = pd.read_excel(archivo_principal, sheet_name="NUEVO")
            df_anterior = pd.read_excel(archivo_principal, sheet_name="ANTERIOR")
            
            # Normalización
            df_n_work = df_nuevo.copy(); df_a_work = df_anterior.copy()
            df_n_work.columns = [normalizar_texto(c) for c in df_n_work.columns]
            df_a_work.columns = [normalizar_texto(c) for c in df_a_work.columns]
            
            # IDs
            df_n_work["ID"] = df_n_work["bodega"].apply(limpiar_valor) + df_n_work["codigo"].apply(limpiar_valor)
            df_a_work["ID"] = df_a_work["bod"].apply(limpiar_valor) + df_a_work["codigo"].apply(limpiar_valor)

            # Diccionarios de Bodega
            d1 = procesar_bodega(f1, 1); d7 = procesar_bodega(f7, 7)
            d5 = procesar_bodega(f5, 5); d6 = procesar_bodega(f6, 6)
            hist_dict = dict(zip(df_a_work["ID"], df_a_work.get("cuenta", "")))

            # Asignación de Cuenta
            def asignar(row):
                bod = str(limpiar_valor(row.get("bodega", "")))
                id_v = row["ID"]
                if bod == "21": return "EPM"
                if bod == "19": return "UDEA"
                if bod == "16": return "HMUA"
                res = d1.get(id_v) or d7.get(id_v) or d5.get(id_v) or d6.get(id_v)
                return res if res else hist_dict.get(id_v, "")

            df_n_work["CUENTA"] = df_n_work.apply(asignar, axis=1)
            
            # Volver a nombres originales para exportar
            df_nuevo["CUENTA"] = df_n_work["CUENTA"]
            
            output = io.BytesIO()
            df_nuevo.to_excel(output, index=False)
            st.success("¡Informe consolidado listo!")
            st.download_button("📥 Descargar Reporte", output.getvalue(), "Consolidado_DataLogix.xlsx", use_container_width=True)
