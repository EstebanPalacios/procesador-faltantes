import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import time

# Configuración de alta gama
st.set_page_config(
    page_title="DataLogix Pro | Gestión de Dispensación",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE DISEÑO (CSS DE ALTO NIVEL) ---
st.markdown("""
    <style>
    /* Importar tipografía premium */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #FDFDFD;
    }

    /* Contenedor Principal de Módulos */
    .module-card {
        background: white;
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.03);
        border: 1px solid #F0F0F0;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    }
    
    .module-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(79, 70, 229, 0.08);
        border-color: #E0E7FF;
    }

    /* Headers con estilo técnico */
    .section-header {
        color: #1E293B;
        font-size: 0.9rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-header::before {
        content: "";
        width: 4px;
        height: 18px;
        background: #4F46E5;
        border-radius: 10px;
    }

    /* Botón Maestro Moderno */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        color: white !important;
        border-radius: 12px;
        padding: 20px;
        font-weight: 600;
        border: none;
        letter-spacing: 1px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        box-shadow: 0 15px 30px rgba(79, 70, 229, 0.3);
        transform: scale(1.01);
    }

    /* Estilización de los file uploaders */
    .stFileUploader section {
        background-color: #FAFAFA;
        border: 1px dashed #CBD5E1 !important;
        border-radius: 12px !important;
    }

    /* Sidebar Estilo Profesional */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    .status-badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #E0E7FF;
        color: #4338CA;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LÓGICA DE PROCESAMIENTO (Sólida y Profesional)
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

def transformar_informe(archivo_excel):
    # Carga con validación de hojas
    xls = pd.ExcelFile(archivo_excel)
    if "NUEVO" not in xls.sheet_names or "ANTERIOR" not in xls.sheet_names:
        st.error("Error Crítico: El archivo debe contener las pestañas 'NUEVO' y 'ANTERIOR'.")
        st.stop()
        
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
    # Asegurar que existan todas las columnas
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
    
    res = df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).to_dict()
    return res

# =========================================================
# INTERFAZ DE USUARIO (EL LIENZO PRO)
# =========================================================

# --- SIDEBAR (PANEL DE CONTROL) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=80)
    st.markdown("## **DataLogix Pro**")
    st.markdown("---")
    st.markdown("### **Estado del Sistema**")
    st.markdown('<span class="status-badge">Núcleo Activo</span>', unsafe_allow_html=True)
    st.markdown('<span class="status-badge">Motor Heurístico</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.info("""
    **Guía Rápida:**
    1. Cargue el archivo matriz en el Módulo 1.
    2. Adjunte los reportes de bodega correspondientes.
    3. El sistema ejecutará el cruce de cuentas e históricos automáticamente.
    """)

# --- CUERPO PRINCIPAL ---
st.markdown('<h1 style="color:#0F172A; font-weight:800; font-size:2.5rem; margin-bottom:5px;">Centro de Procesamiento</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B; font-size:1.1rem; margin-bottom:40px;">Consolidación Avanzada de Informes de Faltantes v3.1</p>', unsafe_allow_html=True)

# Módulo 1: Archivo Maestro
st.markdown('<div class="section-header">Módulo 01 | Archivo Maestro de Faltantes</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    archivo_principal = st.file_uploader("Cargar Informe Principal (Debe contener hojas 'NUEVO' y 'ANTERIOR')", type=["xlsx"])
    st.markdown('</div>', unsafe_allow_html=True)

# Módulo 2: Ingesta de Bodegas
st.markdown('<div class="section-header" style="margin-top:40px;">Módulo 02 | Inteligencia de Bodegas (Lista de Cuentas)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="module-card">', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        b1 = st.file_uploader("Bodega 1 - Principal", type=["xlsx","xls","csv"])
        b7 = st.file_uploader("Bodega 7 - Satélite", type=["xlsx","xls","csv"])
    with col_b:
        b5 = st.file_uploader("Bodega 5 - Especializada", type=["xlsx","xls","csv"])
        b6 = st.file_uploader("Bodega 6 - Regional", type=["xlsx","xls","csv"])
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="margin-top:50px;"></div>', unsafe_allow_html=True)

# Acción Final
if st.button("EJECUTAR PROCESAMIENTO ANALÍTICO"):
    if archivo_principal is None:
        st.warning("⚠️ Acción bloqueada: Se requiere el Informe Maestro para iniciar.")
    else:
        with st.status("Ejecutando algoritmos de limpieza y cruce...", expanded=True) as status:
            st.write("📖 Analizando estructura de datos...")
            df_final, df_hist = transformar_informe(archivo_principal)
            
            st.write("🔗 Mapeando identificadores de bodega...")
            dict_b1 = procesar_bodega(b1, 1)
            dict_b7 = procesar_bodega(b7, 7)
            dict_b5 = procesar_bodega(b5, 5)
            dict_b6 = procesar_bodega(b6, 6)
            
            st.write("🧪 Aplicando lógica de asignación de cuentas...")
            hist_dict = dict(zip(df_hist["ID"], df_hist["cuenta"]))
            
            # Aplicar lógica final
            for i, row in df_final.iterrows():
                bod = int(row["Bod"])
                id_val = str(bod) + str(row["Codigo"]).strip().upper()
                cuenta = ""
                
                # Reglas directas
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
            status.update(label="✅ Procesamiento Finalizado", state="complete")

        # Resultado Visual
        st.balloons()
        
        # Generar Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
        output.seek(0)
        
        st.success("### Generación Exitosa")
        st.markdown(f"Se han procesado **{len(df_final)}** registros con éxito.")
        
        st.download_button(
            label="📥 DESCARGAR INFORME CONSOLIDADO (XLSX)",
            data=output,
            file_name="CONSOLIDADO_FALTANTES_PRO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
