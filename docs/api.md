# Документация API

## Okdesk API Integration

### Базовая конфигурация

```python
from api.okdesk_api import OkdeskAPI

# Инициализация клиента
okdesk = OkdeskAPI(
    base_url="https://yourcompany.okdesk.ru",
    api_token="your_api_token"
)
```

### Методы API

#### Работа с компаниями

##### `search_company_by_inn(inn: str) -> Optional[Dict]`
Поиск компании по ИНН.

```python
company = await okdesk.search_company_by_inn("1234567890")
if company:
    print(f"Найдена компания: {company['name']}")
```

**Параметры:**
- `inn` (str) - ИНН компании (10 или 12 цифр)

**Возвращает:**
- `Dict` - данные компании или `None`

#### Работа с контактами

##### `search_contact(phone: str = None, email: str = None) -> List[Dict]`
Поиск контакта по телефону или email.

```python
contacts = await okdesk.search_contact(phone="+79001234567")
```

**Параметры:**
- `phone` (str, optional) - номер телефона
- `email` (str, optional) - email адрес

**Возвращает:**
- `List[Dict]` - список найденных контактов

##### `create_contact(first_name: str, last_name: str, **kwargs) -> Dict`
Создание нового контакта.

```python
contact = await okdesk.create_contact(
    first_name="Иван",
    last_name="Петров",
    phone="+79001234567",
    email="ivan@example.com",
    company_id=123,
    position="Менеджер",
    comment="Telegram: @username"
)
```

**Обязательные параметры:**
- `first_name` (str) - имя
- `last_name` (str) - фамилия

**Дополнительные параметры:**
- `phone` (str) - номер телефона
- `email` (str) - email адрес
- `company_id` (int) - ID компании
- `position` (str) - должность
- `comment` (str) - комментарий

##### `update_contact(contact_id: int, **kwargs) -> Dict`
Обновление существующего контакта.

```python
updated_contact = await okdesk.update_contact(
    contact_id=123,
    company_id=456,
    position="Старший менеджер"
)
```

**Параметры:**
- `contact_id` (int) - ID контакта
- `**kwargs` - поля для обновления

#### Работа с заявками

##### `create_issue(title: str, description: str, **kwargs) -> Dict`
Создание новой заявки.

```python
issue = await okdesk.create_issue(
    title="Проблема с доступом",
    description="Не могу войти в систему",
    contact_id=123,
    priority="high"
)
```

**Обязательные параметры:**
- `title` (str) - заголовок заявки
- `description` (str) - описание проблемы

**Дополнительные параметры:**
- `contact_id` (int) - ID контакта
- `company_id` (int) - ID компании
- `priority` (str) - приоритет заявки
- `assignee_id` (int) - ID ответственного

##### `get_issues(limit: int = 50) -> List[Dict]`
Получение списка заявок.

```python
issues = await okdesk.get_issues(limit=20)
```

##### `update_issue_contact(issue_id: int, contact_id: int) -> Dict`
Привязка заявки к контакту.

```python
result = await okdesk.update_issue_contact(
    issue_id=456,
    contact_id=123
)
```

### Обработка ошибок

Все методы API могут выбрасывать исключения:

```python
try:
    contact = await okdesk.create_contact(
        first_name="Тест",
        last_name="Тестов"
    )
except Exception as e:
    logger.error(f"Ошибка создания контакта: {e}")
```

### Логирование

API клиент автоматически логирует все запросы:

```
2025-08-16 19:54:00 - api.okdesk_api - INFO - POST https://company.okdesk.ru/api/v1/contacts
2025-08-16 19:54:01 - api.okdesk_api - INFO - Response status: 200
```

### Примеры использования

#### Полный цикл регистрации пользователя

```python
async def register_user(phone: str, first_name: str, last_name: str, company_inn: str = None):
    okdesk = OkdeskAPI(base_url=OKDESK_BASE_URL, api_token=OKDESK_API_TOKEN)
    
    # 1. Поиск существующего контакта
    existing_contacts = await okdesk.search_contact(phone=phone)
    
    if existing_contacts:
        contact = existing_contacts[0]
        
        # 2. Если есть ИНН компании, ищем компанию и обновляем контакт
        if company_inn:
            company = await okdesk.search_company_by_inn(company_inn)
            if company and not contact.get('company_id'):
                contact = await okdesk.update_contact(
                    contact['id'], 
                    company_id=company['id']
                )
    else:
        # 3. Создаем новый контакт
        contact_data = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone
        }
        
        # Если есть компания, добавляем её ID
        if company_inn:
            company = await okdesk.search_company_by_inn(company_inn)
            if company:
                contact_data['company_id'] = company['id']
        
        contact = await okdesk.create_contact(**contact_data)
    
    return contact
```

#### Создание заявки с привязкой к пользователю

```python
async def create_user_issue(user_id: int, title: str, description: str):
    # Получаем данные пользователя из базы
    user = await get_user(user_id)
    
    if not user or not user.get('okdesk_contact_id'):
        raise ValueError("Пользователь не зарегистрирован")
    
    # Создаем заявку
    issue = await okdesk.create_issue(
        title=title,
        description=description,
        contact_id=user['okdesk_contact_id']
    )
    
    return issue
```
