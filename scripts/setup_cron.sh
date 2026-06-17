#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CRON_LINE="0 9 * * * cd ${PROJECT_DIR} && bash scripts/run.sh >> logs/cron.log 2>&1"

mkdir -p "${PROJECT_DIR}/logs"

(crontab -l 2>/dev/null | grep -Fv "scripts/run.sh" || true; echo "${CRON_LINE}") | crontab -

echo "已写入 cron："
echo "${CRON_LINE}"
