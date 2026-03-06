import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
import plotly.express as px

# =========================================================
# CONFIGURACIÓN DE PÁGINA (FILOSOFÍA JOBS: MINIMALISMO RADICAL)
# =========================================================
st.set_page_config(
    page_title="DataLogix | Control",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed" # Jobs odia la barra lateral por defecto
)

# --- SISTEMA DE DISEÑO APPLE OBSIDIAN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --apple-blue: #007AFF;
        --apple-gray: #8E8E93;
        --apple-bg: #F5F5F7;
        --datalogix-primary: #1D1D1F;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        background-color: var(--apple-bg);
        color: #1D1D1F;
    }

    /* Contenedores Estilo Glassmorphism (Tarjetas) */
    .apple-card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        height: 100%;
    }
    
    .apple-card:hover {
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
        transform: translateY(-4px);
    }

    /* Títulos Principales (Cambio de Título) */
    .main-title {
        font-weight: 700;
        font-size: 3rem;
        letter-spacing: -2px;
        background: linear-gradient(180deg, #1D1D1F 0%, #434344 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }

    .sub-title {
        color: var(--apple-gray);
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 30px;
    }

    /* Botón Ejecutar Estilo jobs */
    [data-testid="baseButton-secondary"] {
        background: var(--datalogix-primary) !important;
        color: white !important;
        border-radius: 999px !important; /* Totalmente redondeado */
        border: none !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
        width: 100%;
    }
    
    [data-testid="baseButton-secondary"]:hover {
        background: var(--apple-blue) !important;
        box-shadow: 0 6px 20px rgba(0, 122, 255, 0.4);
        transform: scale(1.02);
    }

    /* File Uploader Custom */
    [data-testid="stFileUploader"] {
        border: 2px dashed #D2D2D7 !important;
        border-radius: 16px !important;
        background: white !important;
        padding: 1rem !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--apple-blue) !important;
        background: #F4F9FF !important;
    }

    /* Etiquetas de Sección (Simplificadas) */
    .section-label {
        font-weight: 600;
        color: #1D1D1F;
        font-size: 1.1rem;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .insight-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--apple-gray);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }

    .insight-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1D1D1F;
        line-height: 1.1;
    }

    .planner-badge {
        background: #E8F2FF;
        color: var(--apple-blue);
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Esconder elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# MOTOR LÓGICO Y DE EXTRACCIÓN (INSIGHTS POTENCIADOS)
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

def extraer_insights_premium(archivo):
    """Extrae datos vitales premium para el panel de control"""
    try:
        df_new = pd.read_excel(archivo, sheet_name="NUEVO")
        df_norm_new = normalizar_columnas(df_new.copy())
        
        # Métricas Críticas Originales
        impactos = len(df_new)
        col_prod = "producto" if "producto" in df_norm_new.columns else None
        refs_unicas = df_norm_new["codigo"].nunique() if "codigo" in df_norm_new.columns else 0
        
        col_plan = "pleaneador" if "pleaneador" in df_norm_new.columns else ("planeador" if "planeador" in df_norm_new.columns else None)
        top_planeador = df_norm_new[col_plan].value_counts().idxmax() if col_plan and not df_norm_new[col_plan].empty else "N/D"
        impactos_top_p = df_norm_new[col_plan].value_counts().max() if col_plan else 0
        
        # DATO GANADOR NUEVO: Top 5 Referencias con más pedidos sumados
        col_ref = "codigo" # Asumimos columna normalizada
        col_ped = "numero pedidos" # Asumimos columna normalizada
        
        if col_ref in df_norm_new.columns and col_ped in df_norm_new.columns:
            # Asegurar que pedidos sea numérico y limpiar Nans
            df_norm_new[col_ped] = pd.to_numeric(df_norm_new[col_ped], errors='coerce').fillna(0)
            
            top_5_refs = df_norm_new.groupby(col_ref)[col_ped].sum().reset_index()
            top_5_refs = top_5_refs.sort_values(by=col_ped, ascending=False).head(5)
            # Capitalizar códigos para mostrar
            top_5_refs[col_ref] = top_5_refs[col_ref].str.upper()
        else:
            top_5_refs = pd.DataFrame() # Vacío si no hay columnas

        insights = {
            "total_impactos": impactos,
            "refs_unicas": refs_unicas,
            "top_planeador": str(top_planeador).title(),
            "impactos_top_p": impactos_top_p,
            "top_5_refs_pedidos": top_5_refs # Añadir nuevo insight
        }
        return insights, df_norm_new
    except Exception as e:
        return 0, 0, "Error", 0, pd.DataFrame()

def transformar_informe(archivo_excel):
    # Cargar y normalizar hojas exactas
    df_nuevo = pd.read_excel(archivo_excel, sheet_name="NUEVO")
    df_anterior = pd.read_excel(archivo_excel, sheet_name="ANTERIOR")
    
    df_nuevo = normalizar_columnas(df_nuevo)
    df_anterior = normalizar_columnas(df_anterior)
    
    # IDs y Limpieza (Misma lógica exacta de tu código que funciona)
    df_nuevo["bodega"] = df_nuevo["bodega"].apply(limpiar_valor)
    df_nuevo["codigo"] = df_nuevo["codigo"].apply(limpiar_valor)
    df_nuevo["ID"] = df_nuevo["bodega"] + df_nuevo["codigo"]
    
    df_anterior["bod"] = df_anterior["bod"].apply(limpiar_valor)
    df_anterior["codigo"] = df_anterior["codigo"].apply(limpiar_valor)
    df_anterior["ID"] = df_anterior["bod"] + df_anterior["codigo"]

    # Mapeo basado en tus nombres normalizados
    mapeo = {
        "prioritario": "PRIORITARIO", "bodega": "Bod", "codigo": "Codigo",
        "fecha novedad": "Fecha Novedad", "producto": "Producto",
        "generico": "Generico", "proveedor": "División", "pleaneador": "Planeador",
        "fechaentrega antigua": "Fecha Entrega Pedido", "num pedidos": "Numero Pedidos",
        "pendiente": "Pendiente", "traslado": "Traslados", "solicitud traslado": "Solicitud Traslados",
    }
    df_nuevo = df_nuevo.rename(columns=mapeo)
    
    # Calcular novedades (Simplificado para velocidad, misma lógica de fecha)
    df_nuevo["Fecha Novedad"] = pd.to_datetime(df_nuevo["Fecha Novedad"], dayfirst=True, errors="coerce")
    df_nuevo["Tipo Novedad"] = np.nan
    df_nuevo.loc[df_nuevo["Fecha Novedad"] == pd.Timestamp("6000-01-01"), "Tipo Novedad"] = "Invima"
    df_nuevo.loc[df_nuevo["Fecha Novedad"] == pd.Timestamp("5000-01-01"), "Tipo Novedad"] = "Invima"
    df_nuevo.loc[df_nuevo["Fecha Novedad"] == pd.Timestamp("3000-01-01"), "Tipo Novedad"] = "Descontinuado"
    condicion_agotado = (df_nuevo["Fecha Novedad"].notna() & df_nuevo["Tipo Novedad"].isna())
    df_nuevo.loc[condicion_agotado, "Tipo Novedad"] = "Agotado"
    
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
    for col in col_finales:
        if col not in df_final.columns: df_final[col] = ""
        
    return df_final[col_finales], df_hist

def procesar_bodega(file, num):
    if file is None: return {}
    df = leer_archivo(file)
    if df is None or "Codigo" not in df.columns or "Nombres" not in df.columns: return {}
    
    df["Codigo"] = df["Codigo"].apply(limpiar_valor).astype(str).str.strip().upper()
    
    # Limpieza texto simple idéntica a la tuva
    def limpiar_texto_tuva(texto):
        if pd.isna(texto): return ""
        texto = str(texto).strip().upper()
        texto = unicodedata.normalize('NFKD', texto)
        return ''.join(c for c in texto if not unicodedata.combining(c))
    
    df["Nombres"] = df["Nombres"].apply(limpiar_texto_tuva)
    df["ID"] = str(num) + df["Codigo"]
    
    return df.groupby("ID")["Nombres"].apply(lambda x: ", ".join(sorted(set(x)))).to_dict()

# =========================================================
# INTERFAZ DE USUARIO (EL LIENZO DE JOBS)
# =========================================================

# --- MAIN ---
st.markdown("<h1 class='main-title'>Informe de Faltantes de Dispensación</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Consolidación y Mapeo Inteligente // v3.5 Clean Edition</p>", unsafe_allow_html=True)

# BLOQUE 1: INGESTA MAESTRA (Fondo blanco dashed, limpio)
st.markdown("<div class='section-label'>📄 1. Informe Maestro</div>", unsafe_allow_html=True)
archivo_principal = st.file_uploader("Subir archivo Excel maestro (hojas NUEVO y ANTERIOR)", type=["xlsx"])

# DASHBOARD DE INDICADORES (SOLO DATOS CRÍTICOS)
if archivo_principal:
    try:
        with st.spinner("Sincronizando universos de datos..."):
            insights, df_preview = extraer_metricas_rapidas_ premium(archivo_principal)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3) # Reducir a 3 para limpieza y enfoque

        with col1:
            st.markdown(f"""
            <div class="apple-card">
                <div class="insight-label">Faltantes Totales (Líneas)</div>
                <div class="insight-value">{insights['total_impactos']:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="apple-card">
                <div class="insight-label">Refs. Únicas Afectadas</div>
                <div class="insight-value">{insights['refs_unicas']:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="apple-card">
                <div class="insight-label">Carga Crítica de Planeador</div>
                <div class="insight-value" style="font-size: 1.5rem;">{insights['top_planeador']}</div>
                <span class="planner-badge">{insights['impactos_top_p']} Impactos</span>
            </div>
            """, unsafe_allow_html=True)

        # NUEVO DATO GANADOR: Gráfico de Barras de Top 5 Referencias por Pedidos
        st.markdown("<br>", unsafe_allow_html=True)
        g_col = st.columns(1)[0] # Usar una sola columna ancha para el gráfico
        
        with g_col:
            st.markdown("<div class='apple-card' style='height:400px;'>", unsafe_allow_html=True)
            st.markdown("<p class='insight-label'>Top 5 Referencias con Más Pedidos (Suma)</p>", unsafe_allow_html=True)
            
            top_5_refs_pedidos = insights["top_5_refs_pedidos"]
            if not top_5_refs_pedidos.empty:
                col_ref_n = "codigo" # Nombre de columna normalizado en el DF agrupado
                col_ped_n = "numero pedidos" # Nombre de columna normalizado en el DF agrupado
                
                # Gráfico brutalmente minimalista y directo
                fig_bar_refs = px.bar(
                    top_5_refs_pedidos,
                    x=col_ped_n,
                    y=col_ref_n,
                    orientation='h',
                    color_discrete_sequence=['#1D1D1F'], # Color Obsidian Jobs
                    text=col_ped_n # Mostrar valores sobre las barras
                )
                fig_bar_refs.update_traces(textposition='outside', textfont_size=10, textfont_color='#000000', cliponaxis=False)
                fig_bar_refs.update_layout(
                    margin=dict(t=10, b=10, l=0, r=20),
                    height=320,
                    xaxis_title=None, yaxis_title=None,
                    xaxis_tickfont_color=None, # Quitar números del eje X para limpieza
                    xaxis_showticklabels=False, # Quitar etiquetas del eje X para limpieza
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#000000', font_size=10
                )
                st.plotly_chart(fig_bar_refs, use_container_width=True)
            else:
                st.info("No se encontraron datos válidos de 'Numero Pedidos' para calcular el Top 5 de referencias.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("---")
    except:
        st.error("Error Crítico: El archivo no cumple con el formato maestro (Pestañas NUEVO y ANTERIOR).")

# BLOQUE 2: RED DE BODEGAS (SÍ ESTÁN ABAJO, PERO YA NO SE DESPLEGAN)
st.markdown("<div class='section-label'>🏢 2. Network de Bodegas (Lista de Cuentas)</div>", unsafe_allow_html=True)
# Quitar st.expander() y mostrar cajas directamente
st.markdown("<p style='color:#86868B; font-size:0.9rem; margin-bottom:1rem;'>Sube los reportes satélites para iniciar el cruce de cuentas.</p>", unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    b1 = st.file_uploader("Bodega 1 - Central", type=["xlsx","xls","csv"])
    b7 = st.file_uploader("Bodega 7 - Satélite", type=["xlsx","xls","csv"])
with col_b:
    b5 = st.file_uploader("Bodega 5 - Especializada", type=["xlsx","xls","csv"])
    b6 = st.file_uploader("Bodega 6 - Regional", type=["xlsx","xls","csv"])

# BLOQUE 3: EJECUCIÓN
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("Ejecutar"): # Simplificado "Ejecutar y ya"
    if not archivo_principal:
        st.error("⚠️ Operación bloqueada: Requiere Informe Maestro.")
    else:
        with st.status("Aplicando algoritmos de consolidación...", expanded=True) as status:
            st.write("📖 Analizando estructura base y cruzando históricos...")
            df_final, df_hist = transformar_informe(archivo_principal)
            
            st.write("🔗 Indexando diccionarios de bodegas satélites...")
            dict_b1 = procesar_bodega(b1, 1); dict_b7 = procesar_bodega(b7, 7)
            dict_b5 = procesar_bodega(b5, 5); dict_b6 = procesar_bodega(b6, 6)
            
            st.write("🧪 Ejecutando lógica de asignación final...")
            hist_dict = dict(zip(df_hist["ID"], df_hist["cuenta"]))
            
            # Asignación de cuenta (Lógica exacta que funciona)
            for i, row in df_final.iterrows():
                bod = int(row["Bod"])
                # Aquí se usa la lógica idéntica para generar el ID_VAL
                # (limpiar valor -> strip -> upper -> bodega + codigo)
                codigo_raw = limpiar_valor(row["Codigo"])
                codigo = str(codigo_raw).strip().upper()
                id_val = str(bod) + codigo
                cuenta = ""
                
                # Reglas directas
                if bod == 21: cuenta = "EPM"
                elif bod == 19: cuenta = "UDEA"
                elif bod == 16: cuenta = "HMUA"
                
                # Diccionarios de bodega
                elif bod == 1: cuenta = dict_b1.get(id_val, "")
                elif bod == 7: cuenta = dict_b7.get(id_val, "")
                elif bod == 5: cuenta = dict_b5.get(id_val, "")
                elif bod == 6: cuenta = dict_b6.get(id_val, "")
                
                # Histórico
                if not cuenta or cuenta == "":
                    cuenta = hist_dict.get(id_val, "")
                    
                df_final.at[i, "CUENTA"] = cuenta

            df_final = df_final.drop_duplicates()
            status.update(label="✅ Consolidación Finalizada", state="complete")

        # DESCARGA PREMIUM (Limpia, sin gradientes raros, redondeada)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
        output.seek(0)
        
        st.balloons()
        st.download_button(
            label="Descargar Reporte Final",
            data=output.getvalue(),
            file_name="CONSOLIDADO_FALTANTES_MASTER.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
