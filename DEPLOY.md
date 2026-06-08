# NovaGhost — Deployment Guide

## Architecture
- **Server** → `server/server.vps.js` (Node.js Express + SQLite) → VPS at `novaghost.twistark.cloud`
- **Client** → Python app → `dist/PortalClient.exe` (PyInstaller)

---

## PART 1 — Server on VPS

### Step 1 — VPS Prerequisites (Ubuntu/Debian)

```bash
# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs git nginx certbot python3-certbot-nginx

# PM2 — keeps server alive across reboots
sudo npm install -g pm2
```

---

### Step 2 — Upload Server Files

From Windows (PowerShell):

```powershell
scp "D:\Twistark\Cheat\NovaGhost\server\server.vps.js" user@YOUR_VPS_IP:/opt/novaghost/
scp "D:\Twistark\Cheat\NovaGhost\server\schema.sql"    user@YOUR_VPS_IP:/opt/novaghost/
scp "D:\Twistark\Cheat\NovaGhost\server\package.json"  user@YOUR_VPS_IP:/opt/novaghost/
```

On the VPS:

```bash
cd /opt/novaghost
npm install
```

---

### Step 3 — Configure Secrets

```bash
# Generate a strong JWT_SECRET
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"

cat > /opt/novaghost/.env << 'EOF'
PORT=3000
JWT_SECRET=PASTE_GENERATED_SECRET_HERE
INIT_SECRET=ANOTHER_RANDOM_STRING
PRIMARY_OWNER=admin
DB_PATH=/opt/novaghost/novaghost.db
EOF

chmod 600 /opt/novaghost/.env
```

---

### Step 4 — Start with PM2

```bash
cd /opt/novaghost
pm2 start server.vps.js --name novaghost
pm2 save
pm2 startup   # run the printed command to enable auto-start on reboot
```

Verify:

```bash
pm2 status
curl http://localhost:3000/api/ping
# {"status":"online","database":"connected",...}
```

---

### Step 5 — Nginx + HTTPS for novaghost.twistark.cloud

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

# Free SSL
sudo certbot --nginx -d novaghost.twistark.cloud
```

DNS — add this A record in your domain registrar:

```
Type:  A
Name:  novaghost
Value: YOUR_VPS_IP
TTL:   300
```

Test after DNS propagates:

```bash
curl https://novaghost.twistark.cloud/api/ping
```

---

### Step 6 — Create First Admin

DB is empty on first run. First registration auto-gets `admin` — no invite key needed.

```bash
curl -X POST https://novaghost.twistark.cloud/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_STRONG_PASSWORD","hwid":""}'
```

Expected:

```json
{"success":true,"message":"Registration successful. Assigned role: admin"}
```

---

### Step 7 — Reset DB (Wipe All Data)

**WARNING: Deletes ALL users, sessions, history, and invite keys.**

```bash
pm2 stop novaghost
rm /opt/novaghost/novaghost.db
pm2 start novaghost
# Re-register admin (Step 6)
```

---

## PART 2 — Desktop Client (.exe)

### Step 1 — Server URL (already set)

`D:\Twistark\Cheat\NovaGhost\.env` already has:

```env
AUTH_SERVER_URL=https://novaghost.twistark.cloud
```

---

### Step 2 — Install PyInstaller

```powershell
cd D:\Twistark\Cheat\NovaGhost
.\venv\Scripts\Activate.ps1
pip install pyinstaller
```

---

### Step 3 — Build Exe

```powershell
pyinstaller main.spec
```

Output: `dist\PortalClient.exe`

Single standalone exe — includes Python runtime, all deps, UI assets.

---

### Step 4 — Test

1. Run `dist\PortalClient.exe`
2. Diagnostics tab → server + database should be green
3. Login with admin credentials
4. Confirm admin portal loads

---

## Quick Reference

| Action | Command |
|--------|---------|
| Server status | `pm2 status` |
| Live logs | `pm2 logs novaghost` |
| Restart server | `pm2 restart novaghost` |
| Health check | `curl https://novaghost.twistark.cloud/api/ping` |
| Wipe DB | `pm2 stop novaghost && rm novaghost.db && pm2 start novaghost` |
| Rebuild exe | `pyinstaller main.spec` |

---

## VPS .env Reference

| Variable | Description |
|----------|-------------|
| `JWT_SECRET` | Signs session tokens — 64+ random chars, keep secret |
| `INIT_SECRET` | Header value to create extra admins after bootstrap |
| `PRIMARY_OWNER` | Username protected from deletion/ban/password-reset |
| `PORT` | HTTP port (default 3000) |
| `DB_PATH` | SQLite file path |
