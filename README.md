# 🛍️ Fashion Nova Reviews Monitoring - Proyecto de Analítica e IA

Este repositorio contiene el desarrollo de una **plataforma inteligente para monitoreo de reseñas de clientes**, usando servicios de AWS, modelos LLM, y una interfaz en Streamlit con observabilidad en Grafana y Prometheus.

---

## 🧠 Descripción del Proyecto
El sistema permite simular y analizar en tiempo real reseñas de clientes de la marca *Fashion Nova*, clasificarlas automáticamente mediante un modelo de sentimiento en AWS Lambda, generar informes estratégicos automáticos mediante LLMs (Bedrock) y enviar alertas vía correo (SES).

Cuenta con:
- Simulador manual y automático de reseñas.
- Dashboard de monitoreo (Streamlit).
- Generación de informes con modelos generativos (Claude en Amazon Bedrock).
- Observabilidad completa (Prometheus + Grafana).
- Asistente comercial con consultas inteligentes sobre los datos reales.

---

## 🧩 Arquitectura Detallada

```mermaid
flowchart LR
    subgraph Navegador
        A[Usuario] -->|Inputs| B[Streamlit App]
    end

    subgraph Backend
        B -->|Texto + Canal| C[Lambda: AnalizarSentimiento]
        C -->|Sentimiento| D[Amazon Comprehend]
        D -->|Resultado| C
        C -->|Guardar resultado| E[DynamoDB]
        B -->|Leer reseñas| E

        B -->|Reseñas negativas| F[Amazon Bedrock]
        F -->|Informe generado| G[Amazon SES]
    end

    subgraph Observabilidad
        B -->|Métricas /metrics| H[Prometheus]
        H --> I[Grafana]
    end

    style A fill:#E3F2FD,stroke:#2196F3,stroke-width:2px
    style B fill:#FFF3E0,stroke:#FF9800,stroke-width:2px
    style C fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px
    style D fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px
    style E fill:#E0F7FA,stroke:#00BCD4,stroke-width:2px
    style F fill:#FCE4EC,stroke:#E91E63,stroke-width:2px
    style G fill:#F5F5F5,stroke:#607D8B,stroke-width:2px
    style H fill:#E8EAF6,stroke:#3F51B5,stroke-width:2px
    style I fill:#EDE7F6,stroke:#673AB7,stroke-width:2px

---

## 🧩 Componentes Clave

### 🔍 1. `app.py`
- Interfaz en Streamlit con 3 pestañas:
  - **Dashboard**: métricas agregadas, tendencias, nube de palabras y generador de informes con LLM.
  - **Simulador**: permite enviar reseñas manuales o simuladas desde el dataset.
  - **Asistente Comercial**: permite hacer preguntas por canal con contexto real extraído de reseñas.

### 🧠 2. LLM - Bedrock (Claude)
- Resume reseñas negativas reales y propone acciones.
- Responde consultas ejecutivas sobre problemas por canal.

### 💌 3. SES
- Envía informes generados por el LLM a correos verificados.
- Usa un remitente personalizado y formato corporativo.

### 📊 4. Observabilidad
- Métricas personalizadas:
  - `inference_requests_total`
  - `manual_reviews_sent_total`
  - `simulated_reviews_sent_total`
  - `llm_prompt_total`, `llm_errors_total`
  - `inference_duration_seconds`
- Endpoint `/metrics` expuesto localmente en el puerto `8001`.

---

## 🚀 Ejecución Local

### 1. Requisitos
- Python 3.12+
- AWS CLI configurado con acceso a Lambda, DynamoDB, Bedrock y SES.
- Docker & Docker Compose

### 2. Levantar infraestructura de observabilidad
```bash
docker compose up -d  # desde la carpeta que contiene docker-compose.yml
```

### 3. Ejecutar la app
```bash
streamlit run app.py
```

Esto abre la interfaz en `localhost:8501`

---

## 📦 Estructura de Archivos

```bash
.
├── app.py                        # Interfaz completa en Streamlit
├── fashionnova_reviews.csv      # Dataset base para simulación
├── prometheus.yml               # Configuración de Prometheus
├── docker-compose.yml           # Define servicios de Prometheus y Grafana
├── provisioning/
│   ├── datasources/prometheus.yml
│   └── dashboards/fashion_nova.json
```

---

## 📈 Dashboard Grafana

Se provisiona automáticamente con:
- Paneles de conteo y errores por componente.
- Tiempo medio de inferencia.
- Visualización en tiempo real.

Acceder a `http://localhost:3000`
- Usuario: `admin`
- Contraseña: `admin`

---

## 🤖 Capacidades del LLM

| Funcionalidad | Modelo | Servicio |
|---------------|--------|----------|
| Informe crítico | Claude-v2 | Bedrock |
| Consultas comerciales | Claude-v2 | Bedrock |

---

## 🧑‍🤝‍🧑 Equipo
Este proyecto fue desarrollado por:
**Héctor Armando Gómez Parra, Anderson Jair Alvarado Rubio, Jorge Mario Ardila Quintero y Santiago Zafra Rodríguez** - Maestría en Inteligencia Artificial

Con enfoque en IA explicable, MLOps, y aplicación empresarial de modelos generativos.

---

