"""
Server Monitoring System v4.11.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot utilities package
Система мониторинга серверов
Версия: 4.11.3
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет утилит бота
"""

from .utils import check_access, get_access_denied_response

__all__ = [
    'check_access',
    'get_access_denied_response'
]