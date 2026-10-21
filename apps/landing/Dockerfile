FROM nginx:1.27-alpine
COPY apps/landing/nginx.conf /etc/nginx/conf.d/default.conf
COPY apps/landing/index.html /usr/share/nginx/html/index.html
COPY apps/landing/brand/ /usr/share/nginx/html/brand/
COPY apps/landing/screens/ /usr/share/nginx/html/screens/
COPY apps/landing/marketing/ /usr/share/nginx/html/marketing/
COPY apps/web/public/fonts/archivo.woff2 /usr/share/nginx/html/fonts/archivo.woff2
COPY apps/landing/privacidade.html /usr/share/nginx/html/privacidade.html
COPY apps/landing/termos.html /usr/share/nginx/html/termos.html
COPY apps/landing/exclusao-de-conta.html /usr/share/nginx/html/exclusao-de-conta.html
EXPOSE 8080

COPY apps/landing/downloads.html /usr/share/nginx/html/downloads.html
COPY apps/landing/windows-stable.json /usr/share/nginx/html/windows-stable.json
