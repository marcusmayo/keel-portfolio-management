const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const LOG = path.join(process.env.HOME, 'keel', 'logs', 'audit.jsonl');

function lastHash() {
  try {
    const data = fs.readFileSync(LOG, 'utf8').trim();
    if (!data) return 'GENESIS';
    const lines = data.split('\n');
    const last = JSON.parse(lines[lines.length - 1]);
    return last.hash || 'GENESIS';
  } catch {
    return 'GENESIS';
  }
}

// Append a hash-chained audit entry. `event` is a plain object.
// Sensitive content is NOT stored — only metadata, counts, and hashes.
function record(event) {
  const prev = lastHash();
  const entry = {
    ts: new Date().toISOString(),
    prev_hash: prev,
    ...event,
  };
  // Hash is over the entry (minus the hash field) chained to prev
  const material = JSON.stringify(entry);
  entry.hash = crypto.createHash('sha256').update(prev + material).digest('hex');

  fs.appendFileSync(LOG, JSON.stringify(entry) + '\n', { mode: 0o600 });
  return entry.hash;
}

// Verify the chain: returns { ok, length, brokenAt }
function verify() {
  let data;
  try { data = fs.readFileSync(LOG, 'utf8').trim(); }
  catch { return { ok: true, length: 0, brokenAt: null }; }
  if (!data) return { ok: true, length: 0, brokenAt: null };

  const lines = data.split('\n');
  let prev = 'GENESIS';
  for (let i = 0; i < lines.length; i++) {
    const entry = JSON.parse(lines[i]);
    const stored = entry.hash;
    const copy = { ...entry };
    delete copy.hash;
    const material = JSON.stringify(copy);
    const expect = crypto.createHash('sha256').update(prev + material).digest('hex');
    if (entry.prev_hash !== prev || stored !== expect) {
      return { ok: false, length: lines.length, brokenAt: i };
    }
    prev = stored;
  }
  return { ok: true, length: lines.length, brokenAt: null };
}

module.exports = { record, verify };
