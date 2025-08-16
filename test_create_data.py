"""
Тест создания контактов и компаний в Okdesk
"""
import asyncio
from api.okdesk_api import OkdeskAPI
import json

async def test_create_data():
    """Тестируем создание контактов и компаний"""
    okdesk = OkdeskAPI()
    
    try:
        print("🔍 Тест создания данных в Okdesk...")
        print("=" * 50)
        
        # 1. Создаем контакт (физическое лицо)
        print("\n👤 1. Создание контакта (физическое лицо):")
        try:
            contact_data = {
                'first_name': 'Иван',
                'last_name': 'Петров',
                'patronymic': 'Сергеевич',
                'phone': '+79123456789',
                'email': 'ivan.petrov@example.com',
                'comment': 'Тестовый контакт из бота'
            }
            
            contact = await okdesk.create_contact(**contact_data)
            print(f"   ✅ Контакт создан! ID: {contact.get('id')}")
            print(f"   📋 Имя: {contact.get('first_name')} {contact.get('last_name')}")
            print(f"   📞 Телефон: {contact.get('phone')}")
            print(f"   📧 Email: {contact.get('email')}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания контакта: {e}")
        
        # 2. Создаем компанию
        print("\n🏢 2. Создание компании:")
        try:
            company_data = {
                'name': 'ООО "Тестовая Компания"',
                'inn': '1234567890',  # Тестовый ИНН
                'phone': '+79234567890',
                'email': 'info@testcompany.ru',
                'address': 'г. Москва, ул. Тестовая, д. 1',
                'description': 'Тестовая компания для проверки API'
            }
            
            company = await okdesk.create_company(**company_data)
            print(f"   ✅ Компания создана! ID: {company.get('id')}")
            print(f"   🏢 Название: {company.get('name')}")
            print(f"   🏛️ ИНН: {company.get('inn_company')}")
            print(f"   📞 Телефон: {company.get('phone')}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания компании: {e}")
        
        # 3. Создаем контакт привязанный к компании
        print("\n👔 3. Создание контакта для компании:")
        try:
            # Получаем ID последней созданной компании
            companies = await okdesk.get_companies(limit=1)
            company_id = None
            if companies:
                company_id = companies[0].get('id')
                print(f"   🏢 Привязываем к компании ID: {company_id}")
            
            employee_data = {
                'first_name': 'Мария',
                'last_name': 'Иванова',
                'patronymic': 'Александровна',
                'phone': '+79345678901',
                'email': 'maria.ivanova@testcompany.ru',
                'position': 'Менеджер по продажам',
                'company_id': company_id,
                'comment': 'Сотрудник тестовой компании'
            }
            
            employee = await okdesk.create_contact(**employee_data)
            print(f"   ✅ Сотрудник создан! ID: {employee.get('id')}")
            print(f"   👔 Должность: {employee.get('position')}")
            print(f"   🏢 Компания: {employee.get('company_name', 'Не указана')}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания сотрудника: {e}")
        
        # 4. Проверяем созданные данные
        print("\n📋 4. Проверка созданных данных:")
        
        # Получаем контакты
        try:
            contacts = await okdesk.get_contacts(limit=10)
            print(f"   👥 Всего контактов: {len(contacts)}")
            for i, contact in enumerate(contacts[-3:], 1):  # Показываем последние 3
                print(f"   {i}. {contact.get('name', 'Без имени')} (ID: {contact.get('id')})")
        except Exception as e:
            print(f"   ❌ Ошибка получения контактов: {e}")
        
        # Получаем компании
        try:
            companies = await okdesk.get_companies(limit=10)
            print(f"   🏢 Всего компаний: {len(companies)}")
            for i, company in enumerate(companies[-2:], 1):  # Показываем последние 2
                print(f"   {i}. {company.get('name', 'Без названия')} (ID: {company.get('id')})")
        except Exception as e:
            print(f"   ❌ Ошибка получения компаний: {e}")
        
        # 5. Тестируем поиск
        print("\n🔍 5. Тестирование поиска:")
        
        # Поиск контакта по телефону
        try:
            found_contacts = await okdesk.search_contact(phone="+79123456789")
            print(f"   📞 Найдено контактов по телефону: {len(found_contacts)}")
            if found_contacts:
                contact = found_contacts[0]
                print(f"      Найден: {contact.get('name')} (ID: {contact.get('id')})")
        except Exception as e:
            print(f"   ❌ Ошибка поиска контакта: {e}")
        
        # Поиск компании
        try:
            found_companies = await okdesk.search_company("Тестовая")
            print(f"   🏢 Найдено компаний: {len(found_companies)}")
            if found_companies:
                company = found_companies[0]
                print(f"      Найдена: {company.get('name')} (ID: {company.get('id')})")
        except Exception as e:
            print(f"   ❌ Ошибка поиска компании: {e}")
            
    finally:
        await okdesk.close()
        print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_create_data())
