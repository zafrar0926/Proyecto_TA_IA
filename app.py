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
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
ses = boto3.client("ses", region_name="us-east-1")

# Funciones auxiliares
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

def construir_prompt_para_llm(df_negativas):
    reseñas = df_negativas['texto'].tolist()
    resumen = "\n".join(f"- {r}" for r in reseñas[:10])
    prompt = (
        "Eres un experto en experiencia del cliente.\n"
        "A continuación se presentan reseñas negativas reales:\n\n"
        f"{resumen}\n\n"
        "Resume los problemas clave y propone 3 acciones estratégicas para mejorar la satisfacción del cliente."
    )
    return prompt

def obtener_respuesta_llm(prompt):
    body = {
        "prompt": f"\n\nHuman:\n{prompt}\n\nAssistant:",
        "max_tokens_to_sample": 800,
        "temperature": 0.7,
    }
    response = bedrock.invoke_model(
        modelId="anthropic.claude-v2",
        body=json.dumps(body),
        contentType="application/json"
    )
    resultado = json.loads(response['body'].read())
    return resultado['completion']

def enviar_informe_por_correo(texto, destinatario):
    ses.send_email(
        Source="santiagoz0926@gmail.com",  # tu correo verificado
        Destination={"ToAddresses": [destinatario]},
        Message={
            "Subject": {"Data": "Informe de reseñas críticas - Fashion Nova"},
            "Body": {
                "Html": {
                    "Data": f"""
                    <html>
                    <body>
                        <p style="font-family:Arial, sans-serif; font-size:14px;">
                        Estimado equipo,<br><br>
                        A continuación encontrará el informe generado automáticamente a partir del análisis de las reseñas más críticas de clientes:<br><br>
                        <blockquote style="color:#555;">{texto}</blockquote>
                        <br>
                        <p>Para cualquier duda o sugerencia, no dude en contactarnos.</p>
                        <br>
                        <p>Atentamente,<br>
                        Héctor, Anderson, Jorge y Santiago<br>
                        <span style="font-size:12px;color:#888;">Equipo de Análisis Fashion Nova</span>
                        </p>
                        </p>
                    </body>
                    </html>
                    """
                }
            }
        }
    )


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

        colA, colB, colC, colD = st.columns([1, 1, 1, 2])
        colA.metric("🔢 Total de reseñas", total_reviews)
        colB.metric("✅ Positivas", pos)
        colC.metric("❌ Negativas", neg)
        colD.metric("⚖️ Mixed", mixed)

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

        st.subheader("📨 Generar Informe Estratégico con LLM")
        destinatario = st.text_input("Correo destino (verificado en SES):")
        if st.button("Generar y Enviar Informe"):
            df_negativas = df[df['sentimiento'] == 'NEGATIVE'].sort_values(by='fecha', ascending=False)
            if df_negativas.empty:
                st.warning("No hay reseñas negativas disponibles para generar el informe.")
            else:
                with st.spinner("Generando informe con LLM..."):
                    prompt = construir_prompt_para_llm(df_negativas)
                    informe = obtener_respuesta_llm(prompt)
                    enviar_informe_por_correo(informe, destinatario)
                st.success("Informe generado y enviado por correo correctamente.")
