import express from 'express';
import cors from 'cors';
import { createHmac, randomUUID } from 'crypto';
import bcrypt from 'bcryptjs';
import Database from 'better-sqlite3';
import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';

config();

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT         = process.env.PORT         || 3000;
const JWT_SECRET   = process.env.JWT_SECRET   || 'DEFAULT_JWT_SIGNING_KEY_novaghost';
const INIT_SECRET  = process.env.INIT_SECRET  || '';
const PRIMARY_OWNER = process.env.PRIMARY_OWNER || 'admin';
const DB_PATH      = process.env.DB_PATH      || resolve(__dirname, 'novaghost.db');

// ── Database ────────────────────────────────────────────────────────────────
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

const schemaPath = resolve(__dirname, 'schema.sql');
if (existsSync(schemaPath)) {
  db.exec(readFileSync(schemaPath, 'utf8'));
}

// ── JWT ─────────────────────────────────────────────────────────────────────
function signJWT(payload) {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const body   = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig    = createHmac('sha256', JWT_SECRET).update(`${header}.${body}`).digest('base64url');
  return `${header}.${body}.${sig}`;
}

function verifyJWT(token) {
  try {
    const [header, body, sig] = token.split('.');
    if (!header || !body || !sig) return null;
    const expected = createHmac('sha256', JWT_SECRET).update(`${header}.${body}`).digest('base64url');
    if (sig !== expected) return null;
    const payload = JSON.parse(Buffer.from(body, 'base64url').toString());
    if (payload.exp && Math.floor(Date.now() / 1000) > payload.exp) return null;
    return payload;
  } catch {
    return null;
  }
}

function authenticateToken(req) {
  const auth = req.headers['authorization'];
  if (!auth || !auth.startsWith('Bearer ')) return null;
  return verifyJWT(auth.split(' ')[1]);
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function isPrimaryOwner(username) {
  if (username === PRIMARY_OWNER) return true;
  try {
    const row = db.prepare('SELECT username FROM users ORDER BY created_at ASC LIMIT 1').get();
    return row && row.username === username;
  } catch {
    return false;
  }
}

function logAudit(actor, action, target, ip, details) {
  try {
    db.prepare('INSERT INTO audit_log (actor, action, target, ip_address, details) VALUES (?, ?, ?, ?, ?)')
      .run(actor, action, target, ip, details);
  } catch (e) {
    console.error('Audit log error:', e);
  }
}

// ── App ──────────────────────────────────────────────────────────────────────
const app = express();
app.set('trust proxy', true);
app.use(cors());
app.use(express.json());

// ── Public routes ─────────────────────────────────────────────────────────────

app.get('/api/ping', (req, res) => {
  let dbStatus = 'connected';
  try { db.prepare('SELECT 1').get(); } catch { dbStatus = 'error'; }
  res.json({ status: 'online', database: dbStatus, timestamp: new Date().toISOString() });
});

app.get('/api/announcements', (req, res) => {
  const row = db.prepare("SELECT value FROM system_config WHERE key = 'announcements'").get();
  res.json({ announcements: row ? row.value : 'No announcements active.' });
});

app.get('/api/version', (req, res) => {
  const row = db.prepare("SELECT value FROM system_config WHERE key = 'latest_version'").get();
  res.type('text').send(row ? row.value : '2.0.0');
});

app.get('/api/changelog', (req, res) => {
  const row = db.prepare("SELECT value FROM system_config WHERE key = 'changelog'").get();
  res.type('text').send(row ? row.value : '');
});

app.get('/api/update', (req, res) => {
  const clientVer = req.query.version || '';
  const rows = db.prepare('SELECT key, value FROM system_config').all();
  const cfg = Object.fromEntries(rows.map(r => [r.key, r.value]));
  const latest = cfg.latest_version || '2.0.0';
  res.json({ latest_version: latest, changelog: cfg.changelog || '', download_url: cfg.download_url || '', update_available: latest !== clientVer });
});

app.post('/api/login', (req, res) => {
  const { username = '', password = '', hwid = '' } = req.body;
  const clientIP = req.ip;
  if (!username.trim() || !password.trim())
    return res.status(400).json({ success: false, message: 'Username and password required' });

  const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username.trim());
  if (!user || !bcrypt.compareSync(password.trim(), user.password_hash)) {
    db.prepare('INSERT INTO login_history (username, ip_address, hwid, status) VALUES (?, ?, ?, ?)').run(username, clientIP, hwid, 'FAILED_PASSWORD');
    return res.status(401).json({ success: false, message: 'Invalid username or password' });
  }
  if (user.is_banned === 1) {
    db.prepare('INSERT INTO login_history (username, ip_address, hwid, status) VALUES (?, ?, ?, ?)').run(username, clientIP, hwid, 'BANNED');
    return res.status(403).json({ success: false, message: 'Account has been banned' });
  }

  let userHWID = user.hwid;
  if (!userHWID) {
    db.prepare('UPDATE users SET hwid = ? WHERE username = ?').run(hwid.trim(), username.trim());
    userHWID = hwid.trim();
  } else if (userHWID !== hwid.trim()) {
    db.prepare('INSERT INTO login_history (username, ip_address, hwid, status) VALUES (?, ?, ?, ?)').run(username, clientIP, hwid, 'DEVICE_MISMATCH');
    return res.status(403).json({ success: false, message: 'Device mismatch.' });
  }

  const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);
  db.prepare('UPDATE users SET last_login = ? WHERE username = ?').run(nowStr, username.trim());
  db.prepare('INSERT INTO login_history (username, ip_address, hwid, status) VALUES (?, ?, ?, ?)').run(username, clientIP, hwid, 'SUCCESS');

  const exp = Math.floor(Date.now() / 1000) + (24 * 3600);
  const token = signJWT({ username: user.username, role: user.role, exp });

  res.json({
    success: true, token,
    user_data: {
      username: user.username,
      ip: clientIP,
      hwid: userHWID,
      role: user.role,
      expires: 'Never (Lifetime)',
      createdate: user.created_at,
      lastlogin: nowStr,
      subscription: user.role === 'admin' ? 'Developer Admin' : user.role === 'moderator' ? 'Moderator' : 'Standard Client',
      credits: user.credits !== null ? user.credits : 15,
      credits_unlimited: !!user.credits_unlimited,
      lifetime_requests: user.lifetime_requests || 0
    }
  });
});

