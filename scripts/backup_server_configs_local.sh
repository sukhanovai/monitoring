#!/bin/bash
# backup_server_configs_local.sh
# Server Monitoring System
# Copyright (c) 2025 Aleksandr Sukhanov — License: MIT
#
# Локальный бэкап конфигов и историй консолей САМОГО бэкап-сервера в каталог
# /zfs/nfs/backup/<host>/ (на бэкап-сервере нет VM и LXC-контейнеров, поэтому
# доставка по SSH и обход гостей не нужны — копируем локально).
#
# Шлёт итоговое письмо в формате расширения config_console_backup_monitor:
#   Тема: Config backup <host> OK|PARTIAL|ERROR
#   Тело (UTF-8, ключ:значение) — то же, что у copy_configs_ssh.sh, но
#   «Способ доставки: local».
#
# Конфиги кладутся с сохранением прошлой версии как <file>~ (rsync --backup),
# истории консолей — новым файлом с timestamp (накопление, без перезаписи).
# Истории берутся у всех пользователей хоста из getent passwd (root, postgres, …).

set -o pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

##################### настройки по умолчанию #####################
# Любую переменную можно переопределить в /etc/backup_server_configs.conf.

DEST_BASE="/zfs/nfs/backup"                     # база; финал: $DEST_BASE/<host>
COLLECT_PSQL_HISTORY=1                           # 1 — забирать ~/.psql_history (обычно postgres)
MAIL_TO="katok@202020.ru"
DEBUG_LOG="${DEBUG_LOG:-/var/log/backup_server_configs.log}"
DRY_RUN="${DRY_RUN:-0}"                          # 1 — не копировать/не слать письмо, печать плана

# Каталоги/файлы конфигов хоста (собираются, если существуют).
HOST_CONFIG_DIRS=("/etc/pve/lxc" "/etc/pve/qemu-server" "/opt")
HOST_CONFIG_FILES=("/etc/network/interfaces" "/etc/fstab" "/etc/postfix/main.cf")

CONF_FILE="/etc/backup_server_configs.conf"
# shellcheck source=/dev/null
[ -f "$CONF_FILE" ] && . "$CONF_FILE"

##################### служебное ##################################

HOST="$(hostname -s)"
MAIL_FROM="root@${HOST}"
RUN_START="$(date '+%Y-%m-%d %H:%M:%S')"
DEST="${DEST_BASE}/${HOST}"
TS() { date '+%Y-%m-%d[%H:%M:%S]'; }

STAGING="$(mktemp -d /tmp/backup_server_configs.XXXXXX)"
trap 'rm -rf "$STAGING"' EXIT

VM_CONFIG_COUNT=0
LXC_CONFIG_COUNT=0
HISTORY_FILE_COUNT=0
ERROR_COUNT=0
PROBLEM_ITEMS=()

log() { echo "$(TS) $*" >> "$DEBUG_LOG"; }
add_problem() { PROBLEM_ITEMS+=("$1"); ERROR_COUNT=$((ERROR_COUNT + 1)); }
mkstage() { mkdir -p "$STAGING/$1" 2>>"$DEBUG_LOG"; }

echo "=========================================" >> "$DEBUG_LOG"
log "Script started on $HOST (DRY_RUN=$DRY_RUN, staging=$STAGING, dest=$DEST)"

##################### сбор конфигов хоста ########################

for dir in "${HOST_CONFIG_DIRS[@]}"; do
    [ -d "$dir" ] || continue
    sub="config/$(echo "$dir" | sed 's#^/##; s#/#_#g')"
    mkstage "$sub"
    if cp -a "$dir/." "$STAGING/$sub/" 2>>"$DEBUG_LOG"; then
        log "Собран каталог $dir → $sub"
    else
        log "ОШИБКА копирования каталога $dir"
        add_problem "dir:$dir"
    fi
done

# Подсчёт конфигов LXC/VM из staging (на pmxcfs `find -type f` бывает пустым).
LXC_CONFIG_COUNT=$(find "$STAGING/config/etc_pve_lxc" -maxdepth 1 -name '*.conf' 2>/dev/null | wc -l | tr -d ' ')
VM_CONFIG_COUNT=$(find "$STAGING/config/etc_pve_qemu-server" -maxdepth 1 -name '*.conf' 2>/dev/null | wc -l | tr -d ' ')

mkstage "config"
for f in "${HOST_CONFIG_FILES[@]}"; do
    [ -f "$f" ] || continue
    cp -a "$f" "$STAGING/config/" 2>>"$DEBUG_LOG" || add_problem "file:$f"
done

crontab -l > "$STAGING/config/crontab" 2>>"$DEBUG_LOG" || log "crontab пуст/недоступен"

##################### истории консолей хоста #####################
# Пользователи хоста из passwd (root, postgres, … — с реальным домашним
# каталогом). Для каждого забираем .bash_history и опц. .psql_history.

