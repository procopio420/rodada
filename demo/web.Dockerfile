FROM node:24-slim
WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
COPY prototype/ /app/prototype/
RUN npm run build
CMD ["npm", "start", "--", "--hostname", "0.0.0.0"]
