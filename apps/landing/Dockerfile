FROM nginx:1.27-alpine
COPY apps/landing/nginx.conf /etc/nginx/conf.d/default.conf
COPY apps/landing/index.html /usr/share/nginx/html/index.html
COPY apps/landing/privacidade.html /usr/share/nginx/html/privacidade.html
COPY apps/landing/termos.html /usr/share/nginx/html/termos.html
COPY apps/landing/exclusao-de-conta.html /usr/share/nginx/html/exclusao-de-conta.html
EXPOSE 8080
