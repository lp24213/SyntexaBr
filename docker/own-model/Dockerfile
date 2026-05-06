FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt requirements-research.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-research.txt

COPY . .

EXPOSE 9000

CMD ["python", "training/serve_model.py", "--checkpoint", "/app/checkpoints/syntexa_small/manifest.json", "--host", "0.0.0.0", "--port", "9000"]
