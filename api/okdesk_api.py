"""
Клиент для работы с Okdesk API
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from config import OKDESK_API_TOKEN, OKDESK_BASE_URL

logger = logging.getLogger(__name__)

class OkdeskAPI:
    """Класс для работы с API Okdesk"""
    
    def __init__(self):
        self.base_url = OKDESK_BASE_URL
        self.token = OKDESK_API_TOKEN
        self.session = None
        
    async def __aenter__(self):
        self.session = await self._get_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def close(self):
        """Закрыть сессию"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить HTTP сессию"""
        return aiohttp.ClientSession(
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Выполнить HTTP запрос к API"""
        if not self.session:
            self.session = await self._get_session()
            
        url = f"{self.base_url}/api/v1{endpoint}"
        
        # Добавляем API токен в параметры
        if '?' in endpoint:
            url += f"&api_token={self.token}"
        else:
            url += f"?api_token={self.token}"
            
        logger.info(f"{method} {url}")
        
        try:
            async with self.session.request(method, url, json=data) as response:
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response: {response_text[:500]}")
                
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"API Error: {e}")
            raise
    
    async def get_issues(self, limit: int = 50) -> List[Dict]:
        """Получить список заявок"""
        params = {'limit': limit}
        
        try:
            # Конвертируем параметры в строку запроса вручную
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint = f"/issues?{query_string}"
            
            response = await self._make_request('GET', endpoint)
            
            # API возвращает данные в разных форматах
            if isinstance(response, dict):
                # Если есть поле data с массивом
                if 'data' in response:
                    return response['data']
                # Если есть поле issues с массивом  
                elif 'issues' in response:
                    return response['issues']
                # Если сам объект содержит заявки
                elif 'id' in response:
                    return [response]
            elif isinstance(response, list):
                return response
                
            return []
        except Exception as e:
            logger.error(f"Ошибка получения заявок: {e}")
            return []
    
    async def get_issue(self, issue_id: int) -> Dict:
        """Получить заявку по ID"""
        response = await self._make_request('GET', f'/issues/{issue_id}')
        return response
    
    async def create_issue(self, title: str, description: str, **kwargs) -> Dict:
        """Создать новую заявку"""
        data = {
            'title': title,
            'description': description,
            'type_id': kwargs.get('type_id', 1),  # Тип заявки по умолчанию
            'priority_id': kwargs.get('priority_id', 2),  # Приоритет по умолчанию
            'status_id': kwargs.get('status_id', 1),  # Статус по умолчанию
        }
        
        # Добавляем дополнительные параметры если они есть
        if 'contact_id' in kwargs:
            data['contact_id'] = kwargs['contact_id']
        if 'company_id' in kwargs:
            data['company_id'] = kwargs['company_id']
        if 'assignee_id' in kwargs:
            data['assignee_id'] = kwargs['assignee_id']
        
        logger.info(f"Создаем заявку с данными: {data}")
        response = await self._make_request('POST', '/issues', data)
        return response
    
    async def create_registration_issue(self, full_name: str, phone: str, user_type: str, **kwargs) -> Dict:
        """Создать заявку для регистрации пользователя в системе"""
        title = "Регистрация нового пользователя в Telegram Bot"
        
        description = f"""Новый пользователь зарегистрировался через Telegram бот:

ФИО: {full_name}
Телефон: {phone}
Тип пользователя: {'Физическое лицо' if user_type == 'individual' else 'Юридическое лицо'}"""
        
        if user_type == "legal":
            if 'position' in kwargs:
                description += f"\nДолжность: {kwargs['position']}"
            if 'company_inn' in kwargs:
                description += f"\nИНН компании: {kwargs['company_inn']}"
        
        description += f"\n\nТелеграм ID: {kwargs.get('telegram_id', 'Не указан')}"
        
        description += "\n\nДанная заявка создана автоматически при регистрации пользователя в Telegram боте."
        
        # Если есть contact_id, привязываем заявку к контакту
        create_params = {}
        if 'contact_id' in kwargs:
            create_params['contact_id'] = kwargs['contact_id']
            description += f"\nКонтакт ID: {kwargs['contact_id']}"
        
        return await self.create_issue(title, description, **create_params)
    
    async def update_issue_status(self, issue_id: int, status_id: int) -> Dict:
        """Обновить статус заявки"""
        data = {'status_id': status_id}
        response = await self._make_request('PATCH', f'/issues/{issue_id}/status', data)
        return response
    
    async def update_issue_contact(self, issue_id: int, contact_id: int) -> Dict:
        """Привязать контакт к заявке"""
        data = {'contact_id': contact_id}
        response = await self._make_request('PATCH', f'/issues/{issue_id}', data)
        return response
    
    async def add_comment(self, issue_id: int, content: str, is_public: bool = True) -> Dict:
        """Добавить комментарий к заявке"""
        data = {
            'content': content,
            'public': is_public
        }
        response = await self._make_request('POST', f'/issues/{issue_id}/comments', data)
        return response
    
    async def get_companies(self, limit: int = 50) -> List[Dict]:
        """Получить список компаний"""
        try:
            # Формируем URL с параметрами
            endpoint = f"/companies/list?limit={limit}"
            response = await self._make_request('GET', endpoint)
            
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            logger.error(f"Ошибка получения компаний: {e}")
            return []
    
    async def search_company(self, query: str) -> List[Dict]:
        """Поиск компании по названию"""
        endpoint = f"/companies/list?search_string={query}"
        response = await self._make_request('GET', endpoint)
        return response if isinstance(response, list) else [response] if response else []
    
    async def search_company_by_inn(self, inn: str) -> Optional[Dict]:
        """Поиск компании по ИНН через параметры"""
        try:
            logger.info(f"Ищем компанию с ИНН: {inn}")
            
            # Получаем список компаний
            endpoint = "/companies/list?limit=100"
            response = await self._make_request('GET', endpoint)
            
            companies = response if isinstance(response, list) else []
            logger.info(f"Получено компаний для поиска: {len(companies)}")
            
            # Ищем компанию с нужным ИНН в параметрах
            for company in companies:
                logger.debug(f"Проверяем компанию: {company.get('name', 'Без названия')}")
                
                # Проверяем параметры компании
                parameters = company.get('parameters', [])
                if parameters:
                    for param in parameters:
                        # Ищем параметр с ИНН
                        if isinstance(param, dict):
                            param_name = param.get('name', '').lower()
                            param_value = str(param.get('value', ''))
                            
                            # Проверяем разные варианты названий поля ИНН
                            if any(inn_field in param_name for inn_field in ['инн', 'inn', 'ИНН']):
                                logger.info(f"Найден параметр ИНН: {param_name} = {param_value}")
                                if param_value == inn:
                                    logger.info(f"Найдена компания с ИНН {inn}: {company.get('name')}")
                                    return company
            
            logger.info(f"Компания с ИНН {inn} не найдена")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска компании по ИНН: {e}")
            return None
    
    async def get_contacts(self, limit: int = 50) -> List[Dict]:
        """Получить список контактов"""
        try:
            endpoint = f"/contacts?limit={limit}"
            response = await self._make_request('GET', endpoint)
            
            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            logger.error(f"Ошибка получения контактов: {e}")
            return []
    
    async def search_contact(self, phone: str = None, email: str = None, search_string: str = None) -> List[Dict]:
        """Поиск контакта"""
        params = {}
        if phone:
            params['phone'] = phone
        elif email:
            params['email'] = email
        elif search_string:
            params['search_string'] = search_string
        
        response = await self._make_request('GET', '/contacts', params)
        
        # API может возвращать один контакт как dict или список
        if isinstance(response, dict) and 'id' in response:
            return [response]  # Возвращаем как список
        elif isinstance(response, list):
            return response
        return []
    
    async def get_contact_fields(self) -> Dict:
        """Получить доступные поля для контактов"""
        try:
            response = await self._make_request('GET', '/contacts/fields')
            return response
        except Exception as e:
            logger.error(f"Ошибка получения полей контактов: {e}")
            return {}
    
    async def create_contact(self, first_name: str, last_name: str, **kwargs) -> Dict:
        """Создать новый контакт"""
        data = {
            'first_name': first_name,
            'last_name': last_name
        }
        
        # Добавляем дополнительные поля
        for field in ['phone', 'email', 'company_id', 'position', 'comment']:
            if field in kwargs and kwargs[field]:
                data[field] = kwargs[field]
        
        logger.info(f"Создаем контакт с данными: {data}")
        response = await self._make_request('POST', '/contacts', data)
        return response

    async def update_contact(self, contact_id: int, **kwargs) -> Dict:
        """Обновить существующий контакт"""
        data = {}
        
        # Добавляем только переданные поля для обновления
        for field in ['first_name', 'last_name', 'phone', 'email', 'company_id', 'position', 'comment']:
            if field in kwargs and kwargs[field] is not None:
                data[field] = kwargs[field]
        
        if not data:
            raise ValueError("Нет данных для обновления контакта")
        
        logger.info(f"Обновляем контакт {contact_id} с данными: {data}")
        response = await self._make_request('PUT', f'/contacts/{contact_id}', data)
        return response

    async def create_contact_with_company_by_inn(self, first_name: str, last_name: str, company_inn: str, **kwargs) -> Dict:
        """Создать контакт и привязать к компании по ИНН"""
        try:
            # Сначала ищем компанию по ИНН
            company = await self.search_company_by_inn(company_inn)
            
            if company:
                logger.info(f"Найдена компания: {company.get('name')} (ID: {company.get('id')})")
                kwargs['company_id'] = company['id']
            else:
                logger.warning(f"Компания с ИНН {company_inn} не найдена")
            
            # Создаем контакт
            contact = await self.create_contact(first_name, last_name, **kwargs)
            
            return contact
            
        except Exception as e:
            logger.error(f"Ошибка создания контакта с компанией: {e}")
            raise
    
    async def get_issue_types(self) -> List[Dict]:
        """Получить типы заявок"""
        response = await self._make_request('GET', '/issues/types')
        return response if isinstance(response, list) else []
    
    async def get_issue_priorities(self) -> List[Dict]:
        """Получить приоритеты заявок"""
        response = await self._make_request('GET', '/issues/priorities')
        return response if isinstance(response, list) else []
    
    async def get_issue_statuses(self) -> List[Dict]:
        """Получить статусы заявок"""
        response = await self._make_request('GET', '/issues/statuses')
        return response if isinstance(response, list) else []
    
    async def get_employees(self) -> List[Dict]:
        """Получить список сотрудников"""
        response = await self._make_request('GET', '/employees')
        return response if isinstance(response, list) else []
    
    async def close(self):
        """Закрыть сессию при завершении работы"""
        if self.session and not self.session.closed:
            await self.session.close()