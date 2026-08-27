# API 202020 — чистый TLS-план для `api.202020.ru:8443`

Документ фиксирует только рабочий план без предварительных этапов и исторического дебага.

## Цель

Подготовить и зафиксировать стабильный HTTPS-контур для BFF:
- домен `api.202020.ru`;
- порт `8443`;
- валидный сертификат с SAN `api.202020.ru`;
- подтверждённый доступ из внешней сети и Android-клиента.

---

## Шаг 1. DNS и внешняя связность

1. Проверить, что `api.202020.ru` резолвится в целевой публичный IP.
2. Проверить, что `8443/tcp` доступен извне.
3. Если сервис за NAT — проверить проброс `WAN:8443 -> LAN:<bff_host>:8443`.

Команды:
```bash
dig +short api.202020.ru A
nc -vz api.202020.ru 8443
```

Критерий готовности:
- домен стабильно резолвится в нужный IP;
- порт `8443` открыт из внешней сети.

---

## Шаг 2. Выпуск и подключение сертификата

1. Выпустить/обновить сертификат для `api.202020.ru`.
2. Подключить сертификат в reverse proxy (`ssl_certificate`, `ssl_certificate_key`).
3. Применить конфигурацию без ошибок.

Команды:
```bash
nginx -t
systemctl reload nginx
```

Критерий готовности:
- Nginx-конфиг валиден;
- сертификат подключён именно к vhost `api.202020.ru:8443`.

---

## Шаг 3. TLS-валидация снаружи

1. Проверить, какой сертификат отдается на `8443`.
2. Проверить SAN, issuer и срок действия.
3. Проверить HTTPS-запрос к health endpoint.

Команды:
```bash
openssl s_client -connect api.202020.ru:8443 -servername api.202020.ru -showcerts </dev/null
openssl s_client -connect api.202020.ru:8443 -servername api.202020.ru </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
curl -vk https://api.202020.ru:8443/health
```

Критерий готовности:
- в SAN присутствует `DNS:api.202020.ru`;
- TLS-handshake успешен;
- endpoint отвечает через HTTPS.

---

## Шаг 4. Автопродление и клиентская проверка

1. Прогнать dry-run автопродления сертификата.
2. Проверить минимум один реальный запрос с Android-клиента.

Команды:
```bash
certbot renew --dry-run
# или
acme.sh --renew -d api.202020.ru --dry-run
```

Критерий готовности:
- dry-run renewal проходит;
- Android не получает SSLHandshakeException/CertPathValidatorException.

---


## Операционный блок: алерт в cron + ручное продление сейчас

### 1) Проверка в cron с exit code 1 при истечении

Скрипт ниже возвращает `0`, если сертификат ещё валиден, и `1`, если уже истёк (или не удалось получить сертификат):

```bash
#!/usr/bin/env bash
set -euo pipefail

host="api.202020.ru"
port="8443"
name="api.202020.ru"

if ! cert=$(echo | openssl s_client -connect "${host}:${port}" -servername "${name}" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null); then
  echo "CRIT: cannot read certificate from ${host}:${port}" >&2
  exit 1
fi

end_date="${cert#notAfter=}"
end_ts=$(date -u -d "$end_date" +%s)
now_ts=$(date -u +%s)
left=$((end_ts - now_ts))

if [ "$left" -le 0 ]; then
  echo "CRIT: certificate expired at ${end_date}"
  exit 1
fi

echo "OK: certificate valid, seconds_left=${left}, end_date_utc=${end_date}"
exit 0
```

Пример cron (каждые 15 минут + лог в файл):

```cron
*/15 * * * * /usr/local/bin/check_api_202020_cert.sh >> /var/log/check_api_202020_cert.log 2>&1
```

### 2) Как продлить сертификат прямо сейчас

Вариант для certbot + nginx:

```bash
certbot certonly --nginx -d api.202020.ru --force-renewal
nginx -t && systemctl reload nginx
```

Проверка после перезагрузки nginx:

```bash
echo | openssl s_client -connect api.202020.ru:8443 -servername api.202020.ru 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

Если используете `acme.sh`, эквивалент:

```bash
acme.sh --renew -d api.202020.ru --force
# затем deploy/install сертификата в путь nginx + reload nginx
```

## Финальный чек-лист готовности

- [ ] `dig` показывает корректный IP для `api.202020.ru`.
- [ ] `8443` доступен из внешней сети.
- [ ] На `:8443` отдается сертификат с SAN `api.202020.ru`.
- [ ] `curl -vk https://api.202020.ru:8443/health` проходит.
- [ ] `renew --dry-run` успешен.
- [ ] Android делает минимум один успешный HTTPS-запрос.

Если любой пункт не закрыт, переход к следующему этапу разработки откладывается.
