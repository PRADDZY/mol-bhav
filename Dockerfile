# ---- Build stage ----
FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# ---- Runtime stage ----
FROM python:3.13-slim

RUN groupadd -r molbhav && useradd -r -g molbhav -d /app -s /sbin/nologin molbhav

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app/ ./app/

RUN chown -R molbhav:molbhav /app

USER molbhav

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
