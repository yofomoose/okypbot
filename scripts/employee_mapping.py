#!/usr/bin/env python
"""
Скрипт для работы с сопоставлениями сотрудников OkDesk и пользователей Telegram.
Позволяет просматривать, добавлять, удалять и устанавливать сопоставления по умолчанию.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Добавляем путь к проекту в sys.path для корректного импорта модулей
project_root = Path(__file__).parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.employee_mapping import EmployeeMappingService

def list_mappings():
    """Показать все сопоставления"""
    mapping_service = EmployeeMappingService()
    mappings = mapping_service.get_all_mappings()
    default_id = mapping_service.get_default_employee_id()
    
    print("\n📋 Текущие сопоставления:")
    print("-" * 40)
    
    if not mappings:
        print("Сопоставления отсутствуют")
    else:
        for okdesk_id, telegram_id in mappings:
            print(f"OkDesk ID: {okdesk_id} → Telegram ID: {telegram_id}")
    
    print("-" * 40)
    print(f"ID сотрудника по умолчанию: {default_id or 'Не установлен'}")
    print()

def add_mapping(okdesk_id, telegram_id):
    """Добавить новое сопоставление"""
    mapping_service = EmployeeMappingService()
    
    try:
        # Проверяем, что ID сотрудника OkDesk является числом
        okdesk_id = str(int(okdesk_id))
        # Проверяем, что ID пользователя Telegram является числом
        telegram_id = int(telegram_id)
        
        if mapping_service.add_mapping(okdesk_id, telegram_id):
            print(f"✅ Сопоставление успешно добавлено: OkDesk ID {okdesk_id} → Telegram ID {telegram_id}")
            return True
        else:
            print("❌ Ошибка при добавлении сопоставления")
            return False
    except ValueError:
        print("❌ ID должны быть числами")
        return False

def remove_mapping(okdesk_id):
    """Удалить сопоставление"""
    mapping_service = EmployeeMappingService()
    
    try:
        # Проверяем, что ID сотрудника OkDesk является числом
        okdesk_id = str(int(okdesk_id))
        
        if mapping_service.remove_mapping(okdesk_employee_id=okdesk_id):
            print(f"✅ Сопоставление для OkDesk ID {okdesk_id} успешно удалено")
            return True
        else:
            print(f"❌ Сопоставление для OkDesk ID {okdesk_id} не найдено")
            return False
    except ValueError:
        print("❌ ID должен быть числом")
        return False

def set_default(okdesk_id):
    """Установить ID сотрудника по умолчанию"""
    mapping_service = EmployeeMappingService()
    
    try:
        # Проверяем, что ID сотрудника OkDesk является числом
        okdesk_id = str(int(okdesk_id))
        
        if mapping_service.set_default_employee_id(okdesk_id):
            print(f"✅ ID сотрудника по умолчанию установлен: {okdesk_id}")
            return True
        else:
            print("❌ Ошибка при установке ID сотрудника по умолчанию")
            return False
    except ValueError:
        print("❌ ID должен быть числом")
        return False

def interactive_menu():
    """Интерактивное меню для работы с сопоставлениями"""
    while True:
        print("\n🔧 Управление сопоставлениями OkDesk → Telegram")
        print("1. Показать все сопоставления")
        print("2. Добавить новое сопоставление")
        print("3. Удалить сопоставление")
        print("4. Установить ID сотрудника по умолчанию")
        print("0. Выход")
        
        choice = input("\nВыберите действие (0-4): ")
        
        if choice == "0":
            print("Выход из программы...")
            break
        
        elif choice == "1":
            list_mappings()
        
        elif choice == "2":
            okdesk_id = input("Введите ID сотрудника OkDesk: ")
            telegram_id = input("Введите ID пользователя Telegram: ")
            add_mapping(okdesk_id, telegram_id)
        
        elif choice == "3":
            okdesk_id = input("Введите ID сотрудника OkDesk для удаления: ")
            remove_mapping(okdesk_id)
        
        elif choice == "4":
            okdesk_id = input("Введите ID сотрудника OkDesk по умолчанию: ")
            set_default(okdesk_id)
        
        else:
            print("❌ Неверный выбор. Пожалуйста, выберите действие от 0 до 4.")
        
        input("\nНажмите Enter для продолжения...")

def main():
    parser = argparse.ArgumentParser(description="Управление сопоставлениями сотрудников OkDesk и пользователей Telegram")
    
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
    
    # Команда для просмотра всех сопоставлений
    list_parser = subparsers.add_parser("list", help="Показать все сопоставления")
    
    # Команда для добавления сопоставления
    add_parser = subparsers.add_parser("add", help="Добавить новое сопоставление")
    add_parser.add_argument("okdesk_id", help="ID сотрудника OkDesk")
    add_parser.add_argument("telegram_id", help="ID пользователя Telegram")
    
    # Команда для удаления сопоставления
    remove_parser = subparsers.add_parser("remove", help="Удалить сопоставление")
    remove_parser.add_argument("okdesk_id", help="ID сотрудника OkDesk")
    
    # Команда для установки ID сотрудника по умолчанию
    default_parser = subparsers.add_parser("default", help="Установить ID сотрудника по умолчанию")
    default_parser.add_argument("okdesk_id", help="ID сотрудника OkDesk")
    
    # Режим интерактивного меню
    menu_parser = subparsers.add_parser("menu", help="Запустить интерактивное меню")
    
    args = parser.parse_args()
    
    # Если команда не указана, запускаем интерактивное меню
    if args.command is None or args.command == "menu":
        interactive_menu()
    
    # Обработка команд
    elif args.command == "list":
        list_mappings()
    
    elif args.command == "add":
        add_mapping(args.okdesk_id, args.telegram_id)
    
    elif args.command == "remove":
        remove_mapping(args.okdesk_id)
    
    elif args.command == "default":
        set_default(args.okdesk_id)

if __name__ == "__main__":
    main()
