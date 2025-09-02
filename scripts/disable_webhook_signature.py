#!/usr/bin/env python3
"""
Скрипт для временного отключения проверки подписи webhook
"""
import os
import sys
import re

def disable_signature_check(file_path):
    # Проверяем существование файла
    if not os.path.exists(file_path):
        print(f"Ошибка: файл {file_path} не найден")
        return False
    
    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем метод verify_signature
    signature_pattern = r'(async\s+def\s+verify_signature.*?return\s+hmac\.compare_digest.*?)\)'
    
    if re.search(signature_pattern, content, re.DOTALL):
        # Заменяем метод
        new_content = re.sub(
            signature_pattern,
            r'\1)\n        # ВРЕМЕННО ОТКЛЮЧЕНА ПРОВЕРКА ПОДПИСИ\n        return True',
            content,
            flags=re.DOTALL
        )
        
        # Создаем резервную копию
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Создана резервная копия: {backup_path}")
        
        # Записываем изменения
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ Проверка подписи webhook отключена в файле {file_path}")
        print("⚠️ ВНИМАНИЕ: Это временное изменение только для тестирования!")
        print("⚠️ Не забудьте восстановить проверку подписи после тестирования:")
        print(f"   cp {backup_path} {file_path}")
        
        return True
    else:
        print("Ошибка: не удалось найти метод verify_signature")
        return False

def print_usage():
    print("Использование: python disable_webhook_signature.py <путь к файлу webhook_server.py>")
    print("Пример: python disable_webhook_signature.py /app/services/webhook_server.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not disable_signature_check(file_path):
        sys.exit(1)
