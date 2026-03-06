import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# CONFIGURACIÓN DE PÁGINA (ESTILO PREMIUM APPLE)
# =========================================================
st.set_page_config(
    page_title="DataLogix Pro | Intelligence in Motion",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE DISEÑO APPLE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --apple-blue: #007AFF;
        --apple-green: #34C759;
        --apple-gray: #8E8E93;
        --apple-bg: #F5F5F7;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--apple-bg);
        color: #1D1D1F;
    }

    /* Contenedores Estilo Glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        border: 1px solid var(--apple-blue);
    }

    .main-title {
        font-weight: 700;
        font-size: 3.5rem;
        letter-spacing: -2px;
        background: linear-gradient(180deg, #1D1D1F 0%, #434344 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }

    .sub-text {
        color: var(--apple-gray);
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 40px;
    }

    /* Botón Pro */
    .stButton > button {
        background: #1D1D1F !important;
        color: white !important;
        border-radius: 999px !important;
        padding: 12px 40px !important;
        font-weight: 500 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        width: 100%;
        font-size: 1.1rem !important;
    }
    
    .stButton > button:hover {
        background: var(--apple-blue) !important;
        transform: scale(1.02);
    }

    /* File Uploader Custom */
    [data-testid="stFileUploader"] {
        border: 2px dashed #D2D2D7 !important;
        border-radius: 20px !important;
        background: white !important;
    }

    .insight-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--apple-gray);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .insight-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1D1D1F;
        margin-top: 5px;
    }

    .planner-badge {
        background: #E8F2FF;
        color: var(--apple-blue);
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LÓGICA DE PROCESAMIENTO (MOTOR HEURÍSTICO)
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

def calcular_tipo_novedad(df, columna_fecha):
    df[columna_fecha] = pd.to_datetime(df[columna_fecha], dayfirst=True, errors="coerce")
    df["Tipo Novedad"] = "Agotado" # Default
    df.loc[df[columna_fecha] == pd.Timestamp("6000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("5000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("3000-01-01"), "Tipo Novedad"] = "Descontinuado"
    return df

@st.cache_data
def extraer_insights_premium(archivo):
    df = pd.read_excel(archivo, sheet_name="NUEVO")
    df_norm = normalizar_columnas(df.copy())
    df_norm = calcular_tipo_novedad(df_norm, "fecha novedad" if "fecha novedad" in df_norm.columns else df_norm.columns[3])
    
    insights = {
        "total_impactos": len(df),
        "refs_unicas": df_norm["codigo"].nunique() if "codigo" in df_norm.columns else 0,
        "top_planeador": df_norm["pleaneador"].value_counts().idxmax() if "pleaneador" in df_norm.columns else "N/A",
        "impactos_top_p": df_norm["pleaneador"].value_counts().max() if "pleaneador" in df_norm.columns else 0,
        "top_producto": df_norm["producto"].value_counts().idxmax() if "producto" in df_norm.columns else "N/A",
        "novedades_dist": df_norm["Tipo Novedad"].value_counts().to_dict()
    }
    return insights, df_norm

def procesar_bodega(file, num):
    if file is None: return {}
    df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, encoding='latin1')
    df.columns = [str(c).strip().title() for c in df.columns]
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().str.upper()
    df["ID"] = str(num) + df["Codigo"]
    return df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).to_dict()

# =========================================================
# INTERFAZ DE USUARIO (EL LIENZO DE JOBS)
# =========================================================

# SIDEBAR: PANEL DE CONTROL
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/665/665939.png", width=80)
    st.markdown("### Control Center")
    st.markdown("---")
    st.markdown("**Sistema:** Activo")
    st.markdown("**Motor:** Heurístico v3.5")
    st.markdown("---")
    if st.button("Resetear Memoria"):
        st.cache_data.clear()
        st.rerun()

# TITULAR PRINCIPAL
st.markdown("<h1 class='main-title'>Intelligence in Motion.</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-text'>Diseñado para la precisión. Construido para la velocidad.</p>", unsafe_allow_html=True)

# 1. INGESTA MAESTRA
st.markdown("<div class='section-label'>01. INFORME MATRIZ</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Arrastra el archivo maestro de faltantes", type=["xlsx"])

