# Backend Kurulum Komutlari

## Onerilen Yol: uv

Resmi uv installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Mevcut shell oturumunda `uv` bulunmazsa:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Backend dependency sync:

```bash
cd backend
uv sync --extra dev
uv run pytest
```

Backend dev server:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

## Fallback: venv + pip

`uv` kullanilamiyorsa:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e 'backend[dev]'
cd backend
../.venv/bin/python -m pytest
../.venv/bin/python -m uvicorn app.main:app --reload
```

Faz 1 guvenlik varsayimlari kurulum yonteminden bagimsizdir:

- `DISARMED`
- `NO_FIRE`
- `dry_run=true`
- `hardware_enabled=false`
