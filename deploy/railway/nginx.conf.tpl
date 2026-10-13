server {
    listen __PORT__;
    server_name _;
    client_max_body_size 8m;

    # Raw Django API families are explicit; Web /manage, /cash, /refunds and
    # opaque /guest/:token pages must stay on Next.js. /api/* remains the BFF.
    location ~ ^/((auth|catalog|customers|developer|dispatch|health|ready|hospitality|house-account|management|order-items|payments|pricing|printing|production|receipts|service-points|tabs|realtime)(/|$)|cash/(points|shifts|correction-requests|received-by-method)(/|$)|refunds/[^/]+(/|$)|guest/(qr|context|tabs|catalog|orders|realtime|service-requests|party-size|receipt)(/|$)) {

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $http_host;
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
