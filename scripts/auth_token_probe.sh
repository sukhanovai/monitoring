#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://localhost"
LOGIN=""
PASSWORD=""
INSECURE="auto" # auto|true|false

usage() {
  cat <<'TXT'
Usage:
  ./scripts/auth_token_probe.sh [--insecure|--strict-tls] [base_url] [login] [password]

Examples:
  ./scripts/auth_token_probe.sh
  ./scripts/auth_token_probe.sh --insecure https://localhost demo demo
  ./scripts/auth_token_probe.sh --strict-tls https://api.202020.ru:8443 demo demo
TXT
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --insecure|-k)
      INSECURE="true"
      shift
      ;;
    --strict-tls)
      INSECURE="false"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ ${#POSITIONAL[@]} -ge 1 ]]; then BASE_URL="${POSITIONAL[0]}"; fi
if [[ ${#POSITIONAL[@]} -ge 2 ]]; then LOGIN="${POSITIONAL[1]}"; fi
if [[ ${#POSITIONAL[@]} -ge 3 ]]; then PASSWORD="${POSITIONAL[2]}"; fi
if [[ ${#POSITIONAL[@]} -gt 3 ]]; then
  echo "[WARN] Лишние позиционные аргументы будут проигнорированы: ${POSITIONAL[*]:3}"
fi

if [[ "$INSECURE" == "auto" ]]; then
  if [[ "$BASE_URL" =~ ^https://(localhost|127\.0\.0\.1|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.) ]]; then
    INSECURE="true"
  else
    INSECURE="false"
  fi
fi

CURL_TLS_ARGS=()
if [[ "$INSECURE" == "true" ]]; then
  CURL_TLS_ARGS+=("-k")
fi

if [[ -z "$LOGIN" || -z "$PASSWORD" ]]; then
  echo "[INFO] login/password не переданы — выполню только discovery без авторизации."
  echo "[INFO] Для полного прогона: $0 --insecure https://localhost <login> <password>"
fi

print_base_url_hint() {
  cat <<TXT
[INFO] Используется BASE_URL: $BASE_URL
[INFO] TLS-режим: $([[ "$INSECURE" == "true" ]] && echo "insecure (-k, self-signed ОК)" || echo "strict")
[INFO] Для запуска на сервере указывай локальный/внутренний адрес (например, https://localhost или https://192.168.20.2).
[INFO] Внешний адрес (https://api.202020.ru:8443) актуален для клиентов извне этого сервера.
TXT
}

print_credentials_hint() {
  cat <<'TXT'

Где взять <login> и <password>:
1) Это не данные из этого репозитория. Нужна учётка из вашего auth/BFF окружения.
2) Обычно их выдаёт владелец бэкенда (тестовый пользователь или операторская учётка).
3) Если login flow ещё не готов — попросите одноразовый Bearer token для Android.
TXT
}

extract_token_hint() {
  local response="$1"
  if echo "$response" | rg -q '"access_token"\s*:'; then
    echo "[OK] Похоже, найден access_token в ответе. Скопируй значение поля access_token."
  fi
}

probe_auth_errors() {
  local url="$1"
  printf "\n== Probe auth requirement: %s/v1/monitoring/availability?scope=all ==\n" "$url"
  curl "${CURL_TLS_ARGS[@]}" -sS -i --max-time 15 "$url/v1/monitoring/availability?scope=all" | sed -n '1,30p' || true
}

try_json_endpoint() {
  local endpoint="$1"
  local payload="$2"

  printf "\n== POST %s ==\n" "$endpoint"
  local response
  response=$(curl "${CURL_TLS_ARGS[@]}" -sS --max-time 15 -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL$endpoint" \
    -H 'Content-Type: application/json' \
    -d "$payload") || true

  echo "$response"
  extract_token_hint "$response"
}

try_form_endpoint() {
  local endpoint="$1"

  printf "\n== POST(form) %s ==\n" "$endpoint"
  local response
  response=$(curl "${CURL_TLS_ARGS[@]}" -sS --max-time 15 -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL$endpoint" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "grant_type=password" \
    --data-urlencode "username=$LOGIN" \
    --data-urlencode "password=$PASSWORD") || true

  echo "$response"
  extract_token_hint "$response"
}

print_base_url_hint
probe_auth_errors "$BASE_URL"

JSON_ENDPOINTS=(
  "/v1/auth/token"
  "/v1/auth/login"
  "/auth/token"
  "/auth/login"
  "/token"
)

if [[ -n "$LOGIN" && -n "$PASSWORD" ]]; then
  for ep in "${JSON_ENDPOINTS[@]}"; do
    try_json_endpoint "$ep" "{\"username\":\"$LOGIN\",\"password\":\"$PASSWORD\"}"
    try_json_endpoint "$ep" "{\"login\":\"$LOGIN\",\"password\":\"$PASSWORD\"}"
    try_json_endpoint "$ep" "{\"email\":\"$LOGIN\",\"password\":\"$PASSWORD\"}"
    try_form_endpoint "$ep"
  done
else
  print_credentials_hint
fi

cat <<'TXT'

JWT decode (без ошибки shell):
TOKEN='<вставь_сюда_JWT>'
python3 -c 'import base64,json,os; t=os.environ["TOKEN"]; p=t.split(".")[1]; p+="="*(-len(p)%4); print(json.dumps(json.loads(base64.urlsafe_b64decode(p)),indent=2,ensure_ascii=False))'
TXT
