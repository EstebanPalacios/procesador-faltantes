import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(page_title="Procesador Integral de Faltantes", layout="wide")
st.title("Procesador Integral de Informe de Faltantes y Asignación de Cuenta")

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
# LECTURA ROBUSTA
# ===============================

def leer_archivo(file):
    try:
        return pd.read_excel(file, engine="openpyxl")
    except:
        try:
            return pd.read_csv(file, encoding="utf-8")
        except:
            return pd.read_csv(file, encoding="latin1")


# ===============================
# PROCESAR BODEGAS
# ===============================

def procesar_bodega(file, numero_bodega):
    df = leer_archivo(file)
    df["Codigo"] = df["Codigo"].astype(str).str.strip().str.upper()
    df["Nombres"] = df["Nombres"].apply(limpiar_texto)
    df["ID"] = str(numero_bodega) + df["Codigo"]

    consolidado = (
        df.groupby("ID")["Nombres"]
        .apply(lambda x: ", ".join(sorted(set(x))))
        .reset_index()
    )

    return dict(zip(consolidado["ID"], consolidado["Nombres"]))


# ===============================
# INTERFAZ
# ===============================

st.subheader("1️⃣ Cargar Informe de Faltantes Dispensación")
faltantes_file = st.file_uploader("Informe de Faltantes", type=["xlsx", "xls", "csv"])

st.subheader("2️⃣ Cargar Archivo Principal Base")
principal_file = st.file_uploader("Archivo Principal", type=["xlsx", "xls", "csv"])

st.subheader("3️⃣ Cargar Archivos de Bodega (Opcional)")
b1 = st.file_uploader("Bodega 1", type=["xlsx", "xls", "csv"])
b7 = st.file_uploader("Bodega 7", type=["xlsx", "xls", "csv"])
b5 = st.file_uploader("Bodega 5", type=["xlsx", "xls", "csv"])
b6 = st.file_uploader("Bodega 6", type=["xlsx", "xls", "csv"])


# ===============================
# PROCESAMIENTO
# ===============================

if st.button("PROCESAR INFORMACIÓN"):

    if faltantes_file is None or principal_file is None:
        st.error("Debe cargar el Informe de Faltantes y el Archivo Principal.")
    else:
        df_faltantes = leer_archivo(faltantes_file)
        df_final = leer_archivo(principal_file)

        # Limpieza clave
        df_final["Codigo"] = df_final["Codigo"].astype(str).str.strip().str.upper()
        df_final["Bod"] = df_final["Bod"].astype(int)
        df_final["CUENTA"] = ""

        # ===============================
        # REGLA NOVEDAD
        # ===============================

        if "Fecha Novedad" in df_final.columns:
            df_final["NOVEDAD_FINAL"] = df_final["Fecha Novedad"].apply(
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
            bod = row["Bod"]
            codigo = str(row["Codigo"]).strip().upper()
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
            file_name="RESULTADO_FINAL_INTEGRADO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
