import streamlit as st
import pandas as pd
import random
import uuid
from datetime import datetime
import boto3
import json

# Configurar cliente Lambda
lambda_client = boto3.client("lambda", region_name="us-east-1")

# Cargar dataset base
@st.cache_data
def cargar_dataset():
    df = pd.read_csv("fashionnova_reviews.csv")
    def procesar_rating(r):
        try:
            return int(r.split()[1])
        except:
            return None
    df["rating_num"] = df["Rating"].apply(procesar_rating)
    df = df[df["Review Text"].notna()]
    df = df[df["rating_num"].notna()]
    return df

df = cargar_dataset()

st.set_page_config(layout="wide", page_title="Simulador de Envío de Reviews")

st.title("🧪 Simulador de Reviews de Usuarios")

st.markdown("---")

# Sección 1: Ingreso manual de mensaje
st.subheader("✍️ Ingresar mensaje como usuario externo")

with st.form(key="manual_form"):
    texto = st.text_area("Escribe aquí la reseña:")
    canal = st.selectbox("Selecciona el canal:", ["web", "movil", "call_center", "redes_sociales"])
    submit_manual = st.form_submit_button("📤 Enviar reseña manual")

    if submit_manual and texto.strip() != "":
        payload = {
            "texto": texto.strip(),
            "canal": canal
        }
        respuesta = lambda_client.invoke(
            FunctionName='AnalizarSentimiento',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode('utf-8')
        )
        result = json.loads(respuesta['Payload'].read())
        st.success(f"Sentimiento detectado: {result.get('sentimiento', 'N/A')}")

st.markdown("---")

# Sección 2: Simular envío desde dataset real
st.subheader("🎲 Simular envío desde reseñas reales")

num_mensajes = st.slider("Número de reseñas a enviar:", min_value=1, max_value=20, value=5)
canales = ["web", "movil", "call_center", "redes_sociales"]

if st.button("🚀 Enviar mensajes simulados"):
    muestras = df.sample(num_mensajes)
    resultados = []
    for _, fila in muestras.iterrows():
        payload = {
            "texto": str(fila["Review Text"]),
            "canal": random.choice(canales)
        }
        respuesta = lambda_client.invoke(
            FunctionName='AnalizarSentimiento',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode('utf-8')
        )
        result = json.loads(respuesta['Payload'].read())
        resultados.append({
            "texto": payload["texto"][:80] + "...",
            "canal": payload["canal"],
            "sentimiento": result.get("sentimiento", "N/A")
        })
    st.success(f"{num_mensajes} mensajes enviados exitosamente.")
    st.dataframe(pd.DataFrame(resultados))