app.post('/api/register', (req, res) => {
  const { username = '', password = '', role: requestedRole = 'user' } = req.body;
  let { hwid = '', invite_key: inviteKey = '' } = req.body;
  const clientIP = req.ip;

  // Accept invite key sent in wrong field (e.g. curl tests using hwid instead of invite_key)
  if (!inviteKey.trim() && hwid.trim().toUpperCase().startsWith('PORTAL-')) {
    inviteKey = hwid.trim();
    hwid = '';
  }

  if (!username.trim() || !password.trim())
    return res.status(400).json({ success: false, message: 'Username and password required' });

  if (db.prepare('SELECT username FROM users WHERE username = ?').get(username.trim()))
    return res.status(409).json({ success: false, message: 'Username already exists' });

  const hashed = bcrypt.hashSync(password.trim(), 10);
  let finalRole = 'user';
  let isBootstrap = false;

  const countRow = db.prepare('SELECT COUNT(*) as count FROM users').get();
  if (countRow && countRow.count === 0) {
    finalRole = 'admin';
    isBootstrap = true;
  } else {
    const initHeader = req.headers['x-init-secret'];
    if (initHeader && INIT_SECRET && initHeader === INIT_SECRET) {
      if (requestedRole === 'admin' || requestedRole === 'moderator') {
        finalRole = requestedRole;
        isBootstrap = true;
      }
    }
  }

  if (!isBootstrap) {
    if (!inviteKey.trim())
      return res.status(400).json({ success: false, message: 'An invite/access key is required. Send it as the "invite_key" field.' });
    const inviteRow = db.prepare('SELECT * FROM invite_keys WHERE key = ? AND is_used = 0').get(inviteKey.trim());
    if (!inviteRow)
      return res.status(403).json({ success: false, message: 'Invalid or already used invite/access key.' });
    db.prepare('UPDATE invite_keys SET is_used = 1, used_by = ? WHERE key = ?').run(username.trim(), inviteKey.trim());
  }

  const initialUnlimited = finalRole === 'admin' ? 1 : 0;
  db.prepare('INSERT INTO users (username, password_hash, hwid, role, credits, credits_unlimited) VALUES (?, ?, ?, ?, ?, ?)')
    .run(username.trim(), hashed, hwid.trim() || null, finalRole, 15, initialUnlimited);

  if (isBootstrap && finalRole !== 'user') {
    logAudit('SYSTEM_INIT', 'INITIALIZE_PRIVILEGED_ROLE', username.trim(), clientIP, `User registered as role '${finalRole}' with unlimited=${initialUnlimited}.`);
  } else {
    logAudit('SYSTEM', 'REGISTER_USER_WITH_KEY', username.trim(), clientIP, `User registered using access key '${inviteKey}'. Credits: 15.`);
  }
  res.status(201).json({ success: true, message: `Registration successful. Assigned role: ${finalRole}` });
});

