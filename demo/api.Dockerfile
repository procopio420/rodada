FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app/apps/api
COPY apps/api/ ./
COPY tools/print-bridge/ /app/tools/print-bridge/
COPY deploy/railway/runtime-profile.sh /app/deploy/railway/runtime-profile.sh
RUN pip install --no-cache-dir '.[dev]'
