#!/bin/bash
# copy_configs_ssh.sh
# Server Monitoring System v8.62.80
# Copyright (c) 2025 Aleksandr Sukhanov — License: MIT
#
# Единый скрипт для ВСЕХ хостов и бэкап-серверов: собирает конфиги VM/LXC и
# истории консолей, доставляет их по SSH (rsync) на приёмник и шлёт итоговое
# письмо для расширения config_console_backup_monitor (Server Monitoring System).
#
# Письмо уходит на katok@202020.ru одним сообщением на каждый прогон:
#   Тема: Config backup <host> OK|PARTIAL|ERROR
#   Тело (UTF-8): ключ:значение построчно (Хост/Способ доставки/Приёмник/Начало/
#                 Завершено/VM конфигов/LXC конфигов/Контейнеров с историей/
#                 Файлов истории/Ошибок/Проблемные элементы).
#
# Скрипт БАЙТ-ИДЕНТИЧЕН на всех машинах. Всё, что отличается между хостами и
# бэкап-серверами, задаётся в опциональном /etc/copy_configs.conf (см.
# copy_configs.conf.example). На бэкап-серверах в conf указывают приёмник = NAS.
# Ручной список контейнеров (CONTAINER_IDS) больше НЕ нужен — гости и пути их
# разделов определяются автоматически.

set -o pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

##################### настройки по умолчанию #####################
# Любую из этих переменных можно переопределить в /etc/copy_configs.conf.

RECEIVER_HOST="sr-bup"                          # приёмник SSH (на бэкап-серверах → NAS)
RECEIVER_USER="root"
RECEIVER_BASE="/zfs/nfs/backup"                 # база на приёмнике; финал: $RECEIVER_BASE/<host>
SSH_KEY="/root/.ssh/id_rsa"                     # приватный ключ для неинтерактивного rsync
SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15"

COLLECT_PSQL_HISTORY=0                           # 1 — забирать ~/.psql_history у postgres
MAIL_TO="katok@202020.ru"
DEBUG_LOG="${DEBUG_LOG:-/var/log/copy_configs_ssh.log}"
DRY_RUN="${DRY_RUN:-0}"                          # 1 — не слать rsync/письмо, только печать плана

# Каталоги/файлы конфигов хоста (собираются, если существуют).
HOST_CONFIG_DIRS=("/etc/pve/lxc" "/etc/pve/qemu-server" "/opt")
HOST_CONFIG_FILES=("/etc/network/interfaces" "/etc/fstab" "/etc/postfix/main.cf")

CONF_FILE="/etc/copy_configs.conf"
# shellcheck source=/dev/null
[ -f "$CONF_FILE" ] && . "$CONF_FILE"

##################### служебное ##################################

HOST="$(hostname -s)"
MAIL_FROM="root@${HOST}"
RUN_START="$(date '+%Y-%m-%d %H:%M:%S')"
TS() { date '+%Y-%m-%d[%H:%M:%S]'; }

STAGING="$(mktemp -d /tmp/copy_configs.XXXXXX)"
trap 'rm -rf "$STAGING"' EXIT

# Счётчики результата и список проблемных элементов.
VM_CONFIG_COUNT=0
LXC_CONFIG_COUNT=0
HISTORY_CONTAINER_COUNT=0
HISTORY_FILE_COUNT=0
ERROR_COUNT=0
PROBLEM_ITEMS=()

log() { echo "$(TS) $*" >> "$DEBUG_LOG"; }
add_problem() { PROBLEM_ITEMS+=("$1"); ERROR_COUNT=$((ERROR_COUNT + 1)); }

mkstage() { mkdir -p "$STAGING/$1" 2>>"$DEBUG_LOG"; }

echo "=========================================" >> "$DEBUG_LOG"
log "Script started on $HOST (DRY_RUN=$DRY_RUN, staging=$STAGING)"

##################### сбор конфигов хоста ########################

# Каталоги конфигов: /etc/pve/lxc, /etc/pve/qemu-server, /opt.
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

# Подсчёт конфигов LXC/VM — по числу реально собранных в staging файлов *.conf.
# (Считаем из staging, а не из /etc/pve: на pmxcfs `find -type f` бывает пустым.)
LXC_CONFIG_COUNT=$(find "$STAGING/config/etc_pve_lxc" -maxdepth 1 -name '*.conf' 2>/dev/null | wc -l | tr -d ' ')
VM_CONFIG_COUNT=$(find "$STAGING/config/etc_pve_qemu-server" -maxdepth 1 -name '*.conf' 2>/dev/null | wc -l | tr -d ' ')

# Одиночные файлы конфигов.
mkstage "config"
for f in "${HOST_CONFIG_FILES[@]}"; do
    [ -f "$f" ] || continue
    if cp -a "$f" "$STAGING/config/" 2>>"$DEBUG_LOG"; then
        log "Собран файл $f"
    else
        add_problem "file:$f"
    fi
done

