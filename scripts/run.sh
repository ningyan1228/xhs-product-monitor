#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -d .venv ]; then
  source .venv/bin/activate
fi

python src/main.py

git add data/products.csv docs/data/products.json

if git diff --cached --quiet; then
  echo "数据没有变化，跳过 commit。"
  exit 0
fi

git commit -m "update product data"
git push
