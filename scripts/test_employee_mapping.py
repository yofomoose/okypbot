"""
Скрипт для тестирования системы сопоставления сотрудников OkDesk и пользователей Telegram
"""
from services.employee_mapping import EmployeeMappingService
import argparse
import sys

def print_mapping(mapping_service):
    """Печать всех сопоставлений"""
    print("\nТекущие сопоставления:")
    print("-" * 40)
    
    mappings = mapping_service.get_all_mappings()
    if not mappings:
        print("Сопоставления отсутствуют")
    else:
        print(f"{'OkDesk ID':<10} | {'Telegram ID':<15}")
        print("-" * 40)
        for okdesk_id, telegram_id in mappings:
            print(f"{okdesk_id:<10} | {telegram_id:<15}")
    
    print("-" * 40)
    default_id = mapping_service.get_default_employee_id()
    print(f"ID сотрудника по умолчанию: {default_id or 'Не установлен'}")
    print("-" * 40)

def add_mapping(mapping_service, okdesk_id, telegram_id):
    """Добавить сопоставление"""
    if mapping_service.add_mapping(okdesk_id, telegram_id):
        print(f"✅ Сопоставление успешно добавлено: OkDesk ID {okdesk_id} -> Telegram ID {telegram_id}")
    else:
        print(f"❌ Ошибка при добавлении сопоставления")

def remove_mapping(mapping_service, okdesk_id):
    """Удалить сопоставление"""
    if mapping_service.remove_mapping(okdesk_employee_id=okdesk_id):
        print(f"✅ Сопоставление для OkDesk ID {okdesk_id} успешно удалено")
    else:
        print(f"❌ Ошибка при удалении сопоставления для OkDesk ID {okdesk_id}")

def set_default(mapping_service, okdesk_id):
    """Установить ID сотрудника по умолчанию"""
    if mapping_service.set_default_employee_id(okdesk_id):
        print(f"✅ ID сотрудника по умолчанию установлен: {okdesk_id}")
    else:
        print(f"❌ Ошибка при установке ID сотрудника по умолчанию")

def test_lookup(mapping_service, okdesk_id=None, telegram_id=None):
    """Тестирование поиска сопоставлений"""
    print("\nТестирование поиска сопоставлений:")
    print("-" * 40)
    
    if okdesk_id:
        telegram_id_result = mapping_service.get_telegram_id(okdesk_id)
        print(f"OkDesk ID {okdesk_id} -> Telegram ID: {telegram_id_result or 'Не найден'}")
    
    if telegram_id:
        okdesk_id_result = mapping_service.get_okdesk_employee_id(int(telegram_id))
        print(f"Telegram ID {telegram_id} -> OkDesk ID: {okdesk_id_result or 'Не найден'}")
    
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Управление сопоставлениями сотрудников OkDesk и пользователей Telegram")
    parser.add_argument("--file", help="Путь к файлу сопоставлений", default=None)
    
    subparsers = parser.add_subparsers(dest="command", help="Команда")
    
    # Команда list
    subparsers.add_parser("list", help="Показать все сопоставления")
    
    # Команда add
    add_parser = subparsers.add_parser("add", help="Добавить сопоставление")
    add_parser.add_argument("okdesk_id", help="ID сотрудника OkDesk")
    add_parser.add_argument("telegram_id", help="ID пользователя Telegram", type=int)
    
    # Команда remove
    remove_parser = subparsers.add_parser("remove", help="Удалить сопоставление")
    remove_parser.add_argument("okdesk_id", help="ID сотрудника OkDesk для удаления")
    
    # Команда default
    default_parser = subparsers.add_parser("default", help="Установить ID сотрудника по умолчанию")
    default_parser.add_argument("okdesk_id", help="ID сотрудника OkDesk по умолчанию")
    
    # Команда lookup
    lookup_parser = subparsers.add_parser("lookup", help="Найти сопоставление")
    lookup_parser.add_argument("--okdesk", help="ID сотрудника OkDesk для поиска")
    lookup_parser.add_argument("--telegram", help="ID пользователя Telegram для поиска", type=int)
    
    args = parser.parse_args()
    
    # Создаем экземпляр сервиса
    mapping_service = EmployeeMappingService(args.file)
    
    # Выполняем команду
    if args.command == "list" or not args.command:
        print_mapping(mapping_service)
    elif args.command == "add":
        add_mapping(mapping_service, args.okdesk_id, args.telegram_id)
        print_mapping(mapping_service)
    elif args.command == "remove":
        remove_mapping(mapping_service, args.okdesk_id)
        print_mapping(mapping_service)
    elif args.command == "default":
        set_default(mapping_service, args.okdesk_id)
        print_mapping(mapping_service)
    elif args.command == "lookup":
        test_lookup(mapping_service, args.okdesk, args.telegram)
    else:
        print(f"Неизвестная команда: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
