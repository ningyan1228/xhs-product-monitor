#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium

if [ ! -f .env ]; then
  cp .env.example .env
fi

mkdir -p data/raw docs/data
echo "安装完成。首次登录请运行：HEADLESS=false bash scripts/run.sh"
