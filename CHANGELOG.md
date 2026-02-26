# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [8.6.0] - 2026-02-26

### Added
- Android/BFF: expanded Windows server types management in mobile settings (create, rename, merge, delete).
- BFF API: dedicated endpoints for Windows credentials and Windows server type operations.
- Project maintenance: `CHANGELOG.md` introduced.

### Changed
- Android settings section label changed from `Auth` to `Аутентификация`.
- Android auth screen behavior simplified: removed extra nested `Аутентификация` button.
- Android settings sync now loads Windows credentials from dedicated endpoint (`/v1/settings/auth/windows-credentials`) to keep list of all accounts consistent.
- Added standard project header template to Python files where it was missing:
  - `lib/tamtam_bot.py`
  - `scripts/generate_mobile_default_token.py`

### Fixed
- Android `Просмотр всех учетных записей` no longer depends only on aggregate auth response; it now fetches current Windows credentials directly.

