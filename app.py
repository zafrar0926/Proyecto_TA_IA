import streamlit as st
import boto3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from io import BytesIO
import random
import uuid
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Configurar app
st.set_page_config(layout="wide", page_title="Fashion Nova App")

# Clientes AWS
lambda_client = boto3.client("lambda", region_name="us-east-1")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tabla = dynamodb.Table('ResenasSentimiento')

# Funciones
def cargar_datos():
    response = tabla.scan()
    df = pd.DataFrame(response['Items'])
    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    return df

def crear_wordcloud(textos):
    texto_completo = " ".join(textos)
    return WordCloud(width=600, height=300, background_color='white', colormap='Set2').generate(texto_completo)

def fig_to_bytes(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    return buf

@st.cache_data
def cargar_dataset_base():
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

# Tabs
tab1, tab2 = st.tabs(["📊 Dashboard", "🧪 Simulador"])

# --- Dashboard ---
with tab1:
    st.markdown("<h1 style='text-align: center; color: black;'>🛍️ Fashion Nova Reviews Monitoring</h1>", unsafe_allow_html=True)
    st.markdown("---")

    if st.button("🔁 Actualizar análisis"):
        st.rerun()

    df = cargar_datos()

    if df.empty:
        st.warning("No hay datos aún.")
    else:
        total_reviews = len(df)
        pos = (df['sentimiento'] == 'POSITIVE').sum()
        neg = (df['sentimiento'] == 'NEGATIVE').sum()
        mixed = (df['sentimiento'] == 'MIXED').sum()

        # Totales
        colA, colB, colC, colD = st.columns([1, 1, 1, 2])
        colA.metric("🔢 Total de reseñas", total_reviews)
        colB.metric("✅ Positivas", pos)
        colC.metric("❌ Negativas", neg)
        colD.metric("⚖️ Mixed", mixed)

        # Marcador
        st.subheader("📍 Tendencia global de sentimiento")
        score = pos - neg
        max_score = max(pos, neg, 1)
        valor = int((score / max_score) * 100)

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=valor,
            title={'text': "Índice de Sentimiento"},
            gauge={
                'axis': {'range': [-100, 100]},
                'bar': {'color': "black"},
                'steps': [
                    {'range': [-100, -10], 'color': "red"},
                    {'range': [-10, 10], 'color': "gray"},
                    {'range': [10, 100], 'color': "green"},
                ],
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Tendencia + distribución
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📈 Tendencia de Reviews Recibidas")

            hoy = pd.to_datetime("today")
            hace_30_dias = hoy - timedelta(days=30)
            df_filtrado = df[df['fecha'] >= hace_30_dias]
            tendencia = df_filtrado.groupby(df_filtrado['fecha'].dt.date).size().reset_index(name='Cantidad')

            fig1, ax1 = plt.subplots(figsize=(6, 3))
            if not tendencia.empty:
                sns.lineplot(data=tendencia, x='fecha', y='Cantidad', ax=ax1, marker="o")
                ax1.set_xlim(tendencia['fecha'].min(), tendencia['fecha'].max())
            else:
                ax1.text(0.5, 0.5, "Sin datos recientes", ha='center')
            ax1.set_xlabel("Fecha")
            ax1.set_ylabel("Cantidad")
            ax1.tick_params(axis='x', rotation=45)
            st.pyplot(fig1)

        with col_g2:
            st.subheader("📊 Distribución de Sentimientos por Canal")
            conteo = df.groupby(['canal', 'sentimiento']).size().reset_index(name='conteo')
            fig2, ax2 = plt.subplots(figsize=(6, 3))
            sns.barplot(data=conteo, x='canal', y='conteo', hue='sentimiento', ax=ax2)
            ax2.set_ylabel("Cantidad")
            st.pyplot(fig2)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🟩 Positivas recientes")
            st.dataframe(df[df['sentimiento'] == 'POSITIVE'].sort_values(by='fecha', ascending=False).head(5)[['fecha', 'canal', 'texto']])
        with col2:
            st.markdown("### 🟥 Negativas recientes")
            st.dataframe(df[df['sentimiento'] == 'NEGATIVE'].sort_values(by='fecha', ascending=False).head(5)[['fecha', 'canal', 'texto']])

        st.subheader("☁️ Palabras más comunes")
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        wordcloud = crear_wordcloud(df['texto'].dropna().astype(str))
        ax3.imshow(wordcloud, interpolation='bilinear')
        ax3.axis('off')
        st.pyplot(fig3)

# --- Simulador ---
with tab2:
    st.markdown("<h1 style='text-align: center; color: black;'>🧪 Simulador de Reviews</h1>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("✍️ Ingresar mensaje como usuario externo")
    with st.form(key="manual_form"):
        texto = st.text_area("Escribe aquí la reseña:")
        canal = st.selectbox("Selecciona el canal:", ["web", "movil", "call_center", "redes_sociales"])
        submit_manual = st.form_submit_button("📤 Enviar reseña manual")

        if submit_manual and texto.strip() != "":
            payload = {"texto": texto.strip(), "canal": canal}
            respuesta = lambda_client.invoke(
                FunctionName='AnalizarSentimiento',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload).encode('utf-8')
            )
            result = json.loads(respuesta['Payload'].read())
            st.success(f"Sentimiento detectado: {result.get('sentimiento', 'N/A')}")

    st.markdown("---")
    st.subheader("🎲 Simular envío desde reseñas reales")

    base_df = cargar_dataset_base()
    num_mensajes = st.slider("Número de reseñas a enviar:", min_value=1, max_value=20, value=5)
    if st.button("🚀 Enviar mensajes simulados"):
        muestras = base_df.sample(num_mensajes)
        resultados = []
        for _, fila in muestras.iterrows():
            payload = {
                "texto": str(fila["Review Text"]),
                "canal": random.choice(["web", "movil", "call_center", "redes_sociales"])
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

