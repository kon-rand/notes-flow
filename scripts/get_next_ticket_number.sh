#!/bin/bash
# Скрипт для получения следующего номера тикета

PLAN_FILE="PLAN.md"

# Если файл не указан, используем PLAN.md
if [ -n "$1" ]; then
    PLAN_FILE="$1"
fi

# Проверяем существование файла
if [ ! -f "$PLAN_FILE" ]; then
    echo "Ошибка: Файл $PLAN_FILE не найден"
    exit 1
fi

# Находим все номера тикетов в таблице (строки вида "| 1 | TICKET-001.md")
# Или в таблице этапов (строки вида "| 1 | Базовая структура |")
LAST_TICKET=$(grep -E "^\|\s*[0-9]+\s+\|" "$PLAN_FILE" | \
    grep "TICKET-" | \
    sed 's/.*TICKET-\([0-9]*\).*/\1/' | \
    sort -n | \
    tail -1)

if [ -z "$LAST_TICKET" ]; then
    echo "001"
else
    # Форматируем следующий номер с ведущими нулями (3 цифры)
    printf "%03d" $((10#$LAST_TICKET + 1))
fi