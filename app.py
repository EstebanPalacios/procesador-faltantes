import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import time

# =========================================================
# CONFIGURACIÓN PREMIUM (ALTO NIVEL)
# =========================================================
st.set_page_config(
    page_title="DataLogix Pro | Inteligencia Logística",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE DISEÑOFluent/Fluent UI + Glassmorphism ---
st.markdown("""
    <style>
    /* Importar tipografía premium geométrica */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #F8FAFC; /* Gris ultra-pálido técnico */
    }

    /* Títulos Principales con Degradado Elegantísimo */
    .main-title {
        background: linear-gradient(135deg, #007AFF 0%, #34C759 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 900;
        letter-spacing: -2px;
        margin-bottom: 0px;
        text-align: center;
    }
    
    .sub-title {
        color: #64748B;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 50px;
    }

    /* Módulos Glassmorphism (Tarjetas que flotan) */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
        transition: all 0.5s cubic-bezier(0.165, 0.84, 0.44, 1);
        margin-bottom: 25px;
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0, 122, 255, 0.08);
        border-color: rgba(0, 122, 255, 0.2);
    }

    /* Headers de Sección Técnicos y Limpios */
    .section-label {
        color: #1E293B;
        font-size: 0.95rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .section-label::before {
        content: "";
        width: 30px;
        height: 3px;
        background: linear-gradient(90deg, #007AFF, #34C759);
        border-radius: 99px;
    }

    /* Botón Maestro Inspirador */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #007AFF 0%, #00CFFF 100%);
        color: white !important;
        border-radius: 12px;
        padding: 20px;
        font-weight: 700;
        border: none;
        letter-spacing: 1px;
        font-size: 1.1rem;
        text-transform: uppercase;
        box-shadow: 0 10px 20px rgba(0, 122, 255, 0.2);
        transition: all 0.4s ease;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #34C759 0%, #007AFF 100%);
        box-shadow: 0 15px 30px rgba(52, 199, 89, 0.3);
        transform: scale(1.02);
    }

    /* Personalización File Uploaders */
    .stFileUploader section {
        background-color: #FFFFFF !important;
        border: 2px dashed #CBD5E1 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }
    .stFileUploader section:hover {
        border-color: #007AFF !important;
        background-color: #F0F9FF !important;
    }

    /* Sidebar Refinado */
    [data-testid="stSidebar"] {
        background-color: rgba(248, 250, 252, 0.9);
        backdrop-filter: blur(10px);
        border-right: 1px solid #E2E8F0;
    }
    
    /* Previsualización rápida de datos */
    .precompute-card {
        padding: 20px;
        border-radius: 15px;
        background: #F0F9FF;
        border-left: 5px solid #007AFF;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LÓGICA DE PROCESAMIENTO (Sólida e Inalterada)
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
    ext = file.name.split('.')[-1].lower()
    if ext == "xlsx": return pd.read_excel(file, engine="openpyxl")
    elif ext == "xls": return pd.read_excel(file)
    elif ext == "csv":
        for encoding in ["utf-8", "latin1", "cp1252"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=encoding)
            except: continue
    return None

def transformar_informe(archivo_excel):
    xls = pd.ExcelFile(archivo_excel)
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
    col_finales = ["ID","PRIORITARIO","Bod","Codigo","Fecha Novedad","Producto","Generico","División","Planeador","Fecha Entrega Pedido","Numero Pedidos","Pendiente","Traslados","Solicitud Traslados","Tipo Novedad","abastecimiento","dispensacion","aliados","CUENTA","responsable"]
    for col in col_finales:
        if col not in df_final.columns: df_final[col] = ""
        
    return df_final[col_finales], df_hist

def procesar_bodega(file, num):
    if file is None: return {}
    df = leer_archivo(file)
    if df is None: return {}
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().upper()
    df["Nombres"] = df["Nombres"].fillna("").astype(str).str.strip().upper()
    df["ID"] = str(num) + df["Codigo"]
    consolidado = df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
    return dict(zip(consolidado["ID"], consolidado["Nombres"]))

# =========================================================
# INTERFAZ DE USUARIO (EL LIENZO INSPIRADOR)
# =========================================================

# --- SIDEBAR ELGANTE ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=70)
    st.markdown("## **DataLogix Pro**")
    st.markdown("---")
    st.info("""
    **Guía Rápida:**
    1. Cargue el archivo matriz en el Módulo 1.
    2. Adjunte los reportes de bodega correspondientes.
    3. El sistema ejecutará el cruce de cuentas e históricos automáticamente.
    """)
    st.markdown("---")
    st.markdown("<p style='color:#64748B; font-size:0.8rem;'>Motor v3.1 | Grado Industrial</p>", unsafe_allow_html=True)

# --- CUERPO PRINCIPAL ---
st.markdown('<p class="main-title">Centro de Procesamiento</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Inteligencia y Consolidación de Faltantes de Dispensación</p>', unsafe_allow_html=True)

# Módulo 1: Archivo Maestro
st.markdown('<div class="section-label">Módulo 1 // Archivo Maestro de Faltantes</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    archivo_principal = st.file_uploader("Arrastre el Informe Principal (Debe contener hojas 'NUEVO' y 'ANTERIOR')", type=["xlsx"])
    
    # Pre-cómputo y dato ganador instantáneo si se sube el archivo
    if archivo_principal:
        try:
            with st.spinner('Analizando estructura base...'):
                time.sleep(1) # Sensación de trabajo premium
                xl_preview = pd.ExcelFile(archivo_principal)
                df_n = xl_preview.parse('NUEVO')
                impactos = len(df_n)
                st.markdown(f'<div class="precompute-card">✅ Archivo Matriz detectado. <b>{impactos:,}</b> impactos a procesar en pestaña NUEVO. Listo para consolidar.</div>', unsafe_allow_html=True)
        except:
            st.error("Error al previsualizar. Asegúrese de que el archivo tenga las hojas 'NUEVO' y 'ANTERIOR'.")
    st.markdown('</div>', unsafe_allow_html=True)

# Módulo 2: Ingesta de Bodegas
st.markdown('<div class="section-label" style="margin-top:40px;">Módulo 2 // Network de Bodegas (Lista de Cuentas)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        b1 = st.file_uploader("Bodega 1 - Principal", type=["xlsx","xls","csv"], key="b1_uploader")
        b7 = st.file_uploader("Bodega 7 - Satélite", type=["xlsx","xls","csv"], key="b7_uploader")
    with col_b:
        b5 = st.file_uploader("Bodega 5 - Especializada", type=["xlsx","xls","csv"], key="b5_uploader")
        b6 = st.file_uploader("Bodega 6 - Regional", type=["xlsx","xls","csv"], key="b6_uploader")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="margin-top:60px;"></div>', unsafe_allow_html=True)

# Acción Final
if st.button("🚀 EJECUTAR CONSOLIDACIÓN DE DATOS"):
    if archivo_principal is None:
        st.warning("⚠️ Acción bloqueada: Se requiere el Informe Maestro para iniciar.")
    else:
        with st.status("Aplicando algoritmos de consolidación y cruce...", expanded=True) as status:
            time.sleep(1)
            
            st.write("Sincronizando Módulos y Pestañas base...")
            df_final, df_hist = transformar_informe(archivo_principal)
            
            st.write("🔗 Mapeando identificadores de Network de Bodegas...")
            dict_b1 = procesar_bodega(b1, 1); dict_b7 = procesar_bodega(b7, 7)
            dict_b5 = procesar_bodega(b5, 5); dict_b6 = procesar_bodega(b6, 6)
            
            st.write("🧪 Ejecutando lógica heurística de asignación de cuentas...")
            hist_dict = dict(zip(df_hist["ID"], df_hist["cuenta"]))
            
            for i, row in df_final.iterrows():
                bod = int(row["Bod"])
                id_val = str(bod) + str(row["Codigo"]).strip().upper()
                cuenta = ""
                
                # Reglas directas e históricas
                if bod == 21: cuenta = "EPM"
                elif bod == 19: cuenta = "UDEA"
                elif bod == 16: cuenta = "HMUA"
                elif bod == 1: cuenta = dict_b1.get(id_val, "")
                elif bod == 7: cuenta = dict_b7.get(id_val, "")
                elif bod == 5: cuenta = dict_b5.get(id_val, "")
                elif bod == 6: cuenta = dict_b6.get(id_val, "")
                
                if not cuenta or cuenta == "": cuenta = hist_dict.get(id_val, "")
                df_final.at[i, "CUENTA"] = cuenta

            df_final = df_final.drop_duplicates()
            status.update(label="✅ Sincronización Finalizada", state="complete")

        # Resultado Visual
        st.balloons()
        
        # Generar Excel Premium en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
        output.seek(0)
        
        st.success(f"## {len(df_final):,} Impactos Procesados Exitosamente")
        
        c_final, c_spacer = st.columns([2, 3])
        with c_final:
            st.download_button(
                label="📥 DESCARGAR INFORME CONSOLIDADO (v3.1)",
                data=output,
                file_name="CONSOLIDADO_FALTANTES_PRO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
