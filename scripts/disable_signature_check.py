"""
Временный скрипт для отключения проверки подписи в webhook_server.py
Используется только для тестирования!
"""
import sys
import os
import re

def disable_signature_check(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Ищем функцию verify_signature и меняем её реализацию
    pattern = r"async def verify_signature\(self, payload: bytes, signature: str\) -> bool:.*?return hmac\.compare_digest\(f\"sha256={expected_signature}\", signature\)"
    replacement = """async def verify_signature(self, payload: bytes, signature: str) -> bool:
        # ВНИМАНИЕ: Проверка подписи отключена для тестирования!
        # НЕ ИСПОЛЬЗУЙТЕ В PRODUCTION!
        print("Подпись проверки отключена для тестирования!")
        return True"""
    
    # Используем re.DOTALL для поиска многострочной функции
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print("ОШИБКА: Функция verify_signature не найдена или имеет другой формат!")
        return False
    
    # Создаем резервную копию
    backup_path = file_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Резервная копия сохранена: {backup_path}")
    
    # Записываем измененный файл
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    print(f"Проверка подписи отключена в файле: {file_path}")
    
    return True

def restore_from_backup(file_path):
    backup_path = file_path + '.bak'
    
    if not os.path.exists(backup_path):
        print(f"ОШИБКА: Резервная копия не найдена: {backup_path}")
        return False
    
    with open(backup_path, 'r', encoding='utf-8') as backup_file:
        content = backup_file.read()
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Восстановлен оригинал файла из резервной копии: {file_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python disable_signature_check.py [disable|restore] [путь_к_файлу]")
        print("По умолчанию: services/webhook_server.py")
        sys.exit(1)
    
    command = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else "services/webhook_server.py"
    
    if command == "disable":
        if disable_signature_check(file_path):
            print("ВНИМАНИЕ: Проверка подписи отключена! Используйте только для тестирования!")
            print("Для восстановления запустите: python disable_signature_check.py restore")
    elif command == "restore":
        if restore_from_backup(file_path):
            print("Проверка подписи восстановлена.")
    else:
        print(f"Неизвестная команда: {command}")
        print("Доступные команды: disable, restore")
