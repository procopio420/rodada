server {
    listen __PORT__;
    server_name _;
    client_max_body_size 8m;

    # Exact /cash is the Next.js UI; /cash/* remains the Django API.
    location = /cash {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $http_host;
    }

    # Preserve legacy guest QR page links. API paths such as
    # /guest/context/ and /guest/qr/resolve/ still go to Django.
    location ~ ^/guest/(?!qr/?$|context/?$|tabs/?$|catalog/?$|receipt/?$|realtime/?$|orders/?$|service-requests/?$)[A-Za-z0-9_-]{1,160}/?$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto https;
    }

    # Django API routes must bypass Next.js (which redirects POST /auth/login/ with 308).
    location ~ ^/(auth|venue|catalog|cash|customers|developer|dispatch|guest|health|ready|hospitality|house-account|management|order-items|payments|pricing|printing|production|receipts|refunds|service-points|tabs)(/|$) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $http_host;
        # Public clients cannot supply signed BFF assertions to Django.
        proxy_set_header X-Rodada-Bff-Host "";
        proxy_set_header X-Rodada-Bff-Time "";
        proxy_set_header X-Rodada-Bff-Signature "";
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $http_host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
