"""
Простой тест создания контакта с указанием ИНН компании
"""
import asyncio
from api.okdesk_api import OkdeskAPI

async def test_simple_contact_creation():
    """Простой тест создания контакта с ИНН"""
    okdesk = OkdeskAPI()
    
    try:
        print("🔍 Создание контакта юридического лица...")
        print("=" * 50)
        
        # Создаем контакт с дополнительным полем для ИНН в комментарии
        print("\n👤 Создание контакта с ИНН компании:")
        
        contact_data = {
            'first_name': 'Владимир',
            'last_name': 'Кузнецов',
            'patronymic': 'Павлович',
            'phone': '+79887776655',
            'email': 'v.kuznetsov@testcompany.ru',
            'position': 'Генеральный директор',
            'comment': 'ИНН компании: 1337. Юридическое лицо. Создан через Telegram бот.'
        }
        
        contact = await okdesk.create_contact(**contact_data)
        
        print(f"   ✅ Контакт создан! ID: {contact.get('id')}")
        print(f"   👤 ФИО: {contact.get('first_name')} {contact.get('last_name')}")
        print(f"   👔 Должность: {contact.get('position')}")
        print(f"   📞 Телефон: {contact.get('phone')}")
        print(f"   📧 Email: {contact.get('email')}")
        print(f"   💬 Комментарий: {contact.get('comment')}")
        
        # Проверяем поиск
        print(f"\n🔍 Поиск созданного контакта:")
        found_contacts = await okdesk.search_contact(phone="+79887776655")
        
        if found_contacts:
            found_contact = found_contacts[0] if isinstance(found_contacts, list) else found_contacts
            print(f"   ✅ Контакт найден:")
            print(f"      ID: {found_contact.get('id')}")
            print(f"      Имя: {found_contact.get('name')}")
            print(f"      Комментарий: {found_contact.get('comment')}")
        else:
            print(f"   ❌ Контакт не найден")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await okdesk.close()

if __name__ == "__main__":
    asyncio.run(test_simple_contact_creation())
