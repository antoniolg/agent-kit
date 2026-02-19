#!/usr/bin/env node
/**
 * Obtiene pageviews diarios de Umami para /cursos/expert/ai
 * Usage: node umami-pageviews.js --start YYYY-MM-DD --end YYYY-MM-DD
 */

import { readFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

function loadConfig() {
  try {
    const cfg = JSON.parse(readFileSync(join(homedir(), '.config/skills/config.json'), 'utf8'));
    return cfg.monthly_content_report || {};
  } catch {
    return {};
  }
}

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--start') opts.start = args[++i];
    else if (args[i] === '--end') opts.end = args[++i];
    else if (args[i] === '--json') opts.json = true;
  }
  return opts;
}

async function getToken(baseUrl, user, pass) {
  const res = await fetch(`${baseUrl}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: user, password: pass }),
  });
  if (!res.ok) throw new Error(`Auth failed: ${res.status} ${await res.text()}`);
  const data = await res.json();
  return data.token;
}

async function getPageviews(baseUrl, token, websiteId, path, startDate, endDate) {
  const startAt = new Date(startDate + 'T00:00:00+01:00').getTime();
  const endAt = new Date(endDate + 'T23:59:59+01:00').getTime();
  const encodedPath = encodeURIComponent(`eq.${path}`);

  const url = `${baseUrl}/api/websites/${websiteId}/pageviews?startAt=${startAt}&endAt=${endAt}&unit=day&timezone=Europe%2FMadrid&path=${encodedPath}`;

  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Pageviews failed: ${res.status} ${await res.text()}`);
  return res.json();
}

async function main() {
  const cfg = loadConfig();
  const opts = parseArgs();

  const baseUrl = cfg.umami_url || process.env.UMAMI_URL;
  const user = cfg.umami_user || process.env.UMAMI_USER;
  const pass = cfg.umami_pass || process.env.UMAMI_PASS;
  const websiteId = cfg.umami_website_id || process.env.UMAMI_WEBSITE_ID;
  const path = cfg.umami_path || '/cursos/expert/ai';

  if (!baseUrl || !user || !pass || !websiteId) {
    console.error('Missing Umami config. Set monthly_content_report in ~/.config/skills/config.json');
    process.exit(1);
  }

  // Default: last month
  const now = new Date();
  const firstOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastOfPrevMonth = new Date(firstOfThisMonth - 1);
  const firstOfPrevMonth = new Date(lastOfPrevMonth.getFullYear(), lastOfPrevMonth.getMonth(), 1);

  const start = opts.start || firstOfPrevMonth.toISOString().split('T')[0];
  const end = opts.end || lastOfPrevMonth.toISOString().split('T')[0];

  const token = await getToken(baseUrl, user, pass);
  const data = await getPageviews(baseUrl, token, websiteId, path, start, end);

  const pageviews = data.pageviews || [];
  const sessions = data.sessions || [];

  // Merge by date
  const byDate = {};
  for (const p of pageviews) {
    const date = new Date(p.x).toISOString().split('T')[0];
    if (!byDate[date]) byDate[date] = { date, pageviews: 0, sessions: 0 };
    byDate[date].pageviews += p.y;
  }
  for (const s of sessions) {
    const date = new Date(s.x).toISOString().split('T')[0];
    if (!byDate[date]) byDate[date] = { date, pageviews: 0, sessions: 0 };
    byDate[date].sessions += s.y;
  }

  const result = Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
  const total = result.reduce((acc, r) => acc + r.pageviews, 0);

  if (opts.json) {
    console.log(JSON.stringify({ start, end, path, total, days: result }, null, 2));
  } else {
    console.log(`Pageviews for ${path} from ${start} to ${end}`);
    console.log(`Total: ${total} pageviews\n`);
    console.log('Date       | Pageviews | Sessions');
    console.log('-----------|-----------|----------');
    for (const d of result) {
      console.log(`${d.date} | ${String(d.pageviews).padStart(9)} | ${d.sessions}`);
    }
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
