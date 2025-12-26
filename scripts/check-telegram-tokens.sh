#!/usr/bin/env bash
set -euo pipefail

pattern='[0-9]{9,10}:[A-Za-z0-9_-]{30,}'

if [[ "${1:-}" == "--staged" ]]; then
  if git diff --cached -U0 --no-color | rg -n "${pattern}"; then
    echo "Найдены похожие на токены Telegram строки в staged diff." >&2
    exit 1
  fi
  exit 0
fi

if rg -n "${pattern}" .; then
  echo "Найдены похожие на токены Telegram строки в репозитории." >&2
  exit 1
fi
