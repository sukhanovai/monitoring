#!/bin/bash
# move_and_clear_backups.sh
# Перенос бэкапов 1С с сервера бэкапов на NAS + очистка + итоговое письмо
# для расширения nas_transfer_monitor (Server Monitoring System).
#
# Письмо уходит на katok@202020.ru одним сообщением на каждый прогон:
#   Тема: NAS transfer <host> OK|ERROR|SKIPPED
#   Тело (UTF-8): ключ:значение построчно (Хост/NAS примонтирован/Начало/
#                 Завершено/Баз обработано/Ошибок/Проблемные базы).

# Добавляем полный PATH
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Создаём файл лога для отладки
DEBUG_LOG="/var/log/backup_debug.log"
echo "=========================================" >> "$DEBUG_LOG"
echo "$(date +%d-%m-%Y[%H:%M:%S]) Script started" >> "$DEBUG_LOG"
echo "PATH: $PATH" >> "$DEBUG_LOG"
echo "UID: $UID, EUID: $EUID" >> "$DEBUG_LOG"

# Переменные и параметры
pbs="/zfs/nfs/backup.1c"
nas="/NAS/backup.1c"
path_7_bases="$pbs/1C_Bases.77"

# Параметры письма-отчёта
MAIL_TO="katok@202020.ru"
HOST="$(hostname -s)"
MAIL_FROM="root@${HOST}"
RUN_START="$(date '+%Y-%m-%d %H:%M:%S')"

# Базы, для которых отсутствие свежего бэкапа НЕ считается проблемой
# (не пишется в ERROR-лог и не попадает в письмо).
# Список можно расширять, не трогая логику: добавьте имена баз в файл
# $IGNORE_BASES_FILE по одному в строке (пустые строки и '#'-комментарии
# игнорируются). Имена соответствуют суффиксу каталога current.<base>.
IGNORE_BASES=("Agreement" "Hold" "Koyvan")
IGNORE_BASES_FILE="/opt/nas_transfer_ignore.txt"
if [ -f "$IGNORE_BASES_FILE" ]; then
    while IFS= read -r _ib; do
        _ib="${_ib%%#*}"                       # отрезаем комментарий
        _ib="$(echo "$_ib" | xargs)"           # обрезаем пробелы
        [ -n "$_ib" ] && IGNORE_BASES+=("$_ib")
    done < "$IGNORE_BASES_FILE"
fi

# Проверяет, входит ли база в список игнорируемых.
is_ignored_base() {
    local b="$1" x
    for x in "${IGNORE_BASES[@]}"; do
        [ "$x" = "$b" ] && return 0
    done
    return 1
}

# Проверка доступности NAS.
# ВАЖНО: точкой монтирования NFS является /NAS, а каталог назначения
# $nas=/NAS/backup.1c — это подкаталог внутри неё. Поэтому
# `mountpoint -q "$nas"` всегда возвращает false. Считаем NAS
# примонтированным, если каталог назначения лежит на отдельной ФС
# (другой номер устройства), а не на корневой (когда NFS не подключён).
nas_is_mounted() {
    local nas_dev root_dev
    nas_dev="$(stat -c %d "$nas" 2>/dev/null)"
    root_dev="$(stat -c %d / 2>/dev/null)"
    [ -n "$nas_dev" ] && [ "$nas_dev" != "$root_dev" ]
}

# Проверяем существование директорий
echo "Checking directories:" >> "$DEBUG_LOG"
for dir in "$pbs" "$nas" "$path_7_bases"; do
    if [ -d "$dir" ]; then
        echo "  OK: $dir exists" >> "$DEBUG_LOG"
        ls -la "$dir" | head -5 >> "$DEBUG_LOG"
    else
        echo "  FAIL: $dir does NOT exist" >> "$DEBUG_LOG"
    fi
done

# Проверяем монтирование NAS
if nas_is_mounted; then
    echo "NAS mounted OK" >> "$DEBUG_LOG"
else
    echo "ERROR: NAS NOT mounted!" >> "$DEBUG_LOG"
fi

echo "$(date +%d-%m-%Y[%H:%M:%S]) BEGIN" >> "$nas/success_time.log" 2>> "$DEBUG_LOG"

