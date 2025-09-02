#!/bin/bash
# Скрипт для настройки сопоставления сотрудников OkDesk и пользователей Telegram

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Сброс цвета

echo -e "${BLUE}=== Настройка сопоставления сотрудников OkDesk и пользователей Telegram ===${NC}"

# Функция для проверки, является ли строка числом
is_number() {
    [[ $1 =~ ^[0-9]+$ ]]
}

# Создаем директорию database, если она не существует
if [ ! -d "database" ]; then
    echo -e "${YELLOW}Создаем директорию database${NC}"
    mkdir -p database
fi

# Проверяем существование файла сопоставлений
MAPPING_FILE="database/employee_mapping.json"
if [ ! -f "$MAPPING_FILE" ]; then
    echo -e "${YELLOW}Создаем новый файл сопоставлений${NC}"
    echo '{
  "mapping": {},
  "reverse_mapping": {},
  "default_employee_id": null
}' > "$MAPPING_FILE"
fi

# Основной цикл работы с меню
while true; do
    echo ""
    echo -e "${BLUE}Меню настройки сопоставлений:${NC}"
    echo -e "1. Показать все сопоставления"
    echo -e "2. Добавить новое сопоставление"
    echo -e "3. Удалить сопоставление"
    echo -e "4. Установить ID сотрудника по умолчанию"
    echo -e "5. Выход"
    
    read -p "Выберите действие (1-5): " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}Текущие сопоставления:${NC}"
            python -c "
import json
try:
    with open('$MAPPING_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        print('Сопоставления OkDesk ID -> Telegram ID:')
        for okdesk_id, tg_id in data.get('mapping', {}).items():
            print(f'OkDesk ID: {okdesk_id} -> Telegram ID: {tg_id}')
            
        default_id = data.get('default_employee_id')
        print(f'\nID сотрудника по умолчанию: {default_id if default_id else \"Не установлен\"}')
except Exception as e:
    print(f'Ошибка: {e}')
"
            ;;
        2)
            echo -e "${YELLOW}Добавление нового сопоставления${NC}"
            read -p "Введите ID сотрудника OkDesk: " okdesk_id
            read -p "Введите ID пользователя Telegram: " telegram_id
            
            # Проверяем, что введены числа
            if ! is_number "$okdesk_id" || ! is_number "$telegram_id"; then
                echo -e "${RED}Ошибка: ID должны быть числами!${NC}"
                continue
            fi
            
            python -c "
import json
try:
    with open('$MAPPING_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Добавляем новое сопоставление
    okdesk_id = '$okdesk_id'
    telegram_id = $telegram_id
    
    if 'mapping' not in data:
        data['mapping'] = {}
    if 'reverse_mapping' not in data:
        data['reverse_mapping'] = {}
    
    data['mapping'][okdesk_id] = telegram_id
    data['reverse_mapping'][str(telegram_id)] = okdesk_id
    
    with open('$MAPPING_FILE', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print('Сопоставление успешно добавлено!')
except Exception as e:
    print(f'Ошибка: {e}')
"
            ;;
        3)
            echo -e "${YELLOW}Удаление сопоставления${NC}"
            read -p "Введите ID сотрудника OkDesk для удаления (или оставьте пустым): " okdesk_id
            
            if [ -n "$okdesk_id" ]; then
                python -c "
import json
try:
    with open('$MAPPING_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    okdesk_id = '$okdesk_id'
    removed = False
    
    if 'mapping' in data and okdesk_id in data['mapping']:
        telegram_id = data['mapping'][okdesk_id]
        del data['mapping'][okdesk_id]
        
        # Удаляем обратное сопоставление
        if 'reverse_mapping' in data and str(telegram_id) in data['reverse_mapping']:
            del data['reverse_mapping'][str(telegram_id)]
        
        removed = True
    
    with open('$MAPPING_FILE', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    if removed:
        print(f'Сопоставление для OkDesk ID {okdesk_id} успешно удалено!')
    else:
        print(f'Сопоставление для OkDesk ID {okdesk_id} не найдено!')
except Exception as e:
    print(f'Ошибка: {e}')
"
            else
                echo -e "${RED}ID сотрудника не указан!${NC}"
            fi
            ;;
        4)
            echo -e "${YELLOW}Установка ID сотрудника по умолчанию${NC}"
            read -p "Введите ID сотрудника OkDesk по умолчанию: " default_id
            
            if [ -n "$default_id" ] && is_number "$default_id"; then
                python -c "
import json
try:
    with open('$MAPPING_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['default_employee_id'] = '$default_id'
    
    with open('$MAPPING_FILE', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f'ID сотрудника по умолчанию установлен: {default_id}')
except Exception as e:
    print(f'Ошибка: {e}')
"
            else
                echo -e "${RED}ID сотрудника должен быть числом!${NC}"
            fi
            ;;
        5)
            echo -e "${GREEN}Выход из программы настройки.${NC}"
            echo -e "${BLUE}Для применения изменений перезапустите контейнер бота:${NC}"
            echo -e "${YELLOW}docker-compose -f docker/docker-compose.prod.yml restart bot${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Неверный выбор! Пожалуйста, выберите число от 1 до 5.${NC}"
            ;;
    esac
done
