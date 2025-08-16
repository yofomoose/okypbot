"""
Тест функции привязки юридического лица к компании по ИНН
"""
import asyncio
from api.okdesk_api import OkdeskAPI
import json

async def test_company_binding():
    """Тестируем привязку контакта к компании по ИНН"""
    okdesk = OkdeskAPI()
    
    try:
        print("🔍 Тест привязки к компании по ИНН...")
        print("=" * 50)
        
        # 1. Получаем список компаний и их ИНН
        print("\n🏢 1. Получение списка компаний:")
        try:
            companies = await okdesk.get_companies(limit=10)
            print(f"Найдено компаний: {len(companies)}")
            
            companies_with_inn = []
            for company in companies:
                inn = company.get('inn_company')
                if inn:
                    companies_with_inn.append(company)
                    print(f"   • {company.get('name')} - ИНН: {inn}")
            
            if not companies_with_inn:
                print("   ❌ Компании с ИНН не найдены")
                return
                
        except Exception as e:
            print(f"   ❌ Ошибка получения компаний: {e}")
            return
        
        # 2. Тестируем поиск компании по ИНН
        test_inn = companies_with_inn[0].get('inn_company')  # Берем первую компанию с ИНН
        print(f"\n🔍 2. Поиск компании по ИНН: {test_inn}")
        
        try:
            found_company = await okdesk.search_company_by_inn(test_inn)
            if found_company:
                print(f"   ✅ Компания найдена:")
                print(f"      Название: {found_company.get('name')}")
                print(f"      ID: {found_company.get('id')}")
                print(f"      ИНН: {found_company.get('inn_company')}")
            else:
                print(f"   ❌ Компания с ИНН {test_inn} не найдена")
                return
                
        except Exception as e:
            print(f"   ❌ Ошибка поиска компании: {e}")
            return
        
        # 3. Создаем контакт с привязкой к компании
        print(f"\n👤 3. Создание контакта с привязкой к компании:")
        
        try:
            contact_data = {
                'first_name': 'Александр',
                'last_name': 'Сидоров',
                'patronymic': 'Викторович',
                'phone': '+79876543210',
                'email': 'a.sidorov@company.ru',
                'position': 'Директор по развитию',
                'comment': 'Тестовый контакт с привязкой к компании через ИНН'
            }
            
            contact = await okdesk.create_contact_with_company_by_inn(
                company_inn=test_inn,
                **contact_data
            )
            
            print(f"   ✅ Контакт создан! ID: {contact.get('id')}")
            print(f"   👤 ФИО: {contact.get('first_name')} {contact.get('last_name')}")
            print(f"   🏢 Компания ID: {contact.get('company_id')}")
            print(f"   🏢 Название компании: {contact.get('company_name')}")
            print(f"   👔 Должность: {contact.get('position')}")
            print(f"   📞 Телефон: {contact.get('phone')}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания контакта: {e}")
        
        # 4. Проверяем созданный контакт
        print(f"\n📋 4. Проверка созданного контакта:")
        
        try:
            # Поиск по телефону
            found_contacts = await okdesk.search_contact(phone="+79876543210")
            print(f"   📞 Найдено контактов по телефону: {len(found_contacts)}")
            
            if found_contacts:
                contact = found_contacts[0] if isinstance(found_contacts, list) else found_contacts
                print(f"   ✅ Найден контакт:")
                print(f"      ID: {contact.get('id')}")
                print(f"      Имя: {contact.get('name')}")
                print(f"      Компания ID: {contact.get('company_id')}")
                print(f"      Название компании: {contact.get('company_name', 'Не указано')}")
                
        except Exception as e:
            print(f"   ❌ Ошибка поиска контакта: {e}")
        
        # 5. Тестируем с несуществующим ИНН
        print(f"\n❌ 5. Тест с несуществующим ИНН:")
        
        try:
            fake_inn = "9999999999"
            contact_data = {
                'first_name': 'Тест',
                'last_name': 'Несуществующий ИНН',
                'phone': '+79999888777',
                'email': 'test@fake.com'
            }
            
            contact = await okdesk.create_contact_with_company_by_inn(
                company_inn=fake_inn,
                **contact_data
            )
            
            print(f"   ✅ Контакт создан без привязки к компании")
            print(f"   🏢 Компания ID: {contact.get('company_id', 'Не указано')}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            
    finally:
        await okdesk.close()
        print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_company_binding())
