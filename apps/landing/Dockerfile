FROM nginx:1.27-alpine
COPY apps/landing/nginx.conf /etc/nginx/conf.d/default.conf
COPY apps/landing/index.html /usr/share/nginx/html/index.html
COPY apps/landing/privacidade.html /usr/share/nginx/html/privacidade.html
EXPOSE 8080