# Предобработка баз 1С 7.7: раскладываем zip по longtime/current
echo "Processing 1C 7.7 backups..." >> "$DEBUG_LOG"
if [ -d "$path_7_bases" ]; then
    ls -la "$path_7_bases" >> "$DEBUG_LOG" 2>&1
    shopt -s nullglob
    backups_7_files=("$path_7_bases"/*.zip)
    echo "Found ${#backups_7_files[@]} zip files" >> "$DEBUG_LOG"

    for file_name_7 in "${backups_7_files[@]}"; do
        echo "Processing: $file_name_7" >> "$DEBUG_LOG"
        file_name_7=$(basename "$file_name_7")
        base7=${file_name_7%-*}
        date_and_extension=${file_name_7#*-}
        day_from_filename=${date_and_extension%.*.*.*}
        echo "  base: $base7, day: $day_from_filename" >> "$DEBUG_LOG"

        if [[ $day_from_filename = "01" || $day_from_filename = "15" ]]; then
            mkdir -p "$pbs/longtime.$base7"
            mv "$pbs/1C_Bases.77/$file_name_7" "$pbs/longtime.$base7/" 2>> "$DEBUG_LOG"
            echo "  Moved to longtime.$base7" >> "$DEBUG_LOG"
        else
            mkdir -p "$pbs/current.$base7"
            mv "$pbs/1C_Bases.77/$file_name_7" "$pbs/current.$base7/" 2>> "$DEBUG_LOG"
            echo "  Moved to current.$base7" >> "$DEBUG_LOG"
        fi
    done
else
    echo "Directory $path_7_bases does not exist!" >> "$DEBUG_LOG"
fi

# Обработка хранения: копируем current.* на NAS и чистим старое
echo "Processing current backups..." >> "$DEBUG_LOG"
shopt -s nullglob
backups_folders=("$pbs"/current.*)
echo "Found ${#backups_folders[@]} current folders" >> "$DEBUG_LOG"

for folder in "${backups_folders[@]}"; do
    folder_name=$(basename "$folder")
    base=${folder_name#*.}
    echo "Processing base: $base" >> "$DEBUG_LOG"

    # Создаём целевую директорию на NAS
    mkdir -p "$nas/current.$base" 2>> "$DEBUG_LOG"

    # Проверяем наличие файлов бэкапов
    dump_file="$pbs/current.$base/$base-$(date +%Y-%m-%d).dump"
    zip_file="$pbs/current.$base/$base-$(date +%d.%m.%Y -d '-1 day').zip"

    echo "  Check dump: $dump_file" >> "$DEBUG_LOG"
    echo "  Check zip: $zip_file" >> "$DEBUG_LOG"

    if [[ -f "$dump_file" || -f "$zip_file" ]]; then
        echo "  Found backup files, copying to NAS..." >> "$DEBUG_LOG"
        cp -rn "$pbs/current.$base/"* "$nas/current.$base/" 2>> "$DEBUG_LOG"

        if [[ "$base" = "Trade" ]]; then
            echo "  Cleaning Trade (13 days)" >> "$DEBUG_LOG"
            find "$pbs/current.$base/" -mindepth 1 -maxdepth 1 -mtime +13 -exec rm -rv {} + >> "$DEBUG_LOG" 2>&1
        else
            echo "  Cleaning $base (3 days)" >> "$DEBUG_LOG"
            find "$pbs/current.$base/" -mindepth 1 -maxdepth 1 -mtime +3 -exec rm -rv {} + >> "$DEBUG_LOG" 2>&1
        fi
    else
        echo "  No backup files found for $base" >> "$DEBUG_LOG"
        if is_ignored_base "$base"; then
            echo "  Base $base is excluded from error logging" >> "$DEBUG_LOG"
        else
            echo "  Writing error to log" >> "$DEBUG_LOG"
            echo "$(date +%Y-%m-%d) problem base $base" >> "$nas/ERROR_$(date +%Y-%m-%d).log"
        fi
    fi
done

# Longtime backup: копируем longtime.* на NAS
echo "Processing longtime backups..." >> "$DEBUG_LOG"
backups_folders=("$pbs"/longtime.*)
echo "Found ${#backups_folders[@]} longtime folders" >> "$DEBUG_LOG"

for folder in "${backups_folders[@]}"; do
    folder_name=$(basename "$folder")
    base=${folder_name#*.}
    echo "Copying longtime.$base" >> "$DEBUG_LOG"
    mkdir -p "$nas/longtime.$base" 2>> "$DEBUG_LOG"
    cp -rn "$pbs/longtime.$base/." "$nas/longtime.$base/" 2>> "$DEBUG_LOG"
done

echo "$(date +%d-%m-%Y[%H:%M:%S]) END" >> "$nas/success_time.log" 2>> "$DEBUG_LOG"
echo "$(date +%d-%m-%Y[%H:%M:%S]) Script finished" >> "$DEBUG_LOG"

# === Итоговое письмо о передаче бэкапов на NAS (для nas_transfer_monitor) ===
RUN_END="$(date '+%Y-%m-%d %H:%M:%S')"

if nas_is_mounted; then
    NAS_MOUNTED="да"
else
    NAS_MOUNTED="нет"
fi

# Сколько баз обработано: каталоги current.* + longtime.*
shopt -s nullglob
processed_dirs=("$pbs"/current.* "$pbs"/longtime.*)
BASES_PROCESSED=${#processed_dirs[@]}

# Проблемные базы берём из лога ошибок текущего дня (его пишет ветка
# "problem base" выше) строками вида: "2026-05-29 problem base Trade".
ERROR_LOG="$nas/ERROR_$(date +%Y-%m-%d).log"
PROBLEM_BASES=""
ERROR_COUNT=0
if [ -f "$ERROR_LOG" ]; then
    # Уникальные проблемные базы за сегодня, с отсевом игнорируемых
    # (на случай записей от более ранних прогонов в этот же день).
    problem_arr=()
    while IFS= read -r _pb; do
        [ -n "$_pb" ] || continue
        is_ignored_base "$_pb" && continue
        problem_arr+=("$_pb")
    done < <(awk '/problem base/ {print $NF}' "$ERROR_LOG" | sort -u)

    ERROR_COUNT=${#problem_arr[@]}
    PROBLEM_BASES="$(printf '%s\n' "${problem_arr[@]}" | paste -sd ',' - | sed 's/,/, /g')"
fi

# Статус прогона
if [ "$NAS_MOUNTED" = "нет" ]; then
    STATUS="SKIPPED"
elif [ "$ERROR_COUNT" -gt 0 ]; then
    STATUS="ERROR"
else
    STATUS="OK"
fi

SUBJECT="NAS transfer ${HOST} ${STATUS}"

# Отправляем письмо. sendmail гарантирует UTF-8 тело и заголовки.
if command -v sendmail >/dev/null 2>&1; then
    sendmail -t <<EOF
From: ${MAIL_FROM}
To: ${MAIL_TO}
Subject: ${SUBJECT}
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit

Хост: ${HOST}
NAS примонтирован: ${NAS_MOUNTED}
Начало: ${RUN_START}
Завершено: ${RUN_END}
Баз обработано: ${BASES_PROCESSED}
Ошибок: ${ERROR_COUNT}
Проблемные базы: ${PROBLEM_BASES}
EOF
else
    # Фолбэк через mailutils/bsd-mailx, если sendmail недоступен.
    printf '%s\n' \
        "Хост: ${HOST}" \
        "NAS примонтирован: ${NAS_MOUNTED}" \
        "Начало: ${RUN_START}" \
        "Завершено: ${RUN_END}" \
        "Баз обработано: ${BASES_PROCESSED}" \
        "Ошибок: ${ERROR_COUNT}" \
        "Проблемные базы: ${PROBLEM_BASES}" \
        | mail -s "$SUBJECT" "$MAIL_TO"
fi

echo "$(date +%d-%m-%Y[%H:%M:%S]) Mail sent: ${SUBJECT} (bases=${BASES_PROCESSED} errors=${ERROR_COUNT})" >> "$DEBUG_LOG"