app.get('/api/user/credits', (req, res) => {
  const session = authenticateToken(req);
  if (!session) return res.status(401).json({ message: 'Unauthorized' });
  const user = db.prepare('SELECT credits, credits_unlimited, lifetime_requests, last_request_at FROM users WHERE username = ?').get(session.username);
  if (!user) return res.status(404).json({ message: 'User not found' });
  res.json({ username: session.username, credits: user.credits ?? 0, credits_unlimited: !!user.credits_unlimited, lifetime_requests: user.lifetime_requests || 0, last_request_at: user.last_request_at || null });
});

app.post('/api/user/consume-credit', (req, res) => {
  const session = authenticateToken(req);
  if (!session) return res.status(401).json({ message: 'Unauthorized' });
  const user = db.prepare('SELECT credits, credits_unlimited FROM users WHERE username = ?').get(session.username);
  if (!user) return res.status(404).json({ message: 'User not found' });
  const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);
  if (user.credits_unlimited) {
    db.prepare('UPDATE users SET lifetime_requests = lifetime_requests + 1, last_request_at = ? WHERE username = ?').run(nowStr, session.username);
    return res.json({ success: true, credits: -1, unlimited: true, message: 'Request processed.' });
  }
  if (!user.credits || user.credits <= 0)
    return res.status(402).json({ success: false, credits: 0, unlimited: false, message: 'No credits available. Contact administrator.' });
  db.prepare('UPDATE users SET credits = credits - 1, lifetime_requests = lifetime_requests + 1, last_request_at = ? WHERE username = ?').run(nowStr, session.username);
  const updated = db.prepare('SELECT credits FROM users WHERE username = ?').get(session.username);
  res.json({ success: true, credits: updated ? updated.credits : 0, unlimited: false, message: 'Credit consumed.' });
});

// ── Admin middleware ───────────────────────────────────────────────────────────
function requireAdmin(req, res, next) {
  const session = authenticateToken(req);
  if (!session) return res.status(401).json({ success: false, message: 'Invalid or expired session token.' });
  if (session.role !== 'admin' && session.role !== 'moderator')
    return res.status(403).json({ success: false, message: 'Forbidden. Admin or Moderator privileges required.' });
  req.session = session;
  next();
}

// ── Admin routes ──────────────────────────────────────────────────────────────

app.get('/api/admin/invites', requireAdmin, (req, res) => {
  res.json(db.prepare('SELECT key, is_used, used_by, created_at FROM invite_keys ORDER BY created_at DESC').all());
});

app.post('/api/admin/invites', requireAdmin, (req, res) => {
  const key = `PORTAL-${randomUUID().substring(0, 12).toUpperCase()}`;
  db.prepare('INSERT INTO invite_keys (key, is_used) VALUES (?, 0)').run(key);
  logAudit(req.session.username, 'GENERATE_INVITE_KEY', key, req.ip, 'Generated a new invite key.');
  res.json({ message: 'Invite key generated successfully', key });
});

app.delete('/api/admin/invites/:key', requireAdmin, (req, res) => {
  const targetKey = req.params.key;
  db.prepare('DELETE FROM invite_keys WHERE key = ?').run(targetKey);
  logAudit(req.session.username, 'DELETE_INVITE_KEY', targetKey, req.ip, 'Deleted invite key.');
  res.json({ message: `Invite key '${targetKey}' deleted successfully` });
});

app.get('/api/admin/users', requireAdmin, (req, res) => {
  const oldest = db.prepare('SELECT username FROM users ORDER BY created_at ASC LIMIT 1').get();
  const users = db.prepare('SELECT username, role, hwid, is_banned, credits, credits_unlimited, lifetime_requests, last_request_at, created_at, last_login FROM users').all();
  res.json(users.map(u => ({ ...u, is_owner: u.username === (oldest && oldest.username) || u.username === PRIMARY_OWNER })));
});

