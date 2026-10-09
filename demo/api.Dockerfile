FROM python:3.13-slim
WORKDIR /app/apps/api
COPY apps/api/ ./
RUN pip install --no-cache-dir '.[dev]'