if archivo_principal:
    with st.spinner("Analizando ADN logístico..."):
        insights, df_preview = extraer_insights_premium(archivo_principal)

    # DASHBOARD DE INDICADORES REALES
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""<div class='metric-card'>
            <p class='insight-label'>Escala de Impacto</p>
            <p class='insight-value'>{insights['total_impactos']:,}</p>
            <p style='color:var(--apple-gray); font-size:0.8rem;'>Líneas totales a gestionar</p>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div class='metric-card'>
            <p class='insight-label'>Diversidad de SKU</p>
            <p class='insight-value'>{insights['refs_unicas']:,}</p>
            <p style='color:var(--apple-gray); font-size:0.8rem;'>Referencias únicas afectadas</p>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""<div class='metric-card'>
            <p class='insight-label'>Carga Crítica</p>
            <p class='insight-value' style='font-size:1.4rem; padding-top:10px;'>{insights['top_planeador']}</p>
            <span class='planner-badge'>{insights['impactos_top_p']} Impactos</span>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""<div class='metric-card'>
            <p class='insight-label'>Foco de Atención</p>
            <p class='insight-value' style='font-size:0.9rem; color:var(--apple-blue); margin-top:15px;'>{insights['top_producto'][:50]}...</p>
            <p style='color:var(--apple-gray); font-size:0.8rem;'>Producto con más quiebres</p>
        </div>""", unsafe_allow_html=True)

    # SEGUNDA FILA DE INSIGHTS: GRÁFICOS
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1.5])

    with g1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<p class='insight-label'>Distribución de Novedades</p>", unsafe_allow_html=True)
        fig_pie = px.pie(
            values=list(insights['novedades_dist'].values()),
            names=list(insights['novedades_dist'].keys()),
            hole=0.7,
            color_discrete_sequence=[px.colors.qualitative.Pastel[0], '#1D1D1F', '#FF3B30']
        )
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False, height=250)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with g2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<p class='insight-label'>Ranking de Planeadores (Top 5)</p>", unsafe_allow_html=True)
        top_5_p = df_preview["pleaneador"].value_counts().head(5)
        fig_bar = px.bar(
            x=top_5_p.values,
            y=top_5_p.index,
            orientation='h',
            color_discrete_sequence=['#007AFF']
        )
        fig_bar.update_layout(
            margin=dict(t=10, b=10, l=0, r=0),
            height=240,
            xaxis_title=None, yaxis_title=None,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# 2. RED DE BODEGAS
st.markdown("<br><div class='section-label'>02. NETWORK BODEGAS</div>", unsafe_allow_html=True)
with st.expander("Expandir Red de Distribución", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        b1 = st.file_uploader("Nodo Central (B1)", type=["xlsx","csv"])
        b7 = st.file_uploader("Nodo Satélite (B7)", type=["xlsx","csv"])
    with col_b:
        b5 = st.file_uploader("Nodo Especial (B5)", type=["xlsx","csv"])
        b6 = st.file_uploader("Nodo Regional (B6)", type=["xlsx","csv"])

# 3. ACCIÓN FINAL
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("EJECUTAR CONSOLIDACIÓN MAESTRA"):
    if not archivo_principal:
        st.error("Apple no permite procesos sin fuente. Sube el informe maestro.")
    else:
        with st.status("Sincronizando universos de datos...", expanded=True) as status:
            st.write("Estructurando Pestañas NUEVO/ANTERIOR...")
            df_nuevo = pd.read_excel(archivo_principal, sheet_name="NUEVO")
            df_anterior = pd.read_excel(archivo_principal, sheet_name="ANTERIOR")
            
            df_nuevo = normalizar_columnas(df_nuevo)
            df_anterior = normalizar_columnas(df_anterior)
            
            # IDs y Limpieza
            df_nuevo["bodega"] = df_nuevo["bodega"].apply(limpiar_valor)
            df_nuevo["codigo"] = df_nuevo["codigo"].apply(limpiar_valor)
            df_nuevo["ID"] = df_nuevo["bodega"] + df_nuevo["codigo"]
            
            df_anterior["bod"] = df_anterior["bod"].apply(limpiar_valor)
            df_anterior["codigo"] = df_anterior["codigo"].apply(limpiar_valor)
            df_anterior["ID"] = df_anterior["bod"] + df_anterior["codigo"]

            st.write("Mapeando Red de Bodegas...")
            d1 = procesar_bodega(b1, 1); d7 = procesar_bodega(b7, 7)
            d5 = procesar_bodega(b5, 5); d6 = procesar_bodega(b6, 6)
            
            st.write("Calculando Novedades e Históricos...")
            df_nuevo = calcular_tipo_novedad(df_nuevo, "fecha novedad" if "fecha novedad" in df_nuevo.columns else df_nuevo.columns[3])
            
            # Merge Histórico
            col_hist = ["ID", "abastecimiento", "dispensacion", "aliados", "responsable", "cuenta"]
            df_hist = df_anterior[[c for c in col_hist if c in df_anterior.columns]].copy()
            df_final = df_nuevo.merge(df_hist, on="ID", how="left")
            
            st.write("Finalizando asignación de Cuentas...")
            # Lógica de asignación (simplificada para velocidad)
            def asignar(row):
                bod = row["bodega"]
                id_v = row["ID"]
                if bod == "21": return "EPM"
                if bod == "19": return "UDEA"
                if bod == "16": return "HMUA"
                return d1.get(id_v, d7.get(id_v, d5.get(id_v, d6.get(id_v, getattr(row, 'cuenta', "")))))

            df_final["CUENTA"] = df_final.apply(asignar, axis=1)
            
            status.update(label="Sincronización Completa", state="complete")

        # DESCARGA PREMIUM
        output = io.BytesIO()
        df_final.to_excel(output, index=False)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label=" DESCARGAR RESULTADO FINAL",
            data=output.getvalue(),
            file_name="DataLogix_Master_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.balloons()
