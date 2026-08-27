# Мониторинг передачи бэкапов на NAS (`nas_transfer_monitor`)

Расширение отслеживает результаты скрипта `move_and_clear_backups.sh` на сервере
бэкапов (`sr-bup`), который копирует бэкапы 1С с сервера бэкапов на NAS. Скрипт
отправляет **одно итоговое письмо на каждый прогон** на ящик `katok@202020.ru`;
письмо фильтром пересылается на почтовый сервер проекта (в Maildir), парсится
`NasTransferParserMixin` и сохраняется в таблицу `nas_transfers` (одна запись на
прогон). Результат виден в Telegram-боте, Matrix-боте и Android-приложении.

## Формат письма (его обязан соблюдать скрипт)

Тема (ASCII, не MIME-кодируется):

```
NAS transfer <host> <STATUS>
```

- `<host>` — короткое имя сервера (`sr-bup`);
- `<STATUS>` — `OK` | `ERROR` | `SKIPPED` (`SKIPPED` = NAS не примонтирован,
  ничего не копировали). Регистр темы не важен; `STARTED`/`BUSY` тоже
  распознаются, но скрипт их не использует.

Тело (UTF-8, по одному полю на строку, формат `Ключ: значение`):

```
Хост: sr-bup
NAS примонтирован: да
Начало: 2026-05-28 02:00:11
Завершено: 2026-05-28 02:47:33
Баз обработано: 14
Ошибок: 2
Проблемные базы: Trade, Hold
```

- `NAS примонтирован:` — `да` / `нет`;
- `Начало:` / `Завершено:` — произвольный текст (показывается как есть);
- `Баз обработано:` / `Ошибок:` — целые числа;
- `Проблемные базы:` — список через запятую; строку можно опустить, если ошибок нет.

Статус берётся из темы, флаг монтирования — из тела. Проблема в интерфейсах
подсвечивается, если `STATUS = ERROR` или `Ошибок > 0`.

## Доработка `move_and_clear_backups.sh` на `sr-bup`

Существующую логику копирования/очистки и записи в логи **трогать не нужно** —
блок ниже только читает уже существующий лог ошибок (`$nas/ERROR_<дата>.log`,
который скрипт пишет в ветке «problem base») и считает каталоги баз.

1. В начало скрипта, сразу после блока определения переменных
   (`pbs="/zfs/nfs/backup.1c"`, `nas="/NAS/backup.1c"`), добавьте фиксацию
   времени старта:

   ```bash
   RUN_START="$(date '+%Y-%m-%d %H:%M:%S')"
   MAIL_TO="katok@202020.ru"
   HOST="$(hostname -s)"
   ```

2. В самый конец скрипта (после строки `... Script finished`) добавьте блок
   отправки итогового письма:

   ```bash
   # === Итоговое письмо о передаче бэкапов на NAS ===
   RUN_END="$(date '+%Y-%m-%d %H:%M:%S')"

   if mountpoint -q "$nas"; then
       NAS_MOUNTED="да"
   else
       NAS_MOUNTED="нет"
   fi

   # Каталоги баз, обработанных скриптом (current.* и longtime.*).
   shopt -s nullglob
   processed_dirs=("$pbs"/current.* "$pbs"/longtime.*)
   BASES_PROCESSED=${#processed_dirs[@]}

   # Проблемные базы берём из лога ошибок текущего дня, который скрипт уже
   # пишет строками вида "2026-05-28 problem base Trade".
   ERROR_LOG="$nas/ERROR_$(date +%Y-%m-%d).log"
   if [ -f "$ERROR_LOG" ]; then
       PROBLEM_BASES="$(awk '/problem base/ {print $NF}' "$ERROR_LOG" \
           | sort -u | paste -sd ', ' -)"
       ERROR_COUNT="$(awk '/problem base/ {print $NF}' "$ERROR_LOG" \
           | sort -u | grep -c .)"
   else
       PROBLEM_BASES=""
       ERROR_COUNT=0
   fi

   if [ "$NAS_MOUNTED" = "нет" ]; then
       STATUS="SKIPPED"
   elif [ "$ERROR_COUNT" -gt 0 ]; then
       STATUS="ERROR"
   else
       STATUS="OK"
   fi

   SUBJECT="NAS transfer ${HOST} ${STATUS}"
   BODY="Хост: ${HOST}
   NAS примонтирован: ${NAS_MOUNTED}
   Начало: ${RUN_START}
   Завершено: ${RUN_END}
   Баз обработано: ${BASES_PROCESSED}
   Ошибок: ${ERROR_COUNT}
   Проблемные базы: ${PROBLEM_BASES}"

   printf '%s\n' "$BODY" | mail -s "$SUBJECT" "$MAIL_TO"
   # Если утилита `mail` недоступна, используйте sendmail:
   # printf 'To: %s\nSubject: %s\n\n%s\n' "$MAIL_TO" "$SUBJECT" "$BODY" | sendmail -t
   ```

> Примечание: тело письма выше выровнено отступами для читабельности — при
> вставке в скрипт убедитесь, что строки `BODY` начинаются без ведущих пробелов
> (heredoc/переменная), иначе ключи `Хост:`, `Ошибок:` и т.д. не должны иметь
> отступа. Парсер ищет ключи в начале строки (`re.MULTILINE`).

## Настройка расширения

- Включение/выключение — в списке расширений Telegram-бота, Matrix-бота
  (`!extensions`) и Android-приложения (тумблер в разделе «Расширения»).
- `NAS_TRANSFER_ALERT_HOURS` (по умолчанию 48) — окно, за которое показываются
  прогоны. Редактируется через Matrix `!settings`; читается ботом, веб-control
  action `backup_nas_transfer` и Android-плиткой.

## Где смотреть результат

- **Telegram:** меню бэкапов → «📤 Передача на NAS».
- **Matrix:** команда `!nas` (или кнопка в `!extensions`).
- **Android:** плитка «NAS» в обзоре; тап открывает сводку прогонов.
