#!/bin/bash
# transfer_backup_to_nas.sh
# Server Monitoring System
# Copyright (c) 2025 Aleksandr Sukhanov — License: MIT
#
# Передача локальных бэкапов (/zfs/nfs/backup) на NAS по NFS — НАДЁЖНО.
#
# Раньше NAS держался постоянно примонтированным через fstab:
#   192.168.20.16:/raid0/data/_NAS_NFS_Exports_ /NAS nfs rsize=8192,wsize=8192,\
#       timeo=30,retrans=5,soft,intr,noatime 0 0
# Постоянный мягкий (soft) маунт может «протухнуть» (stale handle) и тихо
# отдавать ошибки. Этот скрипт монтирует NAS ПО ТРЕБОВАНИЮ на время прогона,
# проверяет что монтирование реально рабочее (не только в таблице, но и с
# тестовой записью), переносит данные rsync'ом и затем отмонтирует. Если NAS
# уже примонтирован (например, штатным fstab) — переиспользует его и НЕ
# отмонтирует.
#
# ВАЖНО: это ФИНАЛЬНАЯ передача всех собранных конфигов/историй на NAS, поэтому
# письмо идёт в формате расширения config_console_backup_monitor (НЕ
# nas_transfer_monitor — тот про бэкапы 1С из move_and_clear_backups.sh, у него
# отдельная тема "NAS transfer ..."). Здесь:
#   Тема: Config backup <host> OK|PARTIAL|ERROR
#   Тело (UTF-8, ключ:значение):
#     Хост / Способ доставки: nas-final / Приёмник / Начало / Завершено /
#     VM конфигов: 0 / LXC конфигов: 0 / Контейнеров с историей: 0 /
#     Файлов истории: <перенесено каталогов> / Ошибок / Проблемные элементы.
# Признак «Способ доставки: nas-final» позволяет боту выделить эту запись как
# общую финальную передачу всех конфигов на NAS.

set -o pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

##################### настройки по умолчанию #####################
# Любую переменную можно переопределить в /etc/transfer_backup_to_nas.conf.

NFS_SERVER="192.168.20.16"
NFS_EXPORT="/raid0/data/_NAS_NFS_Exports_"
MOUNTPOINT="/NAS"                               # точка монтирования NFS
NAS_SUBDIR="backup"                             # подкаталог назначения на NAS
SRC="${SRC:-/zfs/nfs/backup}"                   # что переносим (с хвостовым / не нужно)
# Опции NFS: как в fstab, но без устаревшего intr; bg/soft чтобы не зависать.
MOUNT_OPTS="rsize=8192,wsize=8192,timeo=30,retrans=5,soft,noatime"
MOUNT_RETRIES=3
MOUNT_TIMEOUT=60                                # сек на попытку mount
RSYNC_DELETE=0                                  # 1 — зеркалить (удалять лишнее на NAS)
MAIL_TO="katok@202020.ru"
DEBUG_LOG="${DEBUG_LOG:-/var/log/transfer_backup_to_nas.log}"
DRY_RUN="${DRY_RUN:-0}"                          # 1 — без mount/rsync/umount/письма

CONF_FILE="/etc/transfer_backup_to_nas.conf"
# shellcheck source=/dev/null
[ -f "$CONF_FILE" ] && . "$CONF_FILE"

##################### служебное ##################################

HOST="$(hostname -s)"
MAIL_FROM="root@${HOST}"
RUN_START="$(date '+%Y-%m-%d %H:%M:%S')"
DEST="${MOUNTPOINT%/}/${NAS_SUBDIR}"

BASES_PROCESSED=0
ERROR_COUNT=0
PROBLEM_ITEMS=()
WE_MOUNTED=0
NAS_MOUNTED="нет"

TS() { date '+%Y-%m-%d[%H:%M:%S]'; }
log() { echo "$(TS) $*" >> "$DEBUG_LOG"; }
add_problem() { PROBLEM_ITEMS+=("$1"); ERROR_COUNT=$((ERROR_COUNT + 1)); }

echo "=========================================" >> "$DEBUG_LOG"
log "Script started on $HOST (DRY_RUN=$DRY_RUN, src=$SRC, dest=$DEST)"

# Реально ли смонтирован MOUNTPOINT: отдельная ФС (device id != корневой) И
# доступен на запись (создаём и удаляем пробный файл). Так ловим stale-маунт.
nas_is_usable() {
    local dev root_dev probe
    mountpoint -q "$MOUNTPOINT" 2>/dev/null || return 1
    dev="$(stat -c %d "$MOUNTPOINT" 2>/dev/null)"
    root_dev="$(stat -c %d / 2>/dev/null)"
    [ -n "$dev" ] && [ "$dev" != "$root_dev" ] || return 1
    probe="${MOUNTPOINT%/}/.nas_write_test.$$"
    ( : > "$probe" ) 2>/dev/null || return 1
    rm -f "$probe" 2>/dev/null
    return 0
}

cleanup() {
    if [ "$WE_MOUNTED" -eq 1 ]; then
        if umount "$MOUNTPOINT" 2>>"$DEBUG_LOG"; then
            log "NAS отмонтирован: $MOUNTPOINT"
        else
            log "umount не удался, пробуем lazy umount -l"
            umount -l "$MOUNTPOINT" 2>>"$DEBUG_LOG" || log "lazy umount тоже не удался"
        fi
    fi
}
trap cleanup EXIT

##################### монтирование NAS ###########################

