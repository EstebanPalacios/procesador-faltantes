import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import plotly.express as px

# =========================================================
# CONFIGURACIÓN DE PÁGINA: ESTÁNDAR PRO
# =========================================================
st.set_page_config(
    page_title="DataLogix Pro",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE DISEÑO: PURE APPLE WHITE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        background-color: #FFFFFF;
        color: #1D1D1F;
    }

    /* Tarjetas de Información */
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E5E5E7;
        padding: 24px;
        transition: all 0.2s ease-in-out;
        height: 100%;
    }
    .metric-card:hover {
        border-color: #D2D2D7;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
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
        margin-bottom: 40px;
    }

    /* Botón Ejecutar Estilo Apple Black */
    .stButton > button {
        background: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 14px 40px !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        width: 100%;
        margin-top: 20px;
    }
    
    .stButton > button:hover {
        background: #1D1D1F !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .section-label {
        font-weight: 600;
        color: #1D1D1F;
        font-size: 1.2rem;
        margin: 2.5rem 0 1rem 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #E5E5E7;
    }
    
    .insight-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #86868B;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }

    .insight-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1D1D1F;
    }

    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 2.5rem; }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LÓGICA DE PROCESAMIENTO (SIN CAMBIOS EN ESTRUCTURA)
# =========================================================

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = texto.strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', '', texto).strip()

def limpiar_valor(valor):
    if pd.isna(valor) or valor == "": return ""
    return str(valor).replace(".0", "").strip()

def limpiar_texto_simple(texto):
    if pd.isna(texto): return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in texto if not unicodedata.combining(c))

def procesar_bodega(file, num):
    """Función de cruce de bodegas con blindaje contra TypeError"""
    if file is None: return {}
    try:
        df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, encoding='latin1')
        df.columns = [str(c).strip().title() for c in df.columns]
        
        if "Codigo" not in df.columns or "Nombres" not in df.columns:
            return {}

        df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().str.upper()
        df["ID"] = str(num) + df["Codigo"]
        
        # Blindaje contra nulos y tipos mixtos para el sorted
        df["Nombres"] = df["Nombres"].apply(limpiar_texto_simple)
        
        def join_seguro(x):
            nombres = [str(n) for n in x if n and str(n).strip() != ""]
            return ", ".join(sorted(list(set(nombres))))

        return df.groupby("ID")["Nombres"].apply(join_seguro).to_dict()
    except:
        return {}

def transformar_informe(archivo_excel):
    """Mantiene la lógica exacta y el orden de columnas original"""
    df_nuevo = pd.read_excel(archivo_excel, sheet_name="NUEVO")
    df_anterior = pd.read_excel(archivo_excel, sheet_name="ANTERIOR")
    
    # Normalización interna para procesamiento
    df_n = df_nuevo.copy()
    df_a = df_anterior.copy()
    df_n.columns = [normalizar_texto(c) for c in df_n.columns]
    df_a.columns = [normalizar_texto(c) for c in df_a.columns]
    
    # IDs
    df_n["ID"] = df_n["bodega"].apply(limpiar_valor) + df_n["codigo"].apply(limpiar_valor)
    df_a["ID"] = df_a["bod"].apply(limpiar_valor) + df_a["codigo"].apply(limpiar_valor)

    # Mapeo de nombres para reporte final (Conserva tu estructura)
    mapeo = {
        "prioritario": "PRIORITARIO", "bodega": "Bod", "codigo": "Codigo",
        "fecha novedad": "Fecha Novedad", "producto": "Producto",
        "generico": "Generico", "proveedor": "División", "pleaneador": "Planeador",
        "fechaentrega antigua": "Fecha Entrega Pedido", "num pedidos": "Numero Pedidos",
        "pendiente": "Pendiente", "traslado": "Traslados", "solicitud traslado": "Solicitud Traslados",
    }
    df_final = df_n.rename(columns=mapeo)
    
    # Cálculo de Tipo Novedad (Tu lógica de fechas)
    df_final["Fecha Novedad"] = pd.to_datetime(df_final["Fecha Novedad"], dayfirst=True, errors="coerce")
    df_final["Tipo Novedad"] = np.nan
    df_final.loc[df_final["Fecha Novedad"] == pd.Timestamp("6000-01-01"), "Tipo Novedad"] = "Invima"
    df_final.loc[df_final["Fecha Novedad"] == pd.Timestamp("5000-01-01"), "Tipo Novedad"] = "Invima"
    df_final.loc[df_final["Fecha Novedad"] == pd.Timestamp("3000-01-01"), "Tipo Novedad"] = "Descontinuado"
    df_final.loc[(df_final["Fecha Novedad"].notna() & df_final["Tipo Novedad"].isna()), "Tipo Novedad"] = "Agotado"
    
    # Cruce con histórico
    col_hist = ["ID", "abastecimiento", "dispensacion", "aliados", "responsable", "cuenta"]
    df_hist = df_a[[c for c in col_hist if c in df_a.columns]].copy()
    
    df_output = df_final.merge(df_hist, on="ID", how="left")
    df_output["CUENTA"] = ""
    
    # Orden de columnas ESTRICTO (El que pediste)
    cols = [
        "ID","PRIORITARIO","Bod","Codigo","Fecha Novedad","Producto","Generico","División",
        "Planeador","Fecha Entrega Pedido","Numero Pedidos","Pendiente","Traslados",
        "Solicitud Traslados","Tipo Novedad","abastecimiento","dispensacion","aliados","CUENTA","responsable"
    ]
    for c in cols:
        if c not in df_output.columns: df_output[c] = ""
        
    return df_output[cols], df_hist

