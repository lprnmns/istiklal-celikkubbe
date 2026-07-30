# Faz 2 Frontend Skeleton ve Dashboard

Frontend `frontend/` altinda Vue 3 + Vite + TypeScript + Pinia + TailwindCSS ile kuruludur.

## Kurulum

pnpm corepack ile etkinlestirilebilir:

```bash
corepack enable pnpm
pnpm --version
```

Dependency kurulumu:

```bash
cd frontend
pnpm install
```

## Gelistirme Sunucusu

```bash
cd frontend
pnpm dev
```

Varsayilan Vite adresi:

```text
http://localhost:5173
```

## Backend Baglantisi

Frontend varsayilan olarak su WebSocket endpointine baglanir:

```text
ws://localhost:8000/ws
```

Backend farkli adreste calisiyorsa:

```bash
cd frontend
VITE_BACKEND_WS_URL=ws://127.0.0.1:8000/ws pnpm dev
```

Backend calismiyorsa UI mock telemetry uretmez. WebSocket reconnect dener ve ekranda `backend disconnected` durumunu gosterir.

## Build ve Typecheck

```bash
cd frontend
pnpm typecheck
pnpm build
```

## Faz 2 Ekranlari

- Dashboard: sistem state, safety state, Pico status, vision mock status, WebSocket connection ve recent events kartlari.
- System: backend system state detaylari.
- Safety: safety gates panelinin ilk surumu.
- Pico: Faz 3 pinout calismasi icin placeholder telemetry ekrani.
- Vision: Faz 5 overlay calismasi icin placeholder status ekrani.
- Logs: WebSocket event listesi.

Bu fazda gercek donanim komutu, motor komutu, fire komutu, detayli Pico SVG pinout veya vision overlay eklenmemistir.