app.get('/api/admin/users/:username/credits', requireAdmin, (req, res) => {
  const user = db.prepare('SELECT credits, credits_unlimited, lifetime_requests, last_request_at FROM users WHERE username = ?').get(req.params.username);
  if (!user) return res.status(404).json({ message: 'User not found' });
  res.json({ username: req.params.username, credits: user.credits ?? 0, credits_unlimited: !!user.credits_unlimited, lifetime_requests: user.lifetime_requests || 0, last_request_at: user.last_request_at || null });
});

app.post('/api/admin/users/:username/credits', requireAdmin, (req, res) => {
  if (req.session.role !== 'admin') return res.status(403).json({ message: 'Admin role required for credit management.' });
  const targetUser = req.params.username;
  const { action = 'set', amount, unlimited } = req.body;
  if (!db.prepare('SELECT username FROM users WHERE username = ?').get(targetUser))
    return res.status(404).json({ message: 'User not found' });
  if (unlimited !== undefined) {
    db.prepare('UPDATE users SET credits_unlimited = ? WHERE username = ?').run(unlimited ? 1 : 0, targetUser);
    const state = unlimited ? 'enabled' : 'disabled';
    logAudit(req.session.username, 'SET_CREDITS_UNLIMITED', targetUser, req.ip, `Unlimited credits ${state}`);
    return res.json({ message: `Unlimited credits ${state} for '${targetUser}'.` });
  }
  const amt = parseInt(amount) || 0;
  if (action === 'set') {
    db.prepare('UPDATE users SET credits = ? WHERE username = ?').run(amt, targetUser);
    logAudit(req.session.username, 'ADMIN_CREDITS_SET', targetUser, req.ip, `Credits set to ${amt}`);
  } else if (action === 'add') {
    db.prepare('UPDATE users SET credits = credits + ? WHERE username = ?').run(amt, targetUser);
    logAudit(req.session.username, 'ADMIN_CREDITS_ADD', targetUser, req.ip, `Added ${amt} credits`);
  } else {
    return res.status(400).json({ message: 'Invalid action.' });
  }
  const updated = db.prepare('SELECT credits FROM users WHERE username = ?').get(targetUser);
  res.json({ message: `Credits updated for '${targetUser}'.`, credits: updated.credits });
});

app.post('/api/admin/users', requireAdmin, (req, res) => {
  const { username = '', password = '', role: targetRole = 'user' } = req.body;
  if (!username.trim() || !password.trim()) return res.status(400).json({ message: 'Username and password required' });
  if (req.session.role === 'moderator' && targetRole !== 'user')
    return res.status(403).json({ message: 'Moderators cannot create privileged user profiles.' });
  try {
    db.prepare('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)').run(username.trim(), bcrypt.hashSync(password.trim(), 10), targetRole);
    logAudit(req.session.username, 'CREATE_USER', username.trim(), req.ip, `Created profile with role '${targetRole}'.`);
    res.json({ message: `User '${username}' created successfully` });
  } catch {
    res.status(409).json({ message: 'Username already exists or database error' });
  }
});

app.delete('/api/admin/users/:username', requireAdmin, (req, res) => {
  const targetUser = req.params.username;
  if (req.session.username === targetUser) return res.status(400).json({ message: 'Cannot delete your own account' });
  if (isPrimaryOwner(targetUser)) return res.status(403).json({ message: 'Cannot delete the protected primary owner account.' });
  if (req.session.role === 'moderator') return res.status(403).json({ message: 'Moderators are not authorized to delete profiles.' });
  if (!db.prepare('SELECT role FROM users WHERE username = ?').get(targetUser))
    return res.status(404).json({ message: 'User not found' });
  db.prepare('DELETE FROM users WHERE username = ?').run(targetUser);
  logAudit(req.session.username, 'DELETE_USER', targetUser, req.ip, 'Deleted user profile.');
  res.json({ message: `User '${targetUser}' deleted successfully` });
});

