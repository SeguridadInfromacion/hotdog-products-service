FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# El proceso corre con un usuario sin privilegios, nunca como root.
RUN useradd --system --uid 10001 --no-create-home appuser
USER 10001

EXPOSE 8000

# --proxy-headers: la IP real del cliente la entrega el gateway (X-Forwarded-For).
# El servicio solo es alcanzable desde la red interna de Docker.
CMD ["uvicorn", "app.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*", \
     "--no-server-header"]