# =========================================================
# INTERFAZ DE USUARIO: EL LIENZO
# =========================================================

st.markdown("<h1 class='main-title'>Informe de Faltantes de Dispensación</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Sistema de consolidación y análisis logístico centralizado.</p>", unsafe_allow_html=True)

# 1. ARCHIVO MAESTRO
st.markdown("<div class='section-label'>Carga de Datos Maestros</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Subir Archivo Excel (Pestañas NUEVO y ANTERIOR)", type=["xlsx"], label_visibility="collapsed")

if archivo_principal:
    try:
        # Análisis de Dashboards
        df_dash = pd.read_excel(archivo_principal, sheet_name="NUEVO")
        df_dash.columns = [normalizar_texto(c) for c in df_dash.columns]
        
        # Métricas principales
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='metric-card'><p class='insight-label'>Líneas Faltantes</p><p class='insight-value'>{len(df_dash):,}</p></div>", unsafe_allow_html=True)
        with m2:
            refs = df_dash['codigo'].nunique() if 'codigo' in df_dash.columns else 0
            st.markdown(f"<div class='metric-card'><p class='insight-label'>Referencias Únicas</p><p class='insight-value'>{refs:,}</p></div>", unsafe_allow_html=True)
        with m3:
            total_pedidos = pd.to_numeric(df_dash['num pedidos'], errors='coerce').sum() if 'num pedidos' in df_dash.columns else 0
            st.markdown(f"<div class='metric-card'><p class='insight-label'>Pedidos Afectados</p><p class='insight-value'>{int(total_pedidos):,}</p></div>", unsafe_allow_html=True)

        # GRÁFICOS ESTRATÉGICOS
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown("<p class='insight-label'>Top 5 Planeadores (Mayor Novedad)</p>", unsafe_allow_html=True)
            p_col = next((c for c in ["pleaneador", "planeador"] if c in df_dash.columns), None)
            if p_col:
                top_p = df_dash[p_col].value_counts().nlargest(5).reset_index()
                fig1 = px.bar(top_p, x='count', y=p_col, orientation='h', text_auto=True)
                fig1.update_traces(marker_color='#1D1D1F')
                fig1.update_layout(margin=dict(t=10,b=10,l=0,r=10), height=300, xaxis_visible=False, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

        with g2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown("<p class='insight-label'>Top 5 SKU (Impacto en Pedidos)</p>", unsafe_allow_html=True)
            if 'codigo' in df_dash.columns and 'num pedidos' in df_dash.columns:
                df_dash['num pedidos'] = pd.to_numeric(df_dash['num pedidos'], errors='coerce').fillna(0)
                top_sku = df_dash.groupby('codigo')['num pedidos'].sum().nlargest(5).reset_index()
                top_sku['codigo'] = top_sku['codigo'].astype(str).str.upper()
                fig2 = px.bar(top_sku, x='num pedidos', y='codigo', orientation='h', text_auto=True)
                fig2.update_traces(marker_color='#1D1D1F')
                fig2.update_layout(margin=dict(t=10,b=10,l=0,r=10), height=300, xaxis_visible=False, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error de lectura en archivo maestro: {e}")

# 2. BODEGAS SATÉLITE
st.markdown("<div class='section-label'>Cruce de Cuentas (Bodegas Satélite)</div>", unsafe_allow_html=True)
col_left, col_right = st.columns(2)
with col_left:
    b1 = st.file_uploader("Bodega 1", type=["xlsx", "csv"])
    b7 = st.file_uploader("Bodega 7", type=["xlsx", "csv"])
with col_right:
    b5 = st.file_uploader("Bodega 5", type=["xlsx", "csv"])
    b6 = st.file_uploader("Bodega 6", type=["xlsx", "csv"])

# 3. ACCIÓN
if st.button("Ejecutar"):
    if not archivo_principal:
        st.warning("Cargue el Informe Maestro para proceder.")
    else:
        with st.status("Ejecutando algoritmos de consolidación...", expanded=True) as status:
            st.write("📖 Analizando archivo maestro y calculando novedades...")
            df_final, df_hist = transformar_informe(archivo_principal)
            
            st.write("🔗 Indexando bases de datos de bodegas satélite...")
            dict_b1 = procesar_bodega(b1, 1); dict_b7 = procesar_bodega(b7, 7)
            dict_b5 = procesar_bodega(b5, 5); dict_b6 = procesar_bodega(b6, 6)
            
            st.write("🧪 Aplicando jerarquía de asignación de cuentas...")
            hist_dict = dict(zip(df_hist["ID"], df_hist.get("cuenta", "")))
            
            def asignar(row):
                bod = str(limpiar_valor(row["Bod"]))
                id_v = row["ID"]
                if bod == "21": return "EPM"
                if bod == "19": return "UDEA"
                if bod == "16": return "HMUA"
                
                # Prioridad 1: Bodegas del día
                cuenta = dict_b1.get(id_v) or dict_b7.get(id_v) or dict_b5.get(id_v) or dict_b6.get(id_v)
                if cuenta: return cuenta
                
                # Prioridad 2: Histórico
                return hist_dict.get(id_v, "")

            df_final["CUENTA"] = df_final.apply(asignar, axis=1)
            
            st.write("✅ Generando reporte final...")
            output = io.BytesIO()
            df_final.to_excel(output, index=False)
            status.update(label="Procesamiento completado.", state="complete")

        st.download_button(
            label="Descargar Reporte Final",
            data=output.getvalue(),
            file_name="CONSOLIDADO_FALTANTES_MAESTRO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
