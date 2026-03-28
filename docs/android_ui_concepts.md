# Варианты интерфейса Android-приложения

Ниже собраны дополнительные UI-концепты с упором на:
- **компактность**;
- **информативность**;
- **доступное и быстрое управление + вызов отчётов**;
- **удобные настройки**.

## Вариант A — Compact Ops Hub
**Идея:** максимум полезной информации на одном экране, минимум скролла, быстрые действия для on-call.

### A1) Dashboard
![Вариант A — Dashboard](assets/android-ui-concepts/variant-compact-ops-dashboard.svg)

### A2) Reports
![Вариант A — Reports](assets/android-ui-concepts/variant-compact-ops-reports.svg)

### A3) Settings
![Вариант A — Settings](assets/android-ui-concepts/variant-compact-ops-settings.svg)

---

## Вариант B — Info-First Matrix
**Идея:** высокая информативность, контекст инцидентов, метрики и тренды без потери читаемости.

### B1) Dashboard
![Вариант B — Dashboard](assets/android-ui-concepts/variant-info-matrix-dashboard.svg)

### B2) Reports
![Вариант B — Reports](assets/android-ui-concepts/variant-info-matrix-reports.svg)

### B3) Settings
![Вариант B — Settings](assets/android-ui-concepts/variant-info-matrix-settings.svg)

---

## Вариант C — Accessible Command Center
**Идея:** крупные контролы, высокая доступность, простая навигация и отчёты в 1–3 действия.

### C1) Dashboard
![Вариант C — Dashboard](assets/android-ui-concepts/variant-accessible-command-dashboard.svg)

### C2) Reports
![Вариант C — Reports](assets/android-ui-concepts/variant-accessible-command-reports.svg)

### C3) Settings
![Вариант C — Settings](assets/android-ui-concepts/variant-accessible-command-settings.svg)

---

## Рекомендация по следующему шагу
1. Взять **A** как базу для MVP (компактность + скорость реакций).
2. Добавить из **B** блоки аналитики и drill-down отчётов.
3. Применить из **C** паттерны доступности (размеры контролов, контраст, TalkBack-labels).
