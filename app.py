import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(page_title="Procesador Integral", layout="wide")
st.title("Procesador Integral de Faltantes y Asignación de Cuenta")

# ===============================
# LIMPIEZA TEXTO
# ===============================

def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto


# ===============================
# LECTURA ROBUSTA STREAMLIT
# ===============================

def leer_archivo(file):
    try:
        file.seek(0)
        if file.name.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(file, engine="openpyxl")
        elif file.name.lower().endswith(".csv"):
            try:
                return pd.read_csv(file, encoding="utf-8")
            except:
                file.seek(0)
                return pd.read_csv(file, encoding="latin1")
        else:
            st.error("Formato no soportado.")
            return None
    except Exception as e:
        st.error(f"Error leyendo archivo: {e}")
        return None


# ===============================
# PROCESAR BODEGA
# ===============================

def procesar_bodega(file, numero_bodega):
    df = leer_archivo(file)
    if df is None:
        return {}

    # Normalizar columnas
    df.columns = [
        unicodedata.normalize('NFKD', col)
        .encode('ascii', errors='ignore')
        .decode('utf-8')
        .strip()
        .upper()
        for col in df.columns
    ]

    # Detectar columnas necesarias
    col_codigo = next((c for c in df.columns if "COD" in c), None)
    col_nombre = next((c for c in df.columns if "NOM" in c), None)

    if col_codigo is None or col_nombre is None:
        st.error(f"Bodega {numero_bodega} no contiene columnas válidas de Código o Nombre.")
        return {}

    df[col_codigo] = df[col_codigo].astype(str).str.strip().str.upper()
    df[col_nombre] = df[col_nombre].apply(limpiar_texto)

    df["ID"] = str(numero_bodega) + df[col_codigo]

    consolidado = (
        df.groupby("ID")[col_nombre]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
    )

    return dict(zip(consolidado["ID"], consolidado[col_nombre]))


# ===============================
# INTERFAZ
# ===============================

st.subheader("1️⃣ Cargar Informe de Faltantes Dispensación")
faltantes_file = st.file_uploader("Informe de Faltantes", type=["xlsx", "xls", "csv"])

st.subheader("2️⃣ Cargar Archivos de Bodega (Opcional)")
b1 = st.file_uploader("Bodega 1", type=["xlsx", "xls", "csv"])
b7 = st.file_uploader("Bodega 7", type=["xlsx", "xls", "csv"])
b5 = st.file_uploader("Bodega 5", type=["xlsx", "xls", "csv"])
b6 = st.file_uploader("Bodega 6", type=["xlsx", "xls", "csv"])


# ===============================
# PROCESAMIENTO
# ===============================

if st.button("PROCESAR INFORMACIÓN"):

    if faltantes_file is None:
        st.error("Debe cargar el Informe de Faltantes.")
        st.stop()

    df_final = leer_archivo(faltantes_file)

    if df_final is None:
        st.stop()

    # ===============================
    # NORMALIZAR COLUMNAS
    # ===============================

    df_final.columns = [
        unicodedata.normalize('NFKD', col)
        .encode('ascii', errors='ignore')
        .decode('utf-8')
        .strip()
        .upper()
        for col in df_final.columns
    ]

    # Detectar columnas clave
    col_codigo = next((c for c in df_final.columns if "COD" in c), None)
    col_bod = next((c for c in df_final.columns if "BOD" in c), None)

    if col_codigo is None or col_bod is None:
        st.error("No se encontraron columnas de Código o Bodega.")
        st.write("Columnas detectadas:", df_final.columns.tolist())
        st.stop()

    # Renombrar internamente
    df_final.rename(columns={
        col_codigo: "CODIGO",
        col_bod: "BOD"
    }, inplace=True)

    df_final["CODIGO"] = df_final["CODIGO"].astype(str).str.strip().str.upper()
    df_final["BOD"] = df_final["BOD"].astype(int)
    df_final["CUENTA"] = ""

    # ===============================
    # REGLA NOVEDAD
    # ===============================

    col_novedad = next((c for c in df_final.columns if "NOVED" in c), None)

    if col_novedad:
        df_final["NOVEDAD_FINAL"] = df_final[col_novedad].apply(
            lambda x: "AGOTADO" if pd.notna(x) else ""
        )

    # ===============================
    # PROCESAR BODEGAS
    # ===============================

    dict_b1 = procesar_bodega(b1, 1) if b1 else {}
    dict_b7 = procesar_bodega(b7, 7) if b7 else {}
    dict_b5 = procesar_bodega(b5, 5) if b5 else {}
    dict_b6 = procesar_bodega(b6, 6) if b6 else {}

    # ===============================
    # ASIGNAR CUENTA
    # ===============================

    for i, row in df_final.iterrows():
        bod = row["BOD"]
        codigo = row["CODIGO"]
        id_val = str(bod) + codigo

        if bod == 21:
            df_final.at[i, "CUENTA"] = "EPM"
        elif bod == 19:
            df_final.at[i, "CUENTA"] = "UDEA"
        elif bod == 16:
            df_final.at[i, "CUENTA"] = "HMUA"
        elif bod == 1:
            df_final.at[i, "CUENTA"] = dict_b1.get(id_val, "")
        elif bod == 7:
            df_final.at[i, "CUENTA"] = dict_b7.get(id_val, "")
        elif bod == 5:
            df_final.at[i, "CUENTA"] = dict_b5.get(id_val, "")
        elif bod == 6:
            df_final.at[i, "CUENTA"] = dict_b6.get(id_val, "")

    # ===============================
    # EXPORTAR RESULTADO
    # ===============================

    output = io.BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)

    st.success("Proceso completado correctamente.")

    st.download_button(
        label="Descargar Resultado Final",
        data=output,
        file_name="RESULTADO_FINAL.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
