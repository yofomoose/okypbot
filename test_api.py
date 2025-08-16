"""
Скрипт для тестирования Okdesk API и изучения структуры данных
"""
import asyncio
import json
import aiohttp
from api.okdesk_api import OkdeskAPI
from config import OKDESK_API_TOKEN, OKDESK_BASE_URL

async def test_api_endpoints():
    """Тестируем доступные API эндпоинты"""
    base_url = OKDESK_BASE_URL.rstrip('/')
    
    # Список эндпоинтов для проверки
    endpoints = [
        '/api/v1/issues',
        '/api/v1/contacts', 
        '/api/v1/companies',
        '/api/v1/issue_types',
        '/api/v1/issue_priorities',
        '/api/v1/issue_statuses',
        '/api/v1/employees'
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Проверяем доступные API эндпоинты...")
        print("=" * 60)
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            params = {'api_token': OKDESK_API_TOKEN, 'limit': 1}
            
            try:
                async with session.get(url, params=params) as response:
                    print(f"📡 {endpoint}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            print(f"   📊 Структура ответа: {list(data.keys())}")
                            if 'data' in data:
                                print(f"   📦 Записей в data: {len(data['data'])}")
                        else:
                            print(f"   📦 Тип ответа: {type(data)}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Ошибка: {error_text[:100]}...")
            except Exception as e:
                print(f"   ❌ Исключение: {str(e)}")
        
        print("\n" + "=" * 60)

async def test_api():
    """Тестируем различные API методы"""
    await test_api_endpoints()
    
    okdesk = OkdeskAPI()
    
    try:
        print("\n🔍 Тестирование методов OkdeskAPI...")
        print("=" * 50)
        
        # 1. Получаем список заявок (базовый тест)
        print("\n� 1. Получение списка заявок:")
        try:
            issues = await okdesk.get_issues(limit=3)
            print(f"Найдено заявок: {len(issues)}")
            if issues:
                print("Пример заявки:")
                issue_example = {
                    'id': issues[0].get('id'),
                    'title': issues[0].get('title'),
                    'status': issues[0].get('status'),
                    'contact': issues[0].get('contact'),
                    'company': issues[0].get('company'),
                    'created_at': issues[0].get('created_at')
                }
                print(json.dumps(issue_example, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Ошибка получения заявок: {e}")
        
        # 2. Получаем типы заявок
        print("\n📋 2. Получение типов заявок:")
        try:
            issue_types = await okdesk.get_issue_types()
            print(f"Найдено типов: {len(issue_types) if isinstance(issue_types, list) else 'неизвестно'}")
            if issue_types:
                print("Доступные типы заявок:")
                for i, issue_type in enumerate(issue_types[:3]):
                    print(f"  {i+1}. {issue_type}")
        except Exception as e:
            print(f"Ошибка получения типов заявок: {e}")
        
        # 3. Получаем приоритеты заявок
        print("\n⚡ 3. Получение приоритетов заявок:")
        try:
            priorities = await okdesk.get_issue_priorities()
            print(f"Найдено приоритетов: {len(priorities) if isinstance(priorities, list) else 'неизвестно'}")
            if priorities:
                print("Доступные приоритеты:")
                for i, priority in enumerate(priorities[:3]):
                    print(f"  {i+1}. {priority}")
        except Exception as e:
            print(f"Ошибка получения приоритетов: {e}")
        
        # 4. Получаем статусы заявок
        print("\n� 4. Получение статусов заявок:")
        try:
            statuses = await okdesk.get_issue_statuses()
            print(f"Найдено статусов: {len(statuses) if isinstance(statuses, list) else 'неизвестно'}")
            if statuses:
                print("Доступные статусы:")
                for i, status in enumerate(statuses[:3]):
                    print(f"  {i+1}. {status}")
        except Exception as e:
            print(f"Ошибка получения статусов: {e}")
        
        # 5. Получаем список сотрудников
        print("\n👥 5. Получение списка сотрудников:")
        try:
            employees = await okdesk.get_employees()
            print(f"Найдено сотрудников: {len(employees)}")
            if employees:
                print("Пример сотрудника:")
                employee_example = {
                    'id': employees[0].get('id'),
                    'name': employees[0].get('name'),
                    'email': employees[0].get('email'),
                    'position': employees[0].get('position')
                }
                print(json.dumps(employee_example, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Ошибка получения сотрудников: {e}")
        
        # 6. Получаем список контактов
        print("\n� 6. Получение списка контактов:")
        try:
            contacts = await okdesk.get_contacts(limit=5)
            print(f"Найдено контактов: {len(contacts)}")
            if contacts:
                print("Пример контакта:")
                print(json.dumps(contacts[0], indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Ошибка получения контактов: {e}")
        
        # 7. Получаем список компаний
        print("\n🏢 7. Получение списка компаний:")
        try:
            companies = await okdesk.get_companies(limit=5)
            print(f"Найдено компаний: {len(companies)}")
            if companies:
                print("Пример компании:")
                print(json.dumps(companies[0], indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Ошибка получения компаний: {e}")
            
    finally:
        await okdesk.close()

if __name__ == "__main__":
    asyncio.run(test_api())
