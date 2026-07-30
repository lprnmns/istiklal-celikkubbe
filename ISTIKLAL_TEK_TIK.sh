#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/release/one_click/linux/ISTIKLAL_TEK_TIK.sh"
