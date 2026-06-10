require('dotenv').config();
const https = require('https');

const GROQ_KEY   = process.env.GROQ_KEY;
const JIRA_EMAIL = process.env.JIRA_EMAIL;
const JIRA_TOKEN = process.env.JIRA_TOKEN;
const JIRA_BASE  = process.env.JIRA_URL?.split('/browse')[0];

function request(options, body = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, res => {
      let data = '';
      res.on('data', c => (data += c));
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function verifyJira() {
  process.stdout.write('\n🔍 Jira connection ... ');
  if (!JIRA_BASE || !JIRA_EMAIL || !JIRA_TOKEN) {
    console.log('SKIP — missing JIRA_URL / JIRA_EMAIL / JIRA_TOKEN in .env');
    return false;
  }
  const auth = Buffer.from(`${JIRA_EMAIL}:${JIRA_TOKEN}`).toString('base64');
  const url  = new URL(`${JIRA_BASE}/rest/api/3/myself`);
  try {
    const { status, body } = await request({
      hostname: url.hostname, path: url.pathname, method: 'GET',
      headers: { Authorization: `Basic ${auth}`, Accept: 'application/json' }
    });
    if (status === 200) {
      const u = JSON.parse(body);
      console.log(`✅  ${u.displayName} <${u.emailAddress}>`);
      return true;
    }
    console.log(`❌  HTTP ${status}`);
    return false;
  } catch (e) { console.log(`❌  ${e.message}`); return false; }
}

async function verifyGroq() {
  process.stdout.write('🔍 GROQ connection  ... ');
  if (!GROQ_KEY) { console.log('SKIP — missing GROQ_KEY in .env'); return false; }
  const payload = JSON.stringify({
    model: 'llama-3.1-8b-instant',
    messages: [{ role: 'user', content: 'Reply with only the word: OK' }],
    max_tokens: 5, temperature: 0
  });
  try {
    const { status, body } = await request({
      hostname: 'api.groq.com', path: '/openai/v1/chat/completions', method: 'POST',
      headers: {
        Authorization: `Bearer ${GROQ_KEY}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    }, payload);
    if (status === 200) {
      const reply = JSON.parse(body).choices[0].message.content.trim();
      console.log(`✅  responded "${reply}"`);
      return true;
    }
    const err = JSON.parse(body);
    console.log(`❌  HTTP ${status} — ${err.error?.message || body}`);
    return false;
  } catch (e) { console.log(`❌  ${e.message}`); return false; }
}

async function verifyTicket() {
  process.stdout.write('🔍 Jira ticket KAN-4 ... ');
  if (!JIRA_BASE || !JIRA_EMAIL || !JIRA_TOKEN) { console.log('SKIP'); return false; }
  const auth = Buffer.from(`${JIRA_EMAIL}:${JIRA_TOKEN}`).toString('base64');
  const url  = new URL(`${JIRA_BASE}/rest/api/3/issue/KAN-4`);
  try {
    const { status, body } = await request({
      hostname: url.hostname, path: url.pathname, method: 'GET',
      headers: { Authorization: `Basic ${auth}`, Accept: 'application/json' }
    });
    if (status === 200) {
      const t = JSON.parse(body);
      console.log(`✅  "${t.fields.summary}"`);
      return true;
    }
    console.log(`❌  HTTP ${status}`);
    return false;
  } catch (e) { console.log(`❌  ${e.message}`); return false; }
}

(async () => {
  console.log('\n╔══════════════════════════════════════╗');
  console.log('║  BLAST Phase 2 — L (Link) Verify     ║');
  console.log('╚══════════════════════════════════════╝');
  const j1 = await verifyJira();
  const g  = await verifyGroq();
  const j2 = await verifyTicket();
  console.log('\n──────────────────────────────────────');
  if (j1 && g && j2) {
    console.log('✅  ALL LINKS VERIFIED — Phase 2 PASS\n');
  } else {
    console.log('❌  SOME LINKS FAILED — fix .env then retry\n');
    process.exit(1);
  }
})();