# crontab и история bash самого хоста.
mkstage "config"
crontab -l > "$STAGING/config/crontab" 2>>"$DEBUG_LOG" || log "crontab пуст/недоступен"
if [ -f "$HOME/.bash_history" ]; then
    cp -a "$HOME/.bash_history" "$STAGING/config/.bash_history.$(TS)" 2>>"$DEBUG_LOG" \
        || add_problem "host_bash_history"
fi

##################### истории консолей LXC #######################
# Без ручного списка контейнеров: перечисляем через `pct list`. Для запущенных
# контейнеров читаем истории через `pct exec` (обходит нетиповые subvol-пути).
# Для остановленных — определяем rootfs из `pct config` + zfs mountpoint, с
# фолбэком на glob /rpool/subvol-<id>-disk-* (покрывает -disk-0, -disk-1 и пр.).

# Печатает "user<TAB>home" для всех пользователей контейнера с реальным домашним
# каталогом. Источник — passwd, поэтому ловит и root (/root), и postgres
# (/var/lib/postgresql), и обычных из /home — без хардкода путей. Дубли по
# домашнему каталогу схлопываются.
container_users_running() {
    local id="$1"
    pct exec "$id" -- getent passwd 2>>"$DEBUG_LOG" \
        | awk -F: '$6 != "" && $6 != "/" && $6 != "/nonexistent" && $6 != "/dev/null" \
                   { print $1"\t"$6 }' \
        | sort -u -t"$(printf '\t')" -k2,2
}

# То же для остановленного контейнера — из <rootfs>/etc/passwd.
container_users_offline() {
    local rootfs="$1"
    [ -f "$rootfs/etc/passwd" ] || return 0
    awk -F: '$6 != "" && $6 != "/" && $6 != "/nonexistent" && $6 != "/dev/null" \
             { print $1"\t"$6 }' "$rootfs/etc/passwd" \
        | sort -u -t"$(printf '\t')" -k2,2
}

# Определяет путь rootfs остановленного контейнера на ФС бэкап-хоста.
container_rootfs_offline() {
    local id="$1" rootfs ds pool mp glob
    rootfs="$(pct config "$id" 2>>"$DEBUG_LOG" | awk -F': ' '/^rootfs:/{print $2}' | cut -d',' -f1)"
    # rootfs вида "local-zfs:subvol-141-disk-0"
    ds="${rootfs#*:}"
    if [ -n "$ds" ]; then
        # Пытаемся получить mountpoint датасета через zfs (надёжно, без хардкода пула).
        for pool in $(zfs list -H -o name 2>/dev/null | grep -E "/${ds}$"); do
            mp="$(zfs get -H -o value mountpoint "$pool" 2>/dev/null)"
            [ -n "$mp" ] && [ "$mp" != "-" ] && [ -d "$mp" ] && { printf '%s\n' "$mp"; return 0; }
        done
    fi
    # Фолбэк: glob по типовому корню (учитывает любой суффикс -disk-N).
    for glob in /rpool/subvol-"${id}"-disk-* /rpool/data/subvol-"${id}"-disk-*; do
        [ -d "$glob" ] && { printf '%s\n' "$glob"; return 0; }
    done
    return 1
}

# Сохраняет содержимое одного файла истории в staging с timestamp
# (истории всегда новый файл — не перезаписываются). $3 — exit code источника.
stage_history() {
    local id="$1" user="$2" kind="$3" status="$4"
    local dest="lxc_historyes/$id/$user"
    if [ "$status" -eq 0 ]; then
        HISTORY_FILE_COUNT=$((HISTORY_FILE_COUNT + 1))
        return 0
    fi
    rm -f "$STAGING/$dest/.${kind}."* 2>/dev/null
    return 1
}

collect_container_histories() {
    local id="$1" status="$2" got=0 user home dest rootfs hpath

    if [ "$status" = "running" ]; then
        while IFS="$(printf '\t')" read -r user home; do
            [ -n "$home" ] || continue
            dest="lxc_historyes/$id/$user"
            # .bash_history
            if pct exec "$id" -- test -f "$home/.bash_history" 2>>"$DEBUG_LOG"; then
                mkstage "$dest"
                pct exec "$id" -- cat "$home/.bash_history" \
                    > "$STAGING/$dest/.bash_history.$(TS)" 2>>"$DEBUG_LOG"
                stage_history "$id" "$user" "bash_history" "$?" && got=1
            fi
            # .psql_history (опционально, best-effort) — обычно у postgres.
            if [ "$COLLECT_PSQL_HISTORY" = "1" ] \
               && pct exec "$id" -- test -f "$home/.psql_history" 2>>"$DEBUG_LOG"; then
                mkstage "$dest"
                pct exec "$id" -- cat "$home/.psql_history" \
                    > "$STAGING/$dest/.psql_history.$(TS)" 2>>"$DEBUG_LOG"
                stage_history "$id" "$user" "psql_history" "$?" && got=1
            fi
        done < <(container_users_running "$id")
    else
        rootfs="$(container_rootfs_offline "$id")" || {
            log "Не удалось определить rootfs остановленного контейнера $id"
            add_problem "lxc-$id/rootfs"
            return 1
        }
        while IFS="$(printf '\t')" read -r user home; do
            [ -n "$home" ] || continue
            dest="lxc_historyes/$id/$user"
            hpath="$rootfs$home"
            if [ -f "$hpath/.bash_history" ]; then
                mkstage "$dest"
                cp -a "$hpath/.bash_history" "$STAGING/$dest/.bash_history.$(TS)" 2>>"$DEBUG_LOG"
                stage_history "$id" "$user" "bash_history" "$?" && got=1
            fi
            if [ "$COLLECT_PSQL_HISTORY" = "1" ] && [ -f "$hpath/.psql_history" ]; then
                mkstage "$dest"
                cp -a "$hpath/.psql_history" "$STAGING/$dest/.psql_history.$(TS)" 2>>"$DEBUG_LOG"
                stage_history "$id" "$user" "psql_history" "$?" && got=1
            fi
        done < <(container_users_offline "$rootfs")
    fi

    [ "$got" = "1" ] && HISTORY_CONTAINER_COUNT=$((HISTORY_CONTAINER_COUNT + 1))
    return 0
}

