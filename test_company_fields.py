"""
Детальное тестирование полей для создания компании
"""
import asyncio
import aiohttp
import json
from config import OKDESK_API_TOKEN, OKDESK_BASE_URL

async def test_company_fields():
    """Тестируем различные варианты полей для создания компании"""
    base_url = OKDESK_BASE_URL.rstrip('/')
    
    # Различные варианты полей для ИНН
    inn_field_variants = [
        {'inn_company': '1234567890'},
        {'inn': '1234567890'},
        {'company_inn': '1234567890'},
        {'tax_number': '1234567890'},
        {'tax_id': '1234567890'}
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Тестируем поля для создания компании...")
        print("=" * 60)
        
        for i, inn_field in enumerate(inn_field_variants, 1):
            company_data = {
                'name': f'Тестовая Компания {i}',
                'phone': f'+7912345678{i}',
                'email': f'company{i}@example.com'
            }
            company_data.update(inn_field)
            
            url = f"{base_url}/api/v1/companies"
            params = {'api_token': OKDESK_API_TOKEN}
            
            print(f"\n{i}. Тестируем поле: {list(inn_field.keys())[0]}")
            print(f"   Данные: {company_data}")
            
            try:
                async with session.post(url, params=params, json=company_data) as response:
                    print(f"   📡 HTTP {response.status}")
                    if response.status in [200, 201]:
                        data = await response.json()
                        print(f"   ✅ Успех! ID: {data.get('id')}")
                        print(f"   📊 ИНН в ответе: {data.get('inn_company', 'не найден')}")
                        break  # Если успешно создалась, выходим
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Ошибка: {error_text}")
            except Exception as e:
                print(f"   ❌ Исключение: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🔍 Тестируем получение данных с разными параметрами...")
        
        # Тестируем получение контактов с разными параметрами
        contact_params_variants = [
            {},
            {'limit': 10},
            {'limit': 50},
            {'page': 1},
            {'page': 1, 'limit': 10},
            {'sort_by': 'created_at'},
            {'sort_direction': 'desc'}
        ]
        
        for i, params_extra in enumerate(contact_params_variants, 1):
            params = {'api_token': OKDESK_API_TOKEN}
            params.update(params_extra)
            
            url = f"{base_url}/api/v1/contacts"
            
            print(f"\n{i}. Параметры: {params_extra}")
            
            try:
                async with session.get(url, params=params) as response:
                    print(f"   📡 HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   📊 Тип ответа: {type(data)}")
                        if isinstance(data, list):
                            print(f"   📦 Найдено контактов: {len(data)}")
                            if data:
                                print(f"   👤 Первый контакт ID: {data[0].get('id')}")
                                break  # Если нашли данные, выходим
                        elif isinstance(data, dict):
                            print(f"   🔑 Ключи ответа: {list(data.keys())}")
                            if 'data' in data:
                                print(f"   📦 Контактов в data: {len(data['data'])}")
                            if 'contacts' in data:
                                print(f"   📦 Контактов в contacts: {len(data['contacts'])}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Ошибка: {error_text[:100]}...")
            except Exception as e:
                print(f"   ❌ Исключение: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_company_fields())
