FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app/apps/api
COPY apps/api/ ./
COPY tools/print-bridge/ /app/tools/print-bridge/
# The existing cross-package contract test runs inside this disposable image.
COPY apps/printer-agent/rodada_printer_agent/contracts.py /app/apps/printer-agent/rodada_printer_agent/contracts.py
COPY deploy/railway/runtime-profile.sh /app/deploy/railway/runtime-profile.sh
RUN pip install --no-cache-dir '.[dev]'
