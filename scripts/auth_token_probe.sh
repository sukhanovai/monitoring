#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://localhost}"
LOGIN="${2:-}"
PASSWORD="${3:-}"

if [[ -z "$LOGIN" || -z "$PASSWORD" ]]; then
  echo "[INFO] login/password не переданы — выполню только discovery без авторизации."
  echo "[INFO] Для полного прогона: $0 https://localhost <login> <password>"
fi



print_base_url_hint() {
  cat <<TXT
[INFO] Используется BASE_URL: $BASE_URL
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

probe_auth_errors() {
  local url="$1"
  printf "\n== Probe auth requirement: %s/v1/monitoring/availability?scope=all ==\n" "$url"
  curl -sS -i --max-time 15 "$url/v1/monitoring/availability?scope=all" | sed -n '1,20p' || true
}

try_json_endpoint() {
  local endpoint="$1"
  local payload="$2"

  printf "\n== POST %s ==\n" "$endpoint"
  local response
  response=$(curl -sS --max-time 15 -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL$endpoint" \
    -H 'Content-Type: application/json' \
    -d "$payload") || true

  echo "$response"
}

try_form_endpoint() {
  local endpoint="$1"

  printf "\n== POST(form) %s ==\n" "$endpoint"
  local response
  response=$(curl -sS --max-time 15 -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL$endpoint" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "grant_type=password" \
    --data-urlencode "username=$LOGIN" \
    --data-urlencode "password=$PASSWORD") || true

  echo "$response"
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

Manual JWT decode one-liner:
python3 -c 'import base64,json,sys; p=sys.argv[1].split(".")[1]; p+="="*(-len(p)%4); print(json.dumps(json.loads(base64.urlsafe_b64decode(p)),indent=2,ensure_ascii=False))' <JWT>
TXT
