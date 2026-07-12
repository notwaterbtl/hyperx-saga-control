#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

export PYTHONPATH="$PWD"
exec python -m hyperx_saga_control "$@"
