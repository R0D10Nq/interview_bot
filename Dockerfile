FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && ln -sf /data/interviews.db /app/interviews.db \
    && chown -R appuser:appuser /app /data

USER appuser

VOLUME ["/data"]

CMD ["python", "-m", "app.main"]
