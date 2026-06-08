# NovaGhost — Deployment Guide

## Architecture
- **Server** → `server/server.vps.js` (Node.js Express + SQLite) → Linux VPS
- **Client** → Python app → `dist/PortalClient.exe` (PyInstaller)

---

## PART 1 — Server on VPS

### Step 1 — VPS Prerequisites (Ubuntu/Debian)

```bash
# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs git

# PM2 (process manager — keeps server alive on reboot)
sudo npm install -g pm2
```

---

### Step 2 — Upload Files to VPS

From your Windows machine (PowerShell):

```powershell
scp "D:\Twistark\Cheat\NovaGhost\server\server.vps.js" user@YOUR_VPS_IP:/opt/novaghost/
scp "D:\Twistark\Cheat\NovaGhost\server\schema.sql"    user@YOUR_VPS_IP:/opt/novaghost/
```

On the VPS:

```bash
mkdir -p /opt/novaghost && cd /opt/novaghost

cat > package.json << 'EOF'
{
  "name": "novaghost-server",
  "version": "1.0.0",
  "type": "module",
  "main": "server.vps.js",
  "dependencies": {
    "bcryptjs": "^2.4.3",
    "better-sqlite3": "^9.4.3",
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.19.2"
  }
}
EOF

npm install
```

---

### Step 3 — Configure Secrets

```bash
# Generate a strong JWT_SECRET
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"

# Create .env
cat > /opt/novaghost/.env << 'EOF'
PORT=3000
JWT_SECRET=PASTE_GENERATED_SECRET_HERE
INIT_SECRET=ANOTHER_RANDOM_STRING_FOR_EXTRA_ADMIN_SETUP
PRIMARY_OWNER=admin
DB_PATH=/opt/novaghost/novaghost.db
EOF

chmod 600 /opt/novaghost/.env
```

---

### Step 4 — Start Server

```bash
cd /opt/novaghost
pm2 start server.vps.js --name novaghost
pm2 save
pm2 startup   # run the command it prints to enable auto-start on reboot
```

Check it's running:

```bash
pm2 status
pm2 logs novaghost
curl http://localhost:3000/api/ping
```

---

### Step 5 — Nginx + HTTPS

```bash
sudo apt install -y nginx certbot python3-certbot-nginx

sudo nano /etc/nginx/sites-available/novaghost
```

Paste (replace `your-domain.com`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

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

# Free SSL via Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

---

### Step 6 — Create First Admin

DB is empty on first run. First `POST /api/register` auto-gets `admin` role — no invite key needed.

```bash
curl -X POST https://your-domain.com/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_STRONG_PASSWORD","hwid":""}'
```

Expected:
```json
{"success":true,"message":"Registration successful. Assigned role: admin"}
```

---

### Step 7 — Reset / Wipe DB (Clear All Auth Data)

**WARNING: Deletes ALL users, history, invite keys, and config. Cannot be undone.**

```bash
pm2 stop novaghost
rm /opt/novaghost/novaghost.db
pm2 start novaghost
```

Server recreates the DB from `schema.sql` on startup. Then re-register your admin (Step 6).

---

## PART 2 — Desktop Client (.exe)

### Step 1 — Set Server URL

Edit `D:\Twistark\Cheat\NovaGhost\.env`:

```env
AUTH_SERVER_URL=https://your-domain.com
```

---

### Step 2 — Install PyInstaller

```powershell
cd D:\Twistark\Cheat\NovaGhost
.\venv\Scripts\Activate.ps1
pip install pyinstaller
```

---

### Step 3 — Build

`main.spec` is already configured (icon, assets, windowed mode). Run:

```powershell
pyinstaller main.spec
```

Output: `dist\PortalClient.exe`

This is a single standalone exe — includes Python runtime, all deps, `ui/bg.png`, `ui/icon.ico`, and CustomTkinter assets.

---

### Step 4 — Test Before Distributing

1. Run `dist\PortalClient.exe`
2. Open Diagnostics — server and database status should be green
3. Login with your admin credentials
4. Confirm admin portal loads

---

## Quick Reference

| Action | Command |
|--------|---------|
| Server status | `pm2 status` |
| Live logs | `pm2 logs novaghost` |
| Restart server | `pm2 restart novaghost` |
| Health check | `curl https://your-domain.com/api/ping` |
| Wipe DB | `pm2 stop novaghost && rm novaghost.db && pm2 start novaghost` |
| Rebuild exe | `pyinstaller main.spec` |
| Add extra admin | POST `/api/register` with `X-Init-Secret` header = your `INIT_SECRET` value |

---

## Environment Variables Reference

| Variable | Where | Purpose |
|----------|-------|---------|
| `JWT_SECRET` | VPS `.env` | Signs session tokens — keep secret, 64+ chars |
| `INIT_SECRET` | VPS `.env` | Allows creating extra admins after bootstrap |
| `PRIMARY_OWNER` | VPS `.env` | Username protected from deletion/ban |
| `PORT` | VPS `.env` | HTTP port (default 3000) |
| `DB_PATH` | VPS `.env` | SQLite file path |
| `AUTH_SERVER_URL` | Client `.env` | Server URL baked into the exe |
