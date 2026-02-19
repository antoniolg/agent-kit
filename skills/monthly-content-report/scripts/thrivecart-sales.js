#!/usr/bin/env node
/**
 * Obtiene ventas de AI Expert desde ThriveCart API
 * Solo cuenta "charge" (primera compra / pago único), ignora "rebill" (plazos posteriores)
 * Usage: node thrivecart-sales.js --start YYYY-MM-DD --end YYYY-MM-DD [--json]
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

async function fetchPage(apiKey, productId, page) {
  const url = `https://thrivecart.com/api/external/transactions?product=${productId}&page=${page}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  if (!res.ok) throw new Error(`ThriveCart API error: ${res.status} ${await res.text()}`);
  return res.json();
}

async function getSales(apiKey, productId, startDate, endDate) {
  const startTs = new Date(startDate + 'T00:00:00').getTime() / 1000;
  const endTs = new Date(endDate + 'T23:59:59').getTime() / 1000;

  const sales = [];
  let page = 1;
  let totalPages = null;

  while (true) {
    const data = await fetchPage(apiKey, productId, page);

    // Calculate total pages from meta.total and meta.results (API doesn't return meta.pages)
    if (totalPages === null) {
      const total = data.meta?.total || 0;
      const perPage = data.meta?.results || 25;
      totalPages = Math.ceil(total / perPage);
    }

    if (!data.transactions?.length) break;

    for (const tx of data.transactions || []) {
      // Solo primera compra (charge), ignorar rebills y failed
      if (tx.transaction_type !== 'charge') continue;

      // Filtrar por rango de fechas
      if (tx.timestamp < startTs || tx.timestamp > endTs) continue;

      sales.push({
        date: tx.date.split(' ')[0], // YYYY-MM-DD
        email: tx.customer?.email || '',
        name: tx.customer?.name || `${tx.customer?.['first name'] || ''} ${tx.customer?.['last name'] || ''}`.trim(),
        payment_type: tx.related_to_recur ? 'plazos' : 'unico',
        pricing_option: tx.item_pricing_option_name || '',
        amount: parseFloat(tx.amount_str) || 0,
        order_id: tx.order_id,
      });
    }

    // Si el timestamp mínimo de esta página es anterior a startDate, podemos parar
    const minTs = Math.min(...(data.transactions?.map(t => t.timestamp) || [Infinity]));
    if (minTs < startTs) break;

    page++;
    if (page > totalPages) break;
  }

  return sales;
}

async function main() {
  const cfg = loadConfig();
  const opts = parseArgs();

  const apiKey = cfg.thrivecart_api_key || process.env.THRIVECART_API_KEY;
  const productId = cfg.thrivecart_product_id || 9;

  if (!apiKey) {
    console.error('Missing ThriveCart API key. Set thrivecart_api_key in ~/.config/skills/config.json');
    process.exit(1);
  }

  // Default: mes anterior
  const now = new Date();
  const firstOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastOfPrevMonth = new Date(firstOfThisMonth - 1);
  const firstOfPrevMonth = new Date(lastOfPrevMonth.getFullYear(), lastOfPrevMonth.getMonth(), 1);

  const start = opts.start || firstOfPrevMonth.toISOString().split('T')[0];
  const end = opts.end || lastOfPrevMonth.toISOString().split('T')[0];

  const sales = await getSales(apiKey, productId, start, end);
  const total = sales.reduce((acc, s) => acc + s.amount, 0);

  if (opts.json) {
    console.log(JSON.stringify({ start, end, count: sales.length, total_eur: total, sales }, null, 2));
  } else {
    console.log(`Ventas AI Expert (primeras compras) del ${start} al ${end}`);
    console.log(`Total: ${sales.length} ventas / ${total.toFixed(2)} EUR\n`);
    console.log('Fecha      | Nombre                        | Tipo    | Importe | Email');
    console.log('-----------|-------------------------------|---------|---------|------');
    for (const s of sales) {
      const name = s.name.padEnd(29).slice(0, 29);
      const type = s.payment_type.padEnd(7);
      console.log(`${s.date} | ${name} | ${type} | ${String(s.amount.toFixed(2)).padStart(7)} | ${s.email}`);
    }
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
