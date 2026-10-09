FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app/apps/api
COPY apps/api/ ./
COPY tools/print-bridge/ /app/tools/print-bridge/
RUN pip install --no-cache-dir '.[dev]'
