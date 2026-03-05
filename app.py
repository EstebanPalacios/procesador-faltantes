import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
import io
 
st.set_page_config(page_title="Informe Faltantes Profesional", layout="wide")
st.title("Procesador Informe de Faltantes de Dispensación")
 
# =========================================================
# FUNCIONES BASE
# =========================================================
 
def normalizar_texto(texto):
    if not isinstance(texto, str):
        return texto
 
    texto = texto.strip().lower()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = re.sub(r'[^a-z0-9 ]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
 
    return texto.strip()
 
 
def normalizar_columnas(df):
    df.columns = [normalizar_texto(col) for col in df.columns]
    return df
 
 
def limpiar_valor(valor):
    if pd.isna(valor):
        return ""
    valor = str(valor)
    valor = valor.replace(".0", "")
    valor = valor.strip()
    return valor
 
 
def crear_id(df, col_bodega, col_codigo):
    df[col_bodega] = df[col_bodega].apply(limpiar_valor)
    df[col_codigo] = df[col_codigo].apply(limpiar_valor)
    df["ID"] = df[col_bodega] + df[col_codigo]
    return df
 
def calcular_tipo_novedad(df, columna_fecha):

    # Guardar valor original como texto
    texto_original = df[columna_fecha].astype(str).str.lower()

    # Convertir fecha
    df[columna_fecha] = pd.to_datetime(
        df[columna_fecha],
        dayfirst=True,
        errors="coerce"
    )

    df["Tipo Novedad"] = np.nan

    # ------------------------------------------------
    # 1️⃣ SI EL TEXTO DICE DESCONTINUADO
    # ------------------------------------------------
    mask_descontinuado_texto = texto_original.str.contains("descontinuado", na=False)

    df.loc[mask_descontinuado_texto, "Tipo Novedad"] = "Descontinuado"

    # ------------------------------------------------
    # 2️⃣ REGLAS POR FECHA ESPECIAL
    # ------------------------------------------------
    df.loc[df[columna_fecha] == pd.Timestamp("6000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("5000-01-01"), "Tipo Novedad"] = "Invima"
    df.loc[df[columna_fecha] == pd.Timestamp("3000-01-01"), "Tipo Novedad"] = "Descontinuado"

    # ------------------------------------------------
    # 3️⃣ SI TIENE FECHA Y NO ES NADA → AGOTADO
    # ------------------------------------------------
    condicion_agotado = (
        df[columna_fecha].notna() &
        df["Tipo Novedad"].isna()
    )

    df.loc[condicion_agotado, "Tipo Novedad"] = "Agotado"

    return df
 
# =========================================================
# LECTURA
# =========================================================
 
def leer_archivo(file):
    file.seek(0)
    if file.name.endswith(".xlsx"):
        return pd.read_excel(file, engine="openpyxl")
    elif file.name.endswith(".xls"):
        return pd.read_excel(file)
    elif file.name.endswith(".csv"):
        for encoding in ["utf-8", "latin1", "cp1252"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=encoding)
            except:
                continue
        raise ValueError("No se pudo leer CSV.")
    else:
        raise ValueError("Formato no soportado.")
 
 
# =========================================================
# TRANSFORMACIÓN PRINCIPAL
# =========================================================
 
def transformar_informe(archivo_excel):
 
    df_nuevo = pd.read_excel(archivo_excel, sheet_name="NUEVO")
    df_anterior = pd.read_excel(archivo_excel, sheet_name="ANTERIOR")
 
    df_nuevo = normalizar_columnas(df_nuevo)
    df_anterior = normalizar_columnas(df_anterior)
 
    df_nuevo = crear_id(df_nuevo, "bodega", "codigo")
    df_anterior = crear_id(df_anterior, "bod", "codigo")
 
    mapeo = {
        "prioritario": "PRIORITARIO",
        "bodega": "Bod",
        "codigo": "Codigo",
        "fecha novedad": "Fecha Novedad",
        "producto": "Producto",
        "generico": "Generico",
        "proveedor": "División",
        "pleaneador": "Planeador",
        "fechaentrega antigua": "Fecha Entrega Pedido",
        "num pedidos": "Numero Pedidos",
        "pendiente": "Pendiente",
        "traslado": "Traslados",
        "solicitud traslado": "Solicitud Traslados",
    }
 
    df_nuevo = df_nuevo.rename(columns=mapeo)
 
    df_nuevo = calcular_tipo_novedad(df_nuevo, "Fecha Novedad")
 
    if "cuenta" not in df_anterior.columns:
        df_anterior["cuenta"] = ""
 
    columnas_hist = ["ID", "abastecimiento", "dispensacion", "aliados", "responsable", "cuenta"]
    df_hist = df_anterior[columnas_hist].copy()
 
    df_final = df_nuevo.merge(df_hist, on="ID", how="left")
 
    df_final["CUENTA"] = ""
 
    columnas_finales = [
        "ID","PRIORITARIO","Bod","Codigo","Fecha Novedad",
        "Producto","Generico","División","Planeador",
        "Fecha Entrega Pedido","Numero Pedidos",
        "Pendiente","Traslados","Solicitud Traslados",
        "Tipo Novedad","abastecimiento","dispensacion",
        "aliados","CUENTA","responsable"
    ]
 
    df_final = df_final[columnas_finales]
 
    return df_final, df_hist
 
 
# =========================================================
# PROCESAR BODEGAS
# =========================================================
 
def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto
 
 
def procesar_bodega(file, numero_bodega):
 
    if file is None:
        return {}
 
    df = leer_archivo(file)
 
    df["Codigo"] = df["Codigo"].apply(limpiar_valor)
    df["Codigo"] = df["Codigo"].astype(str).str.strip().str.upper()
    df["Nombres"] = df["Nombres"].apply(limpiar_texto)
 
    df["ID"] = str(numero_bodega) + df["Codigo"]
 
    consolidado = (
        df.groupby("ID")["Nombres"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
    )
 
    return dict(zip(consolidado["ID"], consolidado["Nombres"]))
 
 
# =========================================================
# ASIGNACIÓN DE CUENTA CON RESPALDO HISTÓRICO
# =========================================================
 
def asignar_cuenta(df_final, df_hist, dict_b1, dict_b7, dict_b5, dict_b6):
 
    hist_dict = dict(zip(df_hist["ID"], df_hist["cuenta"]))
 
    for i, row in df_final.iterrows():
 
        bod = int(row["Bod"])
        codigo = limpiar_valor(row["Codigo"])
        codigo = str(codigo).strip().upper()
 
        id_val = str(bod) + codigo
        cuenta = ""
 
        if bod == 21:
            cuenta = "EPM"
        elif bod == 19:
            cuenta = "UDEA"
        elif bod == 16:
            cuenta = "HMUA"
        elif bod == 1:
            cuenta = dict_b1.get(id_val, "")
        elif bod == 7:
            cuenta = dict_b7.get(id_val, "")
        elif bod == 5:
            cuenta = dict_b5.get(id_val, "")
        elif bod == 6:
            cuenta = dict_b6.get(id_val, "")
 
        # 🔥 SI NO ENCUENTRA EN BODEGA → BUSCAR EN HISTÓRICO
        if cuenta == "":
            cuenta = hist_dict.get(id_val, "")
 
        df_final.at[i, "CUENTA"] = cuenta
 
    return df_final
 
 
# =========================================================
# INTERFAZ
# =========================================================
 
st.subheader("1️⃣ CARGAR INFORME DE FALTANTES DISPENSACIÓN")
archivo_principal = st.file_uploader("Informe principal", type=["xlsx"])
 
st.subheader("2️⃣ CARGAR PEDIDOS DE BODEGAS  (BUSQUEDA DE CUENTAS)")
b1 = st.file_uploader("Bodega 1", type=["xlsx","xls","csv"])
b7 = st.file_uploader("Bodega 7", type=["xlsx","xls","csv"])
b5 = st.file_uploader("Bodega 5", type=["xlsx","xls","csv"])
b6 = st.file_uploader("Bodega 6", type=["xlsx","xls","csv"])
 
if st.button("PROCESAR INFORME COMPLETO"):
 
    if archivo_principal is None:
        st.error("Debe cargar el informe principal.")
        st.stop()
 
    df_final, df_hist = transformar_informe(archivo_principal)
 
    dict_b1 = procesar_bodega(b1, 1)
    dict_b7 = procesar_bodega(b7, 7)
    dict_b5 = procesar_bodega(b5, 5)
    dict_b6 = procesar_bodega(b6, 6)
 
    df_final = asignar_cuenta(df_final, df_hist, dict_b1, dict_b7, dict_b5, dict_b6)
 
    # 🔥 ELIMINAR REGISTROS COMPLETAMENTE IDÉNTICOS
    df_final = df_final.drop_duplicates()
 
    output = io.BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)
 
    st.success("Proceso finalizado correctamente.")
 
    st.download_button(
        label="Descargar RESULTADO_FINAL_CON_CUENTA.xlsx",
        data=output,
        file_name="RESULTADO_FINAL_CON_CUENTA.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
