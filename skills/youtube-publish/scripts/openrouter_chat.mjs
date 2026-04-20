#!/usr/bin/env node

import process from 'node:process';

function printUsage() {
  console.error(`Usage:
  node openrouter_chat.mjs <model> [prompt]

Examples:
  node --env-file=.env openrouter_chat.mjs openai/gpt-4.1-nano "Escribe un post sobre MCP"
  cat prompt.txt | node --env-file=.env openrouter_chat.mjs anthropic/claude-sonnet-4

Environment variables:
  OPENROUTER_API_KEY          Required
  OPENROUTER_SYSTEM_PROMPT    Optional
  OPENROUTER_TEMPERATURE      Optional
  OPENROUTER_MAX_TOKENS       Optional
  OPENROUTER_SITE_URL         Optional (HTTP-Referer)
  OPENROUTER_APP_NAME         Optional (X-OpenRouter-Title)
`);
}

function parseNumber(value) {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function normalizeContent(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .map((part) => {
        if (typeof part === 'string') return part;
        if (part?.type === 'text') return part.text ?? '';
        return '';
      })
      .join('')
      .trim();
  }
  return '';
}

async function readStdin() {
  if (process.stdin.isTTY) return '';

  let data = '';
  for await (const chunk of process.stdin) {
    data += chunk;
  }
  return data.trim();
}

const args = process.argv.slice(2);

if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  printUsage();
  process.exit(args.length === 0 ? 1 : 0);
}

const [model, ...promptParts] = args;
const promptFromArgs = promptParts.join(' ').trim();
const prompt = promptFromArgs || (await readStdin());

if (!prompt) {
  console.error('Missing prompt. Pass it as an argument or via stdin.');
  process.exit(1);
}

const apiKey = process.env.OPENROUTER_API_KEY;

if (!apiKey) {
  console.error('Missing OPENROUTER_API_KEY.');
  console.error('Tip: node --env-file=.env openrouter_chat.mjs <model> "your prompt"');
  process.exit(1);
}

const payload = {
  model,
  messages: [],
};

if (process.env.OPENROUTER_SYSTEM_PROMPT?.trim()) {
  payload.messages.push({
    role: 'system',
    content: process.env.OPENROUTER_SYSTEM_PROMPT.trim(),
  });
}

payload.messages.push({
  role: 'user',
  content: prompt,
});

const temperature = parseNumber(process.env.OPENROUTER_TEMPERATURE);
if (temperature !== undefined) {
  payload.temperature = temperature;
}

const maxTokens = parseNumber(process.env.OPENROUTER_MAX_TOKENS);
if (maxTokens !== undefined) {
  payload.max_completion_tokens = Math.max(1, Math.floor(maxTokens));
}

const headers = {
  Authorization: `Bearer ${apiKey}`,
  'Content-Type': 'application/json',
};

if (process.env.OPENROUTER_SITE_URL?.trim()) {
  headers['HTTP-Referer'] = process.env.OPENROUTER_SITE_URL.trim();
}

if (process.env.OPENROUTER_APP_NAME?.trim()) {
  headers['X-OpenRouter-Title'] = process.env.OPENROUTER_APP_NAME.trim();
}

const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers,
  body: JSON.stringify(payload),
});

const rawBody = await response.text();
let body;

try {
  body = JSON.parse(rawBody);
} catch {
  body = { raw: rawBody };
}

if (!response.ok) {
  console.error(`OpenRouter error (${response.status} ${response.statusText})`);
  console.error(JSON.stringify(body, null, 2));
  process.exit(1);
}

const message = body?.choices?.[0]?.message;
const text = normalizeContent(message?.content);

if (!text) {
  console.error('No text content returned.');
  console.error(JSON.stringify(body, null, 2));
  process.exit(1);
}

process.stdout.write(text.endsWith('\n') ? text : `${text}\n`);
