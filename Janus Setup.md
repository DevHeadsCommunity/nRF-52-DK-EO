# Setup Guide

## 1. Install Nginx

On Fedora:

---

## 2. Install Janus Gateway from Snap

First ensure snapd is installed:

Fedora:

```bash
sudo dnf install -y snapd
sudo ln -s /var/lib/snapd/snap /snap
sudo systemctl enable --now snapd.socket
```

Then install Janus:
```bash
sudo snap install janus-gateway
```


---

## 3. Copy this Nginx file

Edit or create `/etc/nginx/conf.d/janus.conf` and paste:

> **_NOTE:_** Change root to point to `html` folder of the provided files.

> **_NOTE:_** Change APP_HOST to point to local running **Flask Application**

```nginx
server {
listen 80;
server_name localhost;
root /var/www/html; # change it to point to janus html files

# ---- Janus HTTP API ----
location /janus/ {
    proxy_pass http://localhost:8188;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;

    add_header 'Access-Control-Allow-Origin' '${CORS_ORIGIN}' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Origin, X-Requested-With, Content-Type, Accept, Authorization' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;

    if ($request_method = 'OPTIONS') {
        return 204;
    }
}

# ---- Janus WebSocket ----
location /ws {
    proxy_pass http://localhost:8188;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;

    add_header 'Access-Control-Allow-Origin' '${CORS_ORIGIN}' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Origin, X-Requested-With, Content-Type, Accept, Authorization' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
}

# ---- Flask app ----
location /app/ {
    rewrite ^/app/(.*) /$1 break;
    include /etc/nginx/proxy_params;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_pass http://${APP_HOST}; # Check Note
}
}
```
Then test and reload nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 4. Start Janus

Start Janus manually:

```bash
sudo nginx -t
janus-gateway.janus -F /var/snap/janus-gateway/current/etc/janus
```

Or run as a service:

```bash
sudo systemctl enable --now snap.janus-gateway.janus.service
sudo systemctl status snap.janus-gateway.janus.service
```