while IFS="$(printf '\t')" read -r user home; do
    [ -n "$home" ] || continue
    dest="historyes/$user"
    if [ -f "$home/.bash_history" ]; then
        mkstage "$dest"
        if cp -a "$home/.bash_history" "$STAGING/$dest/.bash_history.$(TS)" 2>>"$DEBUG_LOG"; then
            HISTORY_FILE_COUNT=$((HISTORY_FILE_COUNT + 1))
        else
            add_problem "history:$user/bash"
        fi
    fi
    if [ "$COLLECT_PSQL_HISTORY" = "1" ] && [ -f "$home/.psql_history" ]; then
        mkstage "$dest"
        cp -a "$home/.psql_history" "$STAGING/$dest/.psql_history.$(TS)" 2>>"$DEBUG_LOG" \
            && HISTORY_FILE_COUNT=$((HISTORY_FILE_COUNT + 1))
    fi
done < <(getent passwd \
    | awk -F: '$6 != "" && $6 != "/" && $6 != "/nonexistent" && $6 != "/dev/null" \
               { print $1"\t"$6 }' \
    | sort -u -t"$(printf '\t')" -k2,2)

##################### локальная доставка #########################
# rsync локально: конфиги перезаписываются с бэкапом прошлой версии в <file>~,
# истории (уникальный timestamp) копятся; без --delete старое не трогаем.

DELIVERY_OK=1
if [ "$DRY_RUN" = "1" ]; then
    log "DRY_RUN: пропуск копирования в $DEST"
    find "$STAGING" -maxdepth 3 >> "$DEBUG_LOG" 2>&1
else
    mkdir -p "$DEST" 2>>"$DEBUG_LOG" || { DELIVERY_OK=0; add_problem "mkdir:$DEST"; }
    if [ "$DELIVERY_OK" -eq 1 ]; then
        if rsync -a --backup --suffix='~' "$STAGING/" "$DEST/" >>"$DEBUG_LOG" 2>&1; then
            log "rsync (local) успешно: $DEST"
        else
            DELIVERY_OK=0
            log "ОШИБКА rsync (local) в $DEST"
            add_problem "rsync:$DEST"
        fi
    fi
fi

##################### итоговое письмо ############################

RUN_END="$(date '+%Y-%m-%d %H:%M:%S')"

if [ "$DELIVERY_OK" -eq 0 ]; then
    STATUS="ERROR"
elif [ "$ERROR_COUNT" -gt 0 ]; then
    STATUS="PARTIAL"
else
    STATUS="OK"
fi

PROBLEM_STR=""
if [ "${#PROBLEM_ITEMS[@]}" -gt 0 ]; then
    PROBLEM_STR="$(printf '%s, ' "${PROBLEM_ITEMS[@]}")"
    PROBLEM_STR="${PROBLEM_STR%, }"
fi

SUBJECT="Config backup ${HOST} ${STATUS}"

send_report() {
    if command -v sendmail >/dev/null 2>&1; then
        sendmail -t <<EOF
From: ${MAIL_FROM}
To: ${MAIL_TO}
Subject: ${SUBJECT}
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit

Хост: ${HOST}
Способ доставки: local
Приёмник: ${DEST}
Начало: ${RUN_START}
Завершено: ${RUN_END}
VM конфигов: ${VM_CONFIG_COUNT}
LXC конфигов: ${LXC_CONFIG_COUNT}
Контейнеров с историей: 0
Файлов истории: ${HISTORY_FILE_COUNT}
Ошибок: ${ERROR_COUNT}
Проблемные элементы: ${PROBLEM_STR}
EOF
    else
        printf '%s\n' \
            "Хост: ${HOST}" \
            "Способ доставки: local" \
            "Приёмник: ${DEST}" \
            "Начало: ${RUN_START}" \
            "Завершено: ${RUN_END}" \
            "VM конфигов: ${VM_CONFIG_COUNT}" \
            "LXC конфигов: ${LXC_CONFIG_COUNT}" \
            "Контейнеров с историей: 0" \
            "Файлов истории: ${HISTORY_FILE_COUNT}" \
            "Ошибок: ${ERROR_COUNT}" \
            "Проблемные элементы: ${PROBLEM_STR}" \
            | mail -s "$SUBJECT" "$MAIL_TO"
    fi
}

if [ "$DRY_RUN" = "1" ]; then
    log "DRY_RUN: письмо не отправлено. Subject='${SUBJECT}'"
    echo "SUBJECT: $SUBJECT"
    echo "VM=$VM_CONFIG_COUNT LXC=$LXC_CONFIG_COUNT files=$HISTORY_FILE_COUNT errors=$ERROR_COUNT"
    echo "problems: $PROBLEM_STR"
else
    send_report
fi

log "Завершено: ${SUBJECT} (vm=${VM_CONFIG_COUNT} lxc=${LXC_CONFIG_COUNT} files=${HISTORY_FILE_COUNT} errors=${ERROR_COUNT})"
################### Конец скрипта ###################################
