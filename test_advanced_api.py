"""
Проверяем параметры компании и альтернативные способы получения данных
"""
import asyncio
import aiohttp
import json
from config import OKDESK_API_TOKEN, OKDESK_BASE_URL

async def test_advanced_api():
    """Расширенное тестирование API"""
    base_url = OKDESK_BASE_URL.rstrip('/')
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Проверяем параметры компании через GET...")
        print("=" * 60)
        
        # Сначала попробуем создать компанию без ИНН
        print("\n1. Попытка создания компании без ИНН:")
        company_data = {
            'name': 'Тестовая Компания Без ИНН',
            'phone': '+79999999999',
            'email': 'test@noinn.com'
        }
        
        url = f"{base_url}/api/v1/companies"
        params = {'api_token': OKDESK_API_TOKEN}
        
        try:
            async with session.post(url, params=params, json=company_data) as response:
                print(f"   📡 HTTP {response.status}")
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"   ✅ Создана! ID: {data.get('id')}")
                    print(f"   📊 Структура: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка: {error_text}")
        except Exception as e:
            print(f"   ❌ Исключение: {str(e)}")
        
        # Попробуем создать компанию с пустым ИНН
        print("\n2. Попытка создания компании с пустым ИНН:")
        company_data = {
            'name': 'Тестовая Компания Пустой ИНН',
            'phone': '+79999999998',
            'email': 'test@emptyinn.com',
            'inn_company': ''
        }
        
        try:
            async with session.post(url, params=params, json=company_data) as response:
                print(f"   📡 HTTP {response.status}")
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"   ✅ Создана! ID: {data.get('id')}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка: {error_text}")
        except Exception as e:
            print(f"   ❌ Исключение: {str(e)}")
        
        # Проверяем получение контактов с использованием контакта, который мы точно создали
        print("\n3. Проверяем получение конкретного контакта по ID:")
        
        # Пробуем получить контакт с ID 6 (который мы создали ранее)
        contact_ids_to_test = [6, 7, 8]  # ID которые были созданы в предыдущих тестах
        
        for contact_id in contact_ids_to_test:
            url = f"{base_url}/api/v1/contacts/{contact_id}"
            try:
                async with session.get(url, params={'api_token': OKDESK_API_TOKEN}) as response:
                    print(f"   📡 GET /contacts/{contact_id}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Найден контакт: {data.get('name')} (ID: {data.get('id')})")
                        print(f"   📞 Телефон: {data.get('phone')}")
                        print(f"   📧 Email: {data.get('email')}")
                        break
                    else:
                        print(f"   ❌ Контакт {contact_id} не найден")
            except Exception as e:
                print(f"   ❌ Ошибка получения контакта {contact_id}: {str(e)}")
        
        # Проверяем альтернативные эндпоинты для получения данных
        print("\n4. Проверяем альтернативные эндпоинты:")
        
        alternative_endpoints = [
            '/api/v1/contacts/all',
            '/api/v1/contacts/list',
            '/contacts',
            '/api/contacts'
        ]
        
        for endpoint in alternative_endpoints:
            url = f"{base_url}{endpoint}"
            try:
                async with session.get(url, params={'api_token': OKDESK_API_TOKEN, 'limit': 5}) as response:
                    print(f"   📡 {endpoint}: HTTP {response.status}")
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, list) and data:
                                print(f"   ✅ Найдено контактов: {len(data)}")
                                break
                            elif isinstance(data, dict) and data:
                                print(f"   📊 Структура dict: {list(data.keys())}")
                        except:
                            text = await response.text()
                            print(f"   📄 Не JSON ответ: {text[:50]}...")
            except Exception as e:
                print(f"   ❌ Ошибка {endpoint}: {str(e)}")
        
        # Проверяем поиск по существующему контакту
        print("\n5. Поиск по существующим данным:")
        
        search_params = [
            {'phone': '+79999999999'},  # Телефон тестового контакта
            {'email': 'test@example.com'},  # Email тестового контакта
            {'search_string': 'Тест'},  # Поиск по имени
            {'name': 'Контакт'},  # Поиск по фамилии
        ]
        
        for search_param in search_params:
            params_with_token = {'api_token': OKDESK_API_TOKEN}
            params_with_token.update(search_param)
            
            url = f"{base_url}/api/v1/contacts"
            try:
                async with session.get(url, params=params_with_token) as response:
                    print(f"   📡 Поиск {search_param}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and data:
                            print(f"   ✅ Найдено: {len(data)} контактов")
                            contact = data[0]
                            print(f"      {contact.get('name')} - {contact.get('phone')}")
                        elif isinstance(data, dict):
                            print(f"   📊 Dict: {list(data.keys())}")
                        else:
                            print(f"   📦 Пустой результат")
            except Exception as e:
                print(f"   ❌ Ошибка поиска: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_advanced_api())
