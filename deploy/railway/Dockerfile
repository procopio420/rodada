# Disposable Aderlan demo: API + dispatcher + Next.js behind one password gate.
FROM node:24-bookworm-slim AS web-build
WORKDIR /src/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
COPY prototype/ /src/prototype/
RUN npm run build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NODE_ENV=production PORT=8080
RUN apt-get update && apt-get install -y --no-install-recommends nginx apache2-utils libstdc++6 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default
COPY --from=web-build /usr/local/bin/node /usr/local/bin/node
WORKDIR /app/apps/api
COPY apps/api/ ./
COPY tools/print-bridge/ /app/tools/print-bridge/
RUN pip install --no-cache-dir .
WORKDIR /app/apps/web
COPY --from=web-build /src/apps/web/ ./
COPY --from=web-build /src/prototype/ /app/prototype/
WORKDIR /app
COPY deploy/railway/ /app/deploy/railway/
EXPOSE 8080
CMD ["/bin/bash", "/app/deploy/railway/start.sh"]