mount_nas() {
    mkdir -p "$MOUNTPOINT" 2>>"$DEBUG_LOG"

    if nas_is_usable; then
        log "NAS уже примонтирован и доступен на запись — переиспользуем"
        WE_MOUNTED=0
        return 0
    fi

    local attempt=1
    while [ "$attempt" -le "$MOUNT_RETRIES" ]; do
        log "mount NAS, попытка $attempt/$MOUNT_RETRIES"
        if timeout "$MOUNT_TIMEOUT" mount -t nfs \
            -o "$MOUNT_OPTS" "${NFS_SERVER}:${NFS_EXPORT}" "$MOUNTPOINT" 2>>"$DEBUG_LOG"; then
            if nas_is_usable; then
                WE_MOUNTED=1
                log "NAS примонтирован: ${NFS_SERVER}:${NFS_EXPORT} → $MOUNTPOINT"
                return 0
            fi
            log "Смонтировано, но не прошло проверку записи — отмонтируем и повторим"
            umount "$MOUNTPOINT" 2>>"$DEBUG_LOG" || umount -l "$MOUNTPOINT" 2>>"$DEBUG_LOG"
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    return 1
}

##################### основной прогон ############################

DELIVERY_OK=1

if [ ! -d "$SRC" ]; then
    log "ОШИБКА: источник $SRC не существует"
    add_problem "src:$SRC"
    DELIVERY_OK=0
fi

if [ "$DRY_RUN" = "1" ]; then
    log "DRY_RUN: монтирование и rsync пропущены"
    if [ -d "$SRC" ]; then
        BASES_PROCESSED=$(find "$SRC" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    fi
    NAS_MOUNTED="(dry-run)"
elif [ "$DELIVERY_OK" -eq 1 ]; then
    if mount_nas; then
        NAS_MOUNTED="да"
        mkdir -p "$DEST" 2>>"$DEBUG_LOG" || add_problem "mkdir:$DEST"

        rsync_opts=(-a --no-owner --no-group)
        [ "$RSYNC_DELETE" = "1" ] && rsync_opts+=(--delete)

        # Переносим каждый каталог верхнего уровня отдельно — чтобы при сбое
        # одного остальные дошли, и чтобы посчитать проблемные элементы.
        shopt -s nullglob
        for entry in "$SRC"/*/; do
            name="$(basename "$entry")"
            BASES_PROCESSED=$((BASES_PROCESSED + 1))
            if ! rsync "${rsync_opts[@]}" "$entry" "$DEST/$name/" >>"$DEBUG_LOG" 2>&1; then
                log "ОШИБКА rsync для $name"
                add_problem "$name"
            fi
        done

        # Файлы в корне источника (если есть) — отдельным проходом.
        if find "$SRC" -mindepth 1 -maxdepth 1 -type f -print -quit 2>/dev/null | grep -q .; then
            if ! rsync "${rsync_opts[@]}" --exclude='*/' "$SRC"/ "$DEST"/ >>"$DEBUG_LOG" 2>&1; then
                add_problem "root-files"
            fi
        fi

        [ "$ERROR_COUNT" -gt 0 ] && DELIVERY_OK=1   # частичная — не общий провал
    else
        log "ОШИБКА: не удалось примонтировать NAS"
        NAS_MOUNTED="нет"
        DELIVERY_OK=0
    fi
fi

##################### итоговое письмо ############################

RUN_END="$(date '+%Y-%m-%d %H:%M:%S')"

# Статус: ERROR — NAS недоступен или были сбои переноса; PARTIAL — доставка
# прошла, но часть каталогов не перенеслась; OK — всё успешно.
if [ "$NAS_MOUNTED" = "нет" ] || [ "$DELIVERY_OK" -eq 0 ]; then
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

# Письмо в формате config_console_backup_monitor (финальная передача на NAS).
SUBJECT="Config backup ${HOST} ${STATUS}"
RECEIVER_REPORT="${NFS_SERVER}:${NFS_EXPORT} → ${DEST}"
[ "$DRY_RUN" = "1" ] && RECEIVER_REPORT="${DEST} (dry-run)"

send_report() {
    if command -v sendmail >/dev/null 2>&1; then
        sendmail -t <<EOF
From: ${MAIL_FROM}
To: ${MAIL_TO}
Subject: ${SUBJECT}
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit

Хост: ${HOST}
Способ доставки: nas-final
Приёмник: ${RECEIVER_REPORT}
Начало: ${RUN_START}
Завершено: ${RUN_END}
VM конфигов: 0
LXC конфигов: 0
Контейнеров с историей: 0
Файлов истории: ${BASES_PROCESSED}
Ошибок: ${ERROR_COUNT}
Проблемные элементы: ${PROBLEM_STR}
EOF
    else
        printf '%s\n' \
            "Хост: ${HOST}" \
            "Способ доставки: nas-final" \
            "Приёмник: ${RECEIVER_REPORT}" \
            "Начало: ${RUN_START}" \
            "Завершено: ${RUN_END}" \
            "VM конфигов: 0" \
            "LXC конфигов: 0" \
            "Контейнеров с историей: 0" \
            "Файлов истории: ${BASES_PROCESSED}" \
            "Ошибок: ${ERROR_COUNT}" \
            "Проблемные элементы: ${PROBLEM_STR}" \
            | mail -s "$SUBJECT" "$MAIL_TO"
    fi
}

if [ "$DRY_RUN" = "1" ]; then
    log "DRY_RUN: письмо не отправлено. Subject='${SUBJECT}' bases=${BASES_PROCESSED}"
    echo "SUBJECT: $SUBJECT"
    echo "delivery=nas-final dirs=$BASES_PROCESSED errors=$ERROR_COUNT"
    echo "problems: $PROBLEM_STR"
else
    send_report
fi

log "Завершено: ${SUBJECT} (delivery=nas-final dirs=${BASES_PROCESSED} errors=${ERROR_COUNT})"
################### Конец скрипта ###################################
