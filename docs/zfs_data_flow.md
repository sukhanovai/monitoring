# ZFS data flow (Telegram + Android)

## Purpose
This note documents where ZFS monitoring data is received, stored, transformed, and read in two UX paths:

1. Telegram bot: `Главное меню -> ZFS`
2. Android app: `Оперативный центр -> tap on tile "ZFS"`

## 1) Data ingestion and storage (single source for both clients)

### Source: email subjects
- `MailMonitor.process_email` handles incoming email and calls `parse_zfs_status(subject)`.
- `parse_zfs_status` checks extension flag `zfs_monitor`, loads ZFS subject patterns from DB/config, parses matched server and pool states, and returns normalized entries.

### Persistence: backup DB table
- `save_zfs_status(...)` stores parsed entries into `zfs_pool_status`.
- Table and index are created in mail monitor bootstrap (`CREATE TABLE IF NOT EXISTS zfs_pool_status ...`, `idx_zfs_server_date`).
- Each row carries `(server_name, pool_name, state, details, subject, received_at)` and is deduplicated by unique constraint.

## 2) Telegram path: `Главное меню -> ZFS`

### Menu routing
- ZFS button appears in main menu only when extension `zfs_monitor` is enabled.
- Callback `zfs_menu` is routed by bot callback handler to `show_zfs_status_summary`.

### Data extraction for Telegram
- `show_zfs_status_summary` loads `ZFS_SERVERS` config and persisted enabled/disabled map (`zfs_monitoring_state`).
- It queries the latest record per `(server_name, pool_name)` from `zfs_pool_status`.
- It builds message lines with host-level monitoring activity and pool state details.
- Fallback branches are explicit for:
  - backup DB not configured,
  - table `zfs_pool_status` not yet created,
  - no data.

### Data mutations that affect Telegram + Android consistency
- Host add/toggle/rename/delete in Telegram settings (`settings_zfs_*`) update both:
  - config setting `ZFS_SERVERS`,
  - persisted state table `zfs_monitoring_state` (and for rename/delete also rows in `zfs_pool_status`).

## 3) Android path: `Оперативный центр -> tap "ZFS"`

### Transport/API
- Android does not query DB directly.
- `MainViewModel` calls BFF endpoint `runControlAction("zfs_menu")`.
- BFF/web layer maps action `zfs` to `zfs_menu` and executes the same server-side query logic over `zfs_pool_status` as in bot flow.

### Parsing in Android ViewModel
- Response text is parsed by regex (`zfsSummaryRegex`, `zfsStatusLineRegex`) into tile summary:
  - total pools,
  - problem pools,
  - host monitoring activity marker.
- On opening ZFS tile, ViewModel may additionally request `settings_zfs_list` to refresh host activity markers against Telegram-side toggles.

## 4) Why discrepancies can happen

Most common mismatch points:
1. **Ingestion mismatch:** subject does not match current ZFS pattern set.
2. **Config mismatch:** server exists in emails but absent/disabled in `ZFS_SERVERS`.
3. **State mismatch:** `zfs_monitoring_state` not synchronized after host operations.
4. **Parsing mismatch in Android:** message format changed server-side but regex in app not updated.
5. **Staleness/race:** Android tile uses cached state until explicit refresh action finishes.

## 5) Quick verification checklist
1. Confirm `zfs_monitor` extension enabled.
2. Inspect latest email subject against active ZFS patterns.
3. Check rows in `zfs_pool_status` for expected server/pool/time.
4. Check `zfs_monitoring_state` for host enabled flags.
5. Compare Telegram `zfs_menu` raw output vs Android `runControlAction("zfs_menu")` payload.
6. If message format differs, update Android regex parser in `MainViewModel`.
