# Troubleshooting

## Tunnel URL returns errors

- Wait 5-10 seconds after tunnel creation.
- Confirm app is reachable locally on the same port.
- Recreate tunnel (URL can become invalid if process dies).

## App process appears alive but port is closed

Use `tmux` pane logs, not only process list. A parent process can exist while the server child has exited.

Recommended checks:

```bash
tmux capture-pane -pt dev-tunnel:app -S -120
lsof -nP -iTCP:<port> -sTCP:LISTEN
curl -I http://127.0.0.1:<port>
```

## Host blocked by dev server

This can happen in stacks that validate `Host` headers (for example Vite/Astro or webpack-dev-server).
If you see a host-not-allowed error, add an allowlist entry for `.trycloudflare.com` in that stack's dev server config.

Example (Vite/Astro):

```js
server: { allowedHosts: ['.trycloudflare.com'] }
```

Then restart the dev server. If no host-blocking error exists, do not modify config.

## Keep one tunnel per app port

Multiple tunnel processes for the same app can create confusion about which URL is active.
Kill old sessions before creating a new one.
