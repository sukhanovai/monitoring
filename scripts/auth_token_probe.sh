#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://localhost"
LOGIN=""
PASSWORD=""
INSECURE="auto" # auto|true|false
HOST_HEADER=""
API_PREFIX=""
FORCE_PROBE="false"

usage() {
  cat <<'TXT'
Usage:
  ./scripts/auth_token_probe.sh [--insecure|--strict-tls] [--host <domain>] [--prefix </api>] [--force-probe] [base_url] [login] [password]

Examples:
  ./scripts/auth_token_probe.sh
  ./scripts/auth_token_probe.sh --insecure https://localhost demo demo
  ./scripts/auth_token_probe.sh --strict-tls https://api.202020.ru:8443 demo demo
  ./scripts/auth_token_probe.sh --insecure --host api.202020.ru https://localhost:443 demo demo
  ./scripts/auth_token_probe.sh --insecure --host api.202020.ru --prefix /api https://localhost:443 demo demo
  ./scripts/auth_token_probe.sh --insecure --host api.202020.ru https://localhost:443 demo demo --force-probe
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
    --host)
      if [[ $# -lt 2 ]]; then
        echo "[ERROR] --host требует значение, например: --host api.202020.ru"
        exit 1
      fi
      HOST_HEADER="$2"
      shift 2
      ;;
    --prefix)
      if [[ $# -lt 2 ]]; then
        echo "[ERROR] --prefix требует значение, например: --prefix /api"
        exit 1
      fi
      API_PREFIX="$2"
      shift 2
      ;;
    --force-probe)
      FORCE_PROBE="true"
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


if [[ -n "$API_PREFIX" ]]; then
  if [[ "$API_PREFIX" != /* ]]; then
    API_PREFIX="/$API_PREFIX"
  fi
  API_PREFIX="${API_PREFIX%/}"
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

CURL_HEADER_ARGS=()
if [[ -n "$HOST_HEADER" ]]; then
  CURL_HEADER_ARGS+=("-H" "Host: $HOST_HEADER")
fi

if [[ -z "$LOGIN" || -z "$PASSWORD" ]]; then
  echo "[INFO] login/password не переданы — выполню только discovery без авторизации."
  echo "[INFO] Для полного прогона: $0 --insecure https://localhost <login> <password>"
fi


PROBE_HTTP_CODE=""
PROBE_IS_APACHE="false"

quick_path_discovery() {
  local candidates=("/" "/health" "/api/health" "/bff/health" "/v1/health" "/openapi.json" "/api/openapi.json" "/swagger" "/docs")
  echo "[INFO] Быстрая проверка возможных маршрутов на текущем BASE_URL..."
  for path in "${candidates[@]}"; do
    local code
    code=$(curl "${CURL_TLS_ARGS[@]}" "${CURL_HEADER_ARGS[@]}" -sS -o /dev/null -w "%{http_code}" --max-time 8 "${BASE_URL}${path}" || true)
    printf "  - %s -> HTTP %s\n" "${BASE_URL}${path}" "${code:-000}"
  done
}

print_base_url_hint() {
  cat <<TXT
[INFO] Используется BASE_URL: $BASE_URL
[INFO] TLS-режим: $([[ "$INSECURE" == "true" ]] && echo "insecure (-k, self-signed ОК)" || echo "strict")
[INFO] Для запуска на сервере указывай локальный/внутренний адрес (например, https://localhost:8443 или https://192.168.20.2:8443).
[INFO] Внешний адрес (https://api.202020.ru:8443) актуален для клиентов извне этого сервера.
[INFO] Host header override: ${HOST_HEADER:-<не задан>}
[INFO] API prefix: ${API_PREFIX:-<нет>}
[INFO] Force probe: $FORCE_PROBE
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
  if echo "$response" | grep -Eq '"access_token"[[:space:]]*:'; then
    echo "[OK] Похоже, найден access_token в ответе. Скопируй значение поля access_token."
  fi
}

analyze_response_hint() {
  local response="$1"

  if echo "$response" | grep -q 'Server: Apache'; then
    PROBE_IS_APACHE="true"
    echo "[WARN] Похоже, запрос ушёл в Apache по умолчанию, а не в BFF/API."
    echo "[WARN] Проверь порт/виртуальный хост. Часто нужный API слушает на :8443."
    echo "[HINT] Попробуй: ./scripts/auth_token_probe.sh --insecure https://localhost:8443 <login> <password>"
    echo "[HINT] Если BFF сидит за Apache/Nginx по доменному vhost, задай Host header:"
    echo "[HINT] ./scripts/auth_token_probe.sh --insecure --host api.202020.ru https://localhost:443 <login> <password>"
  fi

  if echo "$response" | grep -q 'HTTP_STATUS:404'; then
    echo "[WARN] Endpoint не найден (404). Возможно, BASE_URL/port/path неверный."
    echo "[HINT] Попробуй добавить префикс API: --prefix /api или --prefix /bff"
  fi

  if echo "$response" | grep -q 'HTTP_STATUS:000'; then
    echo "[WARN] Нет TCP/HTTP ответа (HTTP_STATUS:000)."
    echo "[HINT] Проверь, какой порт реально слушает локально: ss -lntp | grep -E '(:443|:8443)'"
  fi
}


build_url() {
  local endpoint="$1"
  echo "${BASE_URL}${API_PREFIX}${endpoint}"
}

probe_auth_errors() {
  local url="$1"
  printf "\n== Probe auth requirement: %s%s/v1/monitoring/availability?scope=all ==\n" "$url" "$API_PREFIX"
  local response
  response=$(curl "${CURL_TLS_ARGS[@]}" "${CURL_HEADER_ARGS[@]}" -sS -i --max-time 15 "$(build_url "/v1/monitoring/availability?scope=all")") || true
  echo "$response" | sed -n '1,30p'
  local code
  code=$(echo "$response" | sed -nE "s#^HTTP/[0-9.]+ ([0-9]{3}).*#\1#p" | head -n1)
  PROBE_HTTP_CODE="$code"
  analyze_response_hint "$response"
}

try_json_endpoint() {
  local endpoint="$1"
  local payload="$2"

  printf "\n== POST %s ==\n" "$endpoint"
  local response
  response=$(curl "${CURL_TLS_ARGS[@]}" "${CURL_HEADER_ARGS[@]}" -sS --max-time 15 -w "\nHTTP_STATUS:%{http_code}" -X POST "$(build_url "$endpoint")" \
    -H 'Content-Type: application/json' \
    -d "$payload") || true

  echo "$response"
  extract_token_hint "$response"
  local code
  code=$(echo "$response" | sed -nE "s#^HTTP/[0-9.]+ ([0-9]{3}).*#\1#p" | head -n1)
  PROBE_HTTP_CODE="$code"
  analyze_response_hint "$response"
}

try_form_endpoint() {
  local endpoint="$1"

  printf "\n== POST(form) %s ==\n" "$endpoint"
  local response
  response=$(curl "${CURL_TLS_ARGS[@]}" "${CURL_HEADER_ARGS[@]}" -sS --max-time 15 -w "\nHTTP_STATUS:%{http_code}" -X POST "$(build_url "$endpoint")" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "grant_type=password" \
    --data-urlencode "username=$LOGIN" \
    --data-urlencode "password=$PASSWORD") || true

  echo "$response"
  extract_token_hint "$response"
  local code
  code=$(echo "$response" | sed -nE "s#^HTTP/[0-9.]+ ([0-9]{3}).*#\1#p" | head -n1)
  PROBE_HTTP_CODE="$code"
  analyze_response_hint "$response"
}

print_base_url_hint
probe_auth_errors "$BASE_URL"

if [[ "$PROBE_IS_APACHE" == "true" && "$PROBE_HTTP_CODE" == "404" && "$FORCE_PROBE" != "true" ]]; then
  echo "[WARN] Похоже, это не auth/BFF endpoint (Apache 404 на probe)."
  quick_path_discovery
  echo "[HINT] Чтобы всё равно прогнать все POST-варианты, добавь --force-probe"
  exit 0
fi

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
