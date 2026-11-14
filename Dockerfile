# Pagina de EP3 (solo local). NO se hornean datos en la imagen: data/ se monta como volumen de solo lectura.
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true \
    HOME=/home/app

# libgomp1: lo piden xgboost y lightgbm en imagenes slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app

WORKDIR /app
COPY requirements_app.txt constraints_ep3.txt ./
RUN pip install -r requirements_app.txt -c constraints_ep3.txt

# solo codigo: el .dockerignore deja pasar unicamente app/ y el paquete ep3
COPY app ./app
COPY app/.streamlit ./.streamlit
COPY src/waymo_evaluacion/__init__.py ./src/waymo_evaluacion/__init__.py
COPY src/waymo_evaluacion/ep3 ./src/waymo_evaluacion/ep3

USER app
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health').status == 200 else 1)"

CMD ["streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
