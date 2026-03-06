import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import plotly.express as px

# =========================================================
# CONFIGURACIÓN DE PÁGINA: MINIMALISMO ABSOLUTO
# =========================================================
st.set_page_config(
    page_title="DataLogix Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE DISEÑO OBSIDIAN V4.0 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        background-color: #FFFFFF;
        color: #1D1D1F;
    }

    .apple-card {
        background: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E5E5E7;
        padding: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
    }
    
    .apple-card:hover {
        border-color: #007AFF;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }

    .main-title {
        font-weight: 700;
        font-size: 2.5rem;
        letter-spacing: -1.2px;
        color: #1D1D1F;
        margin-bottom: 0px;
    }

    .sub-title {
        color: #86868B;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 40px;
    }

    /* Botón Ejecutar Estilo Apple Black */
    .stButton > button {
        background: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        width: 100%;
        transition: background 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #323232 !important;
    }

    .section-label {
        font-weight: 600;
        color: #1D1D1F;
        font-size: 1.1rem;
        margin: 2rem 0 1rem 0;
        border-left: 3px solid #007AFF;
        padding-left: 12px;
    }
    
    .insight-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #86868B;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }

    .insight-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1D1D1F;
    }

    /* Ocultar basura visual de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 3rem; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# NÚCLEO LÓGICO (INVICTO)
# =========================================================

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = texto.strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', '', texto).strip()

def limpiar_valor(valor):
    if pd.isna(valor) or valor == "": return ""
    return str(valor).replace(".0", "").strip()

def leer_excel_seguro(file, sheet=0):
    try:
        file.seek(0)
        return pd.read_excel(file, sheet_name=sheet)
    except:
        return None

def procesar_bodega(file, num):
    """Procesamiento de bodegas con corrección del TypeError"""
    if file is None: return {}
    df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, encoding='latin1')
    
    # Estandarizar columnas
    df.columns = [str(c).strip().title() for c in df.columns]
    
    if "Codigo" not in df.columns or "Nombres" not in df.columns:
        return {}

    # Generar ID
    df["ID"] = str(num) + df["Codigo"].apply(limpiar_valor).astype(str).str.strip().str.upper()
    
    # SOLUCIÓN AL TYPEERROR: Forzar a string y eliminar nulos antes de agrupar
    df["Nombres"] = df["Nombres"].astype(str).replace(['nan', 'None', ''], np.nan)
    
    # Agrupación segura
    def join_nombres(x):
        nombres_limpios = [str(n).strip().upper() for n in x if pd.notna(n) and str(n).strip() != ""]
        return ", ".join(sorted(list(set(nombres_limpios))))

    return df.groupby("ID")["Nombres"].apply(join_nombres).to_dict()

# =========================================================
# INTERFAZ DE USUARIO (SIMPLICIDAD ES SOFISTICACIÓN)
# =========================================================

st.markdown("<h1 class='main-title'>Informe de Faltantes de Dispensación</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Consolidación profesional de suministros.</p>", unsafe_allow_html=True)

# 1. CARGA MAESTRA
st.markdown("<div class='section-label'>Archivo Maestro</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Cargue el archivo con pestañas NUEVO y ANTERIOR", type=["xlsx"], label_visibility="collapsed")

if archivo_principal:
    try:
        df_new_raw = leer_excel_seguro(archivo_principal, "NUEVO")
        if df_new_raw is not None:
            # Análisis rápido para indicadores
            df_norm = df_new_raw.copy()
            df_norm.columns = [normalizar_texto(c) for c in df_norm.columns]
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='apple-card'><p class='insight-label'>Impactos Totales</p><p class='insight-value'>{len(df_new_raw):,}</p></div>", unsafe_allow_html=True)
            with c2:
                refs = df_norm['codigo'].nunique() if 'codigo' in df_norm.columns else 0
                st.markdown(f"<div class='apple-card'><p class='insight-label'>Refs. Únicas</p><p class='insight-value'>{refs:,}</p></div>", unsafe_allow_html=True)
            with c3:
                plan_col = next((c for c in ["pleaneador", "planeador"] if c in df_norm.columns), None)
                top_p = df_norm[plan_col].value_counts().idxmax() if plan_col else "N/D"
                st.markdown(f"<div class='apple-card'><p class='insight-label'>Planeador Crítico</p><p class='insight-value' style='font-size:1.4rem;'>{str(top_p).upper()}</p></div>", unsafe_allow_html=True)

            # TOP 5 REFERENCIAS POR NUMERO PEDIDOS
            ped_col = "numero pedidos"
            if "codigo" in df_norm.columns and ped_col in df_norm.columns:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='apple-card'>", unsafe_allow_html=True)
                st.markdown("<p class='insight-label'>Top 5 Referencias con más Pedidos (Suma)</p>", unsafe_allow_html=True)
                
                df_norm[ped_col] = pd.to_numeric(df_norm[ped_col], errors='coerce').fillna(0)
                top_5 = df_norm.groupby("codigo")[ped_col].sum().nlargest(5).reset_index()
                top_5["codigo"] = top_5["codigo"].astype(str).str.upper()
                
                fig = px.bar(top_5, x=ped_col, y='codigo', orientation='h', text=ped_col)
                fig.update_traces(marker_color='#1D1D1F', textposition='outside', textfont_size=12)
                fig.update_layout(
                    margin=dict(t=0, b=0, l=0, r=40),
                    height=280,
                    xaxis_visible=False,
                    yaxis_title=None,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Inter", size=12)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error en estructura: {e}")

# 2. BODEGAS (SISTEMA DE RED)
st.markdown("<div class='section-label'>Reportes de Bodega</div>", unsafe_allow_html=True)
col_l, col_r = st.columns(2)
with col_l:
    b1 = st.file_uploader("Bodega 1", type=["xlsx", "csv"])
    b7 = st.file_uploader("Bodega 7", type=["xlsx", "csv"])
with col_r:
    b5 = st.file_uploader("Bodega 5", type=["xlsx", "csv"])
    b6 = st.file_uploader("Bodega 6", type=["xlsx", "csv"])

# 3. EJECUCIÓN
st.markdown("<br>", unsafe_allow_html=True)
if st.button("Ejecutar"):
    if not archivo_principal:
        st.warning("Debe cargar el Informe Maestro primero.")
    else:
        with st.status("Procesando datos...", expanded=False) as status:
            # Leer hojas
            df_nuevo = pd.read_excel(archivo_principal, sheet_name="NUEVO")
            df_anterior = pd.read_excel(archivo_principal, sheet_name="ANTERIOR")
            
            # Normalizar nombres de columnas para lógica interna
            df_nuevo.columns = [normalizar_texto(c) for c in df_nuevo.columns]
            df_anterior.columns = [normalizar_texto(c) for c in df_anterior.columns]
            
            # Crear IDs
            df_nuevo["ID"] = df_nuevo["bodega"].apply(limpiar_valor) + df_nuevo["codigo"].apply(limpiar_valor)
            df_anterior["ID"] = df_anterior["bod"].apply(limpiar_valor) + df_anterior["codigo"].apply(limpiar_valor)
            
            # Procesar Cuentas de Bodegas
            dict_b1 = procesar_bodega(b1, 1); dict_b7 = procesar_bodega(b7, 7)
            dict_b5 = procesar_bodega(b5, 5); dict_b6 = procesar_bodega(b6, 6)
            
            # Mapeo histórico
            hist_dict = dict(zip(df_anterior["ID"], df_anterior.get("cuenta", "")))
            
            # Lógica de asignación definitiva
            def asignar_cuenta(row):
                bod = str(limpiar_valor(row.get("bodega", "")))
                id_v = row["ID"]
                
                if bod == "21": return "EPM"
                if bod == "19": return "UDEA"
                if bod == "16": return "HMUA"
                
                # Buscar en bodegas subidas
                res = dict_b1.get(id_v) or dict_b7.get(id_v) or dict_b5.get(id_v) or dict_b6.get(id_v)
                if res: return res
                
                # Buscar en histórico
                return hist_dict.get(id_v, "")

            df_nuevo["CUENTA"] = df_nuevo.apply(asignar_cuenta, axis=1)
            
            # Preparar descarga (Renombrar a formato original si es necesario)
            output = io.BytesIO()
            df_nuevo.to_excel(output, index=False)
            status.update(label="Proceso completado con éxito.", state="complete")

        st.download_button(
            label="Descargar Reporte Final",
            data=output.getvalue(),
            file_name="Resultado_Faltantes_Consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