if command -v pct >/dev/null 2>&1; then
    # Формат `pct list`: "VMID  Status  Lock  Name"; шапку пропускаем.
    while read -r cid cstatus _rest; do
        [ "$cid" = "VMID" ] && continue
        [[ "$cid" =~ ^[0-9]+$ ]] || continue
        log "Контейнер $cid ($cstatus): сбор историй"
        collect_container_histories "$cid" "$cstatus" || add_problem "lxc-$cid"
    done < <(pct list 2>>"$DEBUG_LOG")
else
    log "pct не найден — не PVE-хост, пропускаем сбор историй контейнеров"
fi

##################### доставка по SSH (rsync) ####################

RECEIVER_PATH="${RECEIVER_BASE}/${HOST}"
RECEIVER="${RECEIVER_USER}@${RECEIVER_HOST}:${RECEIVER_PATH}"
DELIVERY_OK=1

if [ "$DRY_RUN" = "1" ]; then
    log "DRY_RUN: пропуск rsync на $RECEIVER"
    echo "DRY_RUN staging tree:" >> "$DEBUG_LOG"
    find "$STAGING" -maxdepth 3 >> "$DEBUG_LOG" 2>&1
else
    # --backup --suffix='~': при перезаписи конфига его прошлая версия остаётся
    #   рядом как <file>~ (как старый `cp -b`). Файлы историй имеют уникальный
    #   timestamp в имени, поэтому никогда не перезаписываются — копятся.
    # Без --delete: ранее собранные истории на приёмнике не удаляются.
    if rsync -az --backup --suffix='~' \
        -e "ssh -i ${SSH_KEY} ${SSH_OPTS}" \
        "$STAGING/" "${RECEIVER}/" >>"$DEBUG_LOG" 2>&1; then
        log "rsync успешно: $RECEIVER"
    else
        DELIVERY_OK=0
        log "ОШИБКА rsync на $RECEIVER"
        add_problem "rsync:$RECEIVER_HOST"
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
Способ доставки: ssh-rsync
Приёмник: ${RECEIVER}
Начало: ${RUN_START}
Завершено: ${RUN_END}
VM конфигов: ${VM_CONFIG_COUNT}
LXC конфигов: ${LXC_CONFIG_COUNT}
Контейнеров с историей: ${HISTORY_CONTAINER_COUNT}
Файлов истории: ${HISTORY_FILE_COUNT}
Ошибок: ${ERROR_COUNT}
Проблемные элементы: ${PROBLEM_STR}
EOF
    else
        printf '%s\n' \
            "Хост: ${HOST}" \
            "Способ доставки: ssh-rsync" \
            "Приёмник: ${RECEIVER}" \
            "Начало: ${RUN_START}" \
            "Завершено: ${RUN_END}" \
            "VM конфигов: ${VM_CONFIG_COUNT}" \
            "LXC конфигов: ${LXC_CONFIG_COUNT}" \
            "Контейнеров с историей: ${HISTORY_CONTAINER_COUNT}" \
            "Файлов истории: ${HISTORY_FILE_COUNT}" \
            "Ошибок: ${ERROR_COUNT}" \
            "Проблемные элементы: ${PROBLEM_STR}" \
            | mail -s "$SUBJECT" "$MAIL_TO"
    fi
}

if [ "$DRY_RUN" = "1" ]; then
    log "DRY_RUN: письмо не отправлено. Subject='${SUBJECT}' problems='${PROBLEM_STR}'"
    echo "SUBJECT: $SUBJECT"
    echo "VM=$VM_CONFIG_COUNT LXC=$LXC_CONFIG_COUNT containers=$HISTORY_CONTAINER_COUNT files=$HISTORY_FILE_COUNT errors=$ERROR_COUNT"
    echo "problems: $PROBLEM_STR"
else
    send_report
fi

log "Завершено: ${SUBJECT} (vm=${VM_CONFIG_COUNT} lxc=${LXC_CONFIG_COUNT} containers=${HISTORY_CONTAINER_COUNT} files=${HISTORY_FILE_COUNT} errors=${ERROR_COUNT})"
################### Конец скрипта ###################################
