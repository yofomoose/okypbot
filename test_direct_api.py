"""
Прямое тестирование API для понимания правильных эндпоинтов
"""
import asyncio
import aiohttp
import json
from config import OKDESK_API_TOKEN, OKDESK_BASE_URL

async def test_direct_api():
    """Тестируем API напрямую для понимания структуры"""
    base_url = OKDESK_BASE_URL.rstrip('/')
    
    # Возможные эндпоинты для заявок
    issue_endpoints = [
        '/api/v1/issues',
        '/api/v1/tickets',  # Часто заявки называют tickets
        '/api/v1/requests',
        '/api/issues',
        '/api/tickets',
        '/issues',
        '/tickets'
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Тестируем различные эндпоинты для заявок...")
        print("=" * 60)
        
        # Тестируем заявки
        for endpoint in issue_endpoints:
            url = f"{base_url}{endpoint}"
            params = {'api_token': OKDESK_API_TOKEN, 'limit': 1}
            
            try:
                async with session.get(url, params=params) as response:
                    print(f"📡 {endpoint}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Успех! Структура: {type(data)}")
                        if isinstance(data, dict):
                            print(f"   📊 Ключи: {list(data.keys())}")
                        elif isinstance(data, list) and data:
                            print(f"   📦 Список из {len(data)} элементов")
                            print(f"   🔑 Первый элемент: {list(data[0].keys()) if data[0] else 'пустой'}")
                    elif response.status in [401, 403]:
                        print(f"   🔒 Нет доступа")
                    else:
                        print(f"   ❌ Ошибка")
            except Exception as e:
                print(f"   ❌ Исключение: {str(e)[:50]}...")
        
        print("\n" + "=" * 60)
        print("🔍 Тестируем создание контакта...")
        
        # Пробуем создать тестовый контакт
        contact_data = {
            'first_name': 'Тест',
            'last_name': 'Контакт',
            'phone': '+79999999999',
            'email': 'test@example.com'
        }
        
        url = f"{base_url}/api/v1/contacts"
        params = {'api_token': OKDESK_API_TOKEN}
        
        try:
            async with session.post(url, params=params, json=contact_data) as response:
                print(f"📡 POST /api/v1/contacts: HTTP {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Контакт создан!")
                    print(f"   📊 Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
                elif response.status == 201:
                    data = await response.json()
                    print(f"   ✅ Контакт создан!")
                    print(f"   📊 Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка создания: {error_text}")
        except Exception as e:
            print(f"   ❌ Исключение при создании: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🔍 Тестируем создание компании...")
        
        # Пробуем создать тестовую компанию
        company_data = {
            'name': 'Тестовая Компания ООО',
            'phone': '+79999999998',
            'email': 'company@example.com'
        }
        
        url = f"{base_url}/api/v1/companies"
        
        try:
            async with session.post(url, params=params, json=company_data) as response:
                print(f"📡 POST /api/v1/companies: HTTP {response.status}")
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"   ✅ Компания создана!")
                    print(f"   📊 Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка создания: {error_text}")
        except Exception as e:
            print(f"   ❌ Исключение при создании: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🔍 Повторно проверяем контакты и компании...")
        
        # Проверяем контакты после создания
        url = f"{base_url}/api/v1/contacts"
        params = {'api_token': OKDESK_API_TOKEN, 'limit': 5}
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"📋 Контакты: найдено {len(data)}")
                    if data:
                        print(f"   📊 Первый контакт: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"   ❌ Ошибка получения контактов: {str(e)}")
        
        # Проверяем компании после создания
        url = f"{base_url}/api/v1/companies"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"🏢 Компании: найдено {len(data)}")
                    if data:
                        print(f"   📊 Первая компания: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"   ❌ Ошибка получения компаний: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_direct_api())
