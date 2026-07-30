# ISTIKLAL Frontend

Vue 3 + Vite + TypeScript + Pinia + TailwindCSS dashboard skeleton.

## Setup

```bash
corepack enable pnpm
pnpm install
```

## Development

```bash
pnpm dev
```

Default URL:

```text
http://localhost:5173
```

## Backend WebSocket

Default endpoint:

```text
ws://localhost:8000/ws
```

Override:

```bash
VITE_BACKEND_WS_URL=ws://127.0.0.1:8000/ws pnpm dev
```

## Verification

```bash
pnpm typecheck
pnpm build
```
