"""
Скрипт для добавления фиксированного ID автора в конфигурацию Docker
"""
import os
import sys
import subprocess
import argparse

def update_docker_compose(author_id):
    """Добавляет OKDESK_AUTHOR_ID в docker-compose.prod.yml"""
    docker_compose_file = "docker/docker-compose.prod.yml"
    
    if not os.path.exists(docker_compose_file):
        print(f"❌ Файл {docker_compose_file} не найден!")
        return False
    
    with open(docker_compose_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Проверяем, есть ли уже OKDESK_AUTHOR_ID в файле
    if "OKDESK_AUTHOR_ID:" in content:
        print(f"⚠️ OKDESK_AUTHOR_ID уже существует в {docker_compose_file}")
        
        # Заменяем существующее значение
        import re
        pattern = r"(OKDESK_AUTHOR_ID:).*"
        replacement = f"OKDESK_AUTHOR_ID: {author_id}"
        content = re.sub(pattern, replacement, content)
        
        with open(docker_compose_file, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"✅ OKDESK_AUTHOR_ID обновлен в {docker_compose_file}")
        return True
    
    # Ищем секцию с переменными окружения для бота
    env_section = content.find("environment:")
    if env_section == -1:
        print(f"❌ Не найдена секция environment в {docker_compose_file}!")
        return False
    
    # Находим конец секции environment
    env_end = content.find("command:", env_section)
    if env_end == -1:
        print(f"❌ Не удалось определить конец секции environment в {docker_compose_file}!")
        return False
    
    # Получаем секцию с переменными окружения
    env_section_content = content[env_section:env_end]
    
    # Добавляем OKDESK_AUTHOR_ID в правильное место
    last_env_var = env_section_content.rstrip().split("\n")[-1]
    indent = " " * (len(last_env_var) - len(last_env_var.lstrip()))
    
    new_env_var = f"{indent}OKDESK_AUTHOR_ID: {author_id}\n"
    new_content = content[:env_end] + new_env_var + content[env_end:]
    
    # Записываем обновленный контент
    with open(docker_compose_file, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f"✅ OKDESK_AUTHOR_ID добавлен в {docker_compose_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Добавить OKDESK_AUTHOR_ID в docker-compose.prod.yml')
    parser.add_argument('author_id', type=int, help='ID автора для комментариев в OkDesk')
    
    args = parser.parse_args()
    author_id = args.author_id
    
    print(f"Добавляем OKDESK_AUTHOR_ID={author_id} в docker-compose.prod.yml...")
    
    if update_docker_compose(author_id):
        print(f"""
✅ OKDESK_AUTHOR_ID успешно добавлен в конфигурацию Docker!

Для применения изменений выполните:
docker-compose -f docker/docker-compose.prod.yml up -d --force-recreate bot

Затем проверьте логи:
docker logs okypbot_app
""")
    else:
        print("❌ Не удалось обновить конфигурацию!")
        sys.exit(1)

if __name__ == "__main__":
    main()
