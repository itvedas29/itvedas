server {
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

    listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/ai.itvedas.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ai.itvedas.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = ai.itvedas.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ai.itvedas.com localhost;
    return 404; # managed by Certbot


}
