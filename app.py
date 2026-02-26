import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(page_title="Procesador Integral", layout="wide")
st.title("Procesador Integral de Faltantes y Asignación Completa")

# =====================================================
# FUNCIONES GENERALES
# =====================================================

def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto


def normalizar_columnas(df):
    df.columns = [
        unicodedata.normalize('NFKD', col)
        .encode('ascii', errors='ignore')
        .decode('utf-8')
        .strip()
        .upper()
        for col in df.columns
    ]
    return df


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


# =====================================================
# PROCESAR BODEGA
# =====================================================

def procesar_bodega(file, numero_bodega):
    df = leer_archivo(file)
    if df is None:
        return {}

    df = normalizar_columnas(df)

    col_codigo = next((c for c in df.columns if "COD" in c), None)
    col_nombre = next((c for c in df.columns if "NOM" in c), None)

    if col_codigo is None or col_nombre is None:
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


# =====================================================
# INTERFAZ
# =====================================================

st.subheader("1️⃣ Informe de Faltantes Dispensación")
faltantes_file = st.file_uploader("Cargar Informe", type=["xlsx", "xls", "csv"])

st.subheader("2️⃣ Archivos de Bodega (Opcional)")
b1 = st.file_uploader("Bodega 1", type=["xlsx", "xls", "csv"])
b7 = st.file_uploader("Bodega 7", type=["xlsx", "xls", "csv"])
b5 = st.file_uploader("Bodega 5", type=["xlsx", "xls", "csv"])
b6 = st.file_uploader("Bodega 6", type=["xlsx", "xls", "csv"])


# =====================================================
# PROCESAMIENTO
# =====================================================

if st.button("PROCESAR INFORMACIÓN"):

    if faltantes_file is None:
        st.error("Debe cargar el Informe.")
        st.stop()

    df = leer_archivo(faltantes_file)
    if df is None:
        st.stop()

    df = normalizar_columnas(df)

    # Detectar columnas principales
    col_codigo = next((c for c in df.columns if "COD" in c), None)
    col_bod = next((c for c in df.columns if "BOD" in c), None)
    col_novedad = next((c for c in df.columns if "NOVED" in c), None)

    if col_codigo is None or col_bod is None:
        st.error("No se detectaron columnas Código o Bodega.")
        st.write("Columnas detectadas:", df.columns.tolist())
        st.stop()

    df.rename(columns={
        col_codigo: "CODIGO",
        col_bod: "BOD"
    }, inplace=True)

    df["CODIGO"] = df["CODIGO"].astype(str).str.strip().str.upper()
    df["BOD"] = pd.to_numeric(df["BOD"], errors="coerce").fillna(0).astype(int)

    # =====================================================
    # ASEGURAR COLUMNAS DE SALIDA
    # =====================================================

    columnas_necesarias = [
        "ABASTECIMIENTO",
        "DISPENSACION",
        "ALIADOS",
        "CUENTA",
        "RESPONSABLE"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = ""

    # =====================================================
    # PROCESAR BODEGAS
    # =====================================================

    dict_b1 = procesar_bodega(b1, 1) if b1 else {}
    dict_b7 = procesar_bodega(b7, 7) if b7 else {}
    dict_b5 = procesar_bodega(b5, 5) if b5 else {}
    dict_b6 = procesar_bodega(b6, 6) if b6 else {}

    # =====================================================
    # LÓGICA PRINCIPAL
    # =====================================================

    for i, row in df.iterrows():

        bod = row["BOD"]
        codigo = row["CODIGO"]
        id_val = str(bod) + codigo

        # CUENTA
        if bod == 21:
            df.at[i, "CUENTA"] = "EPM"
        elif bod == 19:
            df.at[i, "CUENTA"] = "UDEA"
        elif bod == 16:
            df.at[i, "CUENTA"] = "HMUA"
        elif bod == 1:
            df.at[i, "CUENTA"] = dict_b1.get(id_val, "")
        elif bod == 7:
            df.at[i, "CUENTA"] = dict_b7.get(id_val, "")
        elif bod == 5:
            df.at[i, "CUENTA"] = dict_b5.get(id_val, "")
        elif bod == 6:
            df.at[i, "CUENTA"] = dict_b6.get(id_val, "")

        # ABASTECIMIENTO
        if col_novedad and pd.notna(row.get(col_novedad)):
            df.at[i, "ABASTECIMIENTO"] = "AGOTADO"

        # DISPENSACION
        if row.get("PENDIENTE", 0) != 0:
            df.at[i, "DISPENSACION"] = "TIENE PENDIENTE"

        # ALIADOS
        if row.get("TRASLADOS", 0) != 0:
            df.at[i, "ALIADOS"] = "REVISAR TRASLADO"

        # RESPONSABLE
        if bod in [1, 7, 5, 6]:
            df.at[i, "RESPONSABLE"] = "BODEGA"
        else:
            df.at[i, "RESPONSABLE"] = "CENTRAL"

    # =====================================================
    # EXPORTAR
    # =====================================================

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.success("Proceso completado correctamente.")

    st.download_button(
        label="Descargar Resultado Final",
        data=output,
        file_name="RESULTADO_FINAL.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
