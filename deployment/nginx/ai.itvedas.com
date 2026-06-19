server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ai.itvedas.com localhost;

    root /root/itvedas/dashboard/frontend/dist;
    index index.html;

    # Proxy /api/ requests to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # SPA fallback — all non-file requests serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
