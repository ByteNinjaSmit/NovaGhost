# NovaGhost — Deployment Guide

## Architecture
- **Server** → `server/server.vps.js` (Node.js Express + SQLite) → VPS at `novaghost.twistark.cloud`
- **Client** → Python app → `dist/PortalClient.exe` (PyInstaller)

---

## PART 1 — Server on VPS (GitHub deploy)

### Step 1 — VPS Prerequisites

```bash
# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs git nginx

# PM2
sudo npm install -g pm2
```

---

### Step 2 — Clone Repo

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git novaghost
cd /opt/novaghost/server
npm install
```

---

### Step 3 — Create .env on VPS

```bash
cat > /opt/novaghost/server/.env << 'EOF'
PORT=3000
JWT_SECRET=REPLACE_WITH_LONG_RANDOM_STRING
INIT_SECRET=REPLACE_WITH_ANOTHER_RANDOM_STRING
PRIMARY_OWNER=admin
DB_PATH=/opt/novaghost/server/novaghost.db
EOF

chmod 600 /opt/novaghost/server/.env
```

Generate secrets:

```bash
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
```

Run twice — one value for `JWT_SECRET`, one for `INIT_SECRET`.

---

### Step 4 — Start with PM2

```bash
cd /opt/novaghost/server
pm2 start server.vps.js --name novaghost
pm2 save
pm2 startup
# Copy and run the command PM2 prints
```

Check:

```bash
pm2 status
curl http://localhost:3000/api/ping
```

---

### Step 5 — Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/novaghost
```

Paste:

```nginx
server {
    listen 80;
    server_name novaghost.twistark.cloud;

    location / {
        proxy_pass         http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header   Host             $host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/novaghost /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

DNS — add A record in your registrar:

```
Type:  A
Name:  novaghost
Value: YOUR_VPS_IP
TTL:   300
```

---

### Step 6 — Create First Admin

DB is empty on first boot — first registration auto-gets `admin`.

```bash
curl -X POST https://novaghost.twistark.cloud/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_STRONG_PASSWORD","hwid":""}'
```

---

### Step 7 — Update Server (pull new code)

```bash
cd /opt/novaghost
git pull
cd server
npm install          # only needed if package.json changed
pm2 restart novaghost
```

---

### Step 8 — Reset DB (Wipe All Data)

**WARNING: Deletes ALL users, sessions, history, invite keys.**

```bash
pm2 stop novaghost
rm /opt/novaghost/server/novaghost.db
pm2 start novaghost
# Re-register admin (Step 6)
```

---

## PART 2 — Desktop Client (.exe)

### Step 1 — Server URL (already set)

`D:\Twistark\Cheat\NovaGhost\.env`:

```env
AUTH_SERVER_URL=https://novaghost.twistark.cloud
```

### Step 2 — Build

```powershell
cd D:\Twistark\Cheat\NovaGhost
.\venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller main.spec
```

Output: `dist\PortalClient.exe`

---

## Quick Reference

| Action | Command (on VPS) |
|--------|-----------------|
| Status | `pm2 status` |
| Logs | `pm2 logs novaghost` |
| Restart | `pm2 restart novaghost` |
| Pull + restart | `cd /opt/novaghost && git pull && pm2 restart novaghost` |
| Health check | `curl https://novaghost.twistark.cloud/api/ping` |
| Wipe DB | `pm2 stop novaghost && rm server/novaghost.db && pm2 start novaghost` |

---

## VPS .env Reference

| Variable | Description |
|----------|-------------|
| `JWT_SECRET` | Signs session tokens — 64+ random chars, never share |
| `INIT_SECRET` | Header value to create extra admins after bootstrap |
| `PRIMARY_OWNER` | Username immune to ban/delete/password-reset by others |
| `PORT` | HTTP port (default 3000) |
| `DB_PATH` | SQLite file path |