app.post('/api/admin/reset-password', requireAdmin, (req, res) => {
  const { username: targetUser = '', password: newPassword = '' } = req.body;
  if (!targetUser.trim() || !newPassword.trim()) return res.status(400).json({ message: 'Username and new password required' });
  if (isPrimaryOwner(targetUser.trim()) && req.session.username !== targetUser.trim())
    return res.status(403).json({ message: 'Cannot reset password for the protected primary owner account.' });
  const profile = db.prepare('SELECT role FROM users WHERE username = ?').get(targetUser.trim());
  if (!profile) return res.status(404).json({ message: 'User not found' });
  if (req.session.role === 'moderator' && profile.role === 'admin')
    return res.status(403).json({ message: 'Moderators cannot reset administrator passwords.' });
  db.prepare('UPDATE users SET password_hash = ? WHERE username = ?').run(bcrypt.hashSync(newPassword.trim(), 10), targetUser.trim());
  logAudit(req.session.username, 'RESET_PASSWORD', targetUser.trim(), req.ip, 'Reset user password.');
  res.json({ message: `Password for user '${targetUser}' reset successfully` });
});

app.post('/api/admin/reset-hwid', requireAdmin, (req, res) => {
  const { username: targetUser = '' } = req.body;
  if (!targetUser.trim()) return res.status(400).json({ message: 'Username required' });
  if (isPrimaryOwner(targetUser.trim()) && req.session.username !== targetUser.trim())
    return res.status(403).json({ message: 'Cannot reset HWID for the protected primary owner account.' });
  db.prepare('UPDATE users SET hwid = NULL WHERE username = ?').run(targetUser.trim());
  logAudit(req.session.username, 'RESET_HWID', targetUser.trim(), req.ip, 'Reset HWID binding.');
  res.json({ message: `Hardware ID for user '${targetUser}' reset successfully` });
});

app.post('/api/admin/ban', requireAdmin, (req, res) => {
  const { username: targetUser = '', banned = 1 } = req.body;
  if (!targetUser.trim()) return res.status(400).json({ message: 'Username required' });
  if (req.session.username === targetUser.trim()) return res.status(400).json({ message: 'Cannot ban your own account' });
  if (isPrimaryOwner(targetUser.trim())) return res.status(403).json({ message: 'Cannot ban the protected primary owner account.' });
  if (req.session.role === 'moderator') {
    const profile = db.prepare('SELECT role FROM users WHERE username = ?').get(targetUser.trim());
    if (profile && profile.role === 'admin') return res.status(403).json({ message: 'Moderators cannot ban admin profiles.' });
  }
  const bannedNum = Number(banned);
  db.prepare('UPDATE users SET is_banned = ? WHERE username = ?').run(bannedNum, targetUser.trim());
  const action = bannedNum === 1 ? 'BANNED' : 'UNBANNED';
  logAudit(req.session.username, action, targetUser.trim(), req.ip, `Banned status set to: ${bannedNum}`);
  res.json({ message: `User '${targetUser}' has been ${action.toLowerCase()}` });
});

app.post('/api/admin/version', requireAdmin, (req, res) => {
  if (req.session.role !== 'admin') return res.status(403).json({ message: 'Forbidden. Admin role required to modify configuration.' });
  const { version = '', changelog = '', download_url: downloadUrl = '', announcements = '' } = req.body;
  if (!version && !announcements && !changelog && !downloadUrl)
    return res.status(400).json({ message: 'Provide at least one setting to update.' });
  const insert = db.prepare('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)');
  db.transaction(() => {
    if (version)     insert.run('latest_version', version);
    if (changelog)   insert.run('changelog', changelog);
    if (downloadUrl) insert.run('download_url', downloadUrl);
    if (announcements) insert.run('announcements', announcements);
  })();
  logAudit(req.session.username, 'UPDATE_SYSTEM_METADATA', null, req.ip, `Updated configs: version='${version}', url='${downloadUrl}'`);
  res.json({ message: 'System configuration updated successfully' });
});

app.get('/api/admin/audit-logs', requireAdmin, (req, res) => {
  res.json(db.prepare('SELECT id, actor, action, target, ip_address, details, timestamp FROM audit_log ORDER BY id DESC LIMIT 150').all());
});

app.get('/api/admin/login-history', requireAdmin, (req, res) => {
  res.json(db.prepare('SELECT id, username, ip_address, hwid, status, timestamp FROM login_history ORDER BY id DESC LIMIT 150').all());
});

// ── Fallback ─────────────────────────────────────────────────────────────────
app.use((req, res) => res.status(404).json({ success: false, message: 'Endpoint not found' }));
app.use((err, req, res, _next) => {
  console.error(err);
  res.status(500).json({ success: false, message: `Server error: ${err.message}` });
});

app.listen(PORT, () => console.log(`NovaGhost server running on port ${PORT}`));
