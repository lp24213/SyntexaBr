FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo
COPY app.py .
COPY vereda_backend/ ./vereda_backend/

# Porta
EXPOSE 8000

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV ORACLE_MODE=true

CMD ["python", "app.py"]
