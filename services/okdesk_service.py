"""
Сервис для работы с Okdesk API
"""

import aiohttp
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OkdeskService:
    """Сервис для работы с Okdesk API"""
    
    def __init__(self, api_key: str, company_id: str, base_url: str = "https://your-company.okdesk.ru"):
        self.api_key = api_key
        self.company_id = company_id
        self.base_url = base_url
        self.session = None
        
    async def initialize(self):
        """Инициализация HTTP сессии"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    'Content-Type': 'application/json'
                }
            )
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_issue(self, title: str, description: str, contact_id: int, 
                          company_id: int = None, priority: str = "normal") -> Optional[Dict]:
        """Создает новую заявку в Okdesk
        
        Args:
            title: Заголовок заявки
            description: Описание заявки
            contact_id: ID контакта
            company_id: ID компании (опционально)
            priority: Приоритет заявки
            
        Returns:
            Dict с информацией о созданной заявке или None при ошибке
        """
        try:
            url = f"{self.base_url}/api/v1/issues"
            
            data = {
                "issue": {
                    "title": title,
                    "description": description,
                    "contact_id": contact_id,
                    "priority": priority,
                    "status": "opened"
                }
            }

            if company_id:
                data["issue"]["company_id"] = company_id
                
            # Добавляем API токен в параметры запроса
            params = {'api_token': self.api_key}
                
            async with self.session.post(url, json=data, params=params) as response:
                if response.status in [200, 201]:  # Принимаем и 200, и 201 как успешные
                    result = await response.json()
                    logger.info(f"Заявка создана: ID {result.get('id', 'Unknown')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка создания заявки: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при создании заявки: {e}")
            return None
    
    async def get_current_user(self) -> Optional[Dict]:
        """Получает информацию о текущем пользователе API"""
        try:
            # Пробуем разные endpoints для получения текущего пользователя
            endpoints = [
                "/api/v1/employees/me",
                "/api/v1/users/me", 
                "/api/v1/me",
                "/api/v1/employees"  # Получим список и возьмем первого
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    params = {'api_token': self.api_key}
                    
                    logger.debug(f"Пробуем endpoint: {endpoint}")
                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"Получены данные пользователя через {endpoint}")
                            
                            # Если это список (как /employees), берем первого
                            if isinstance(data, list) and len(data) > 0:
                                user = data[0]
                                logger.info(f"Выбран первый пользователь из списка: {user.get('id', 'Unknown')}")
                                return user
                            elif isinstance(data, dict):
                                logger.info(f"Получен пользователь: {data.get('id', 'Unknown')}")
                                return data
                            else:
                                logger.warning(f"Неожиданный формат данных от {endpoint}: {type(data)}")
                        else:
                            logger.debug(f"Endpoint {endpoint} вернул {response.status}")
                            
                except Exception as endpoint_error:
                    logger.warning(f"Ошибка при запросе к {endpoint}: {endpoint_error}")
                    continue
            
            logger.warning("Не удалось получить данные пользователя через все endpoints")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения данных пользователя: {e}")
            return None
    
    async def add_comment_to_issue(self, issue_id: int, comment_text: str, 
                                 is_public: bool = True, author_id: int = None) -> bool:
        """Добавляет комментарий к заявке
        
        Args:
            issue_id: ID заявки
            comment_text: Текст комментария
            is_public: Публичный ли комментарий
            author_id: ID автора комментария (опционально)
            
        Returns:
            True если комментарий добавлен успешно
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}/comments"
            
            data = {
                "comment": {
                    "content": comment_text,
                    "public": is_public
                }
            }
            
            # Добавляем author_id если указан
            if author_id:
                data["comment"]["author_id"] = author_id
            else:
                # Пробуем получить текущего пользователя API
                logger.info("Пытаемся получить текущего пользователя API для author_id")
                current_user = await self.get_current_user()
                if current_user and isinstance(current_user, dict) and 'id' in current_user:
                    data["comment"]["author_id"] = current_user['id']
                    logger.info(f"Используем ID текущего API пользователя: {current_user['id']}")
                else:
                    logger.warning("Не удалось получить author_id, отправляем запрос без него")
                    # Убираем author_id из данных, возможно API позволит создать комментарий без него
                    pass  # Не добавляем author_id
            
            # Добавляем API токен в параметры запроса
            params = {'api_token': self.api_key}
            
            logger.info(f"Отправляем запрос на добавление комментария к заявке {issue_id}")
            logger.debug(f"Данные запроса: {data}")
            
            async with self.session.post(url, json=data, params=params) as response:
                if response.status in [200, 201]:  # Принимаем и 200, и 201 как успешные
                    logger.info(f"Комментарий успешно добавлен к заявке {issue_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка добавления комментария: {response.status} - {error_text}")
                    
                    # Если ошибка 422 с author_id, попробуем без него
                    if response.status == 422 and "author_id" in error_text:
                        logger.warning("Повторяем запрос без author_id")
                        if "author_id" in data["comment"]:
                            del data["comment"]["author_id"]
                        
                        async with self.session.post(url, json=data, params=params) as retry_response:
                            if retry_response.status in [200, 201]:
                                logger.info(f"Комментарий успешно добавлен к заявке {issue_id} (без author_id)")
                                return True
                            else:
                                retry_error_text = await retry_response.text()
                                logger.error(f"Ошибка повторного запроса: {retry_response.status} - {retry_error_text}")
                                return False
                    else:
                        return False
                    
        except Exception as e:
            logger.error(f"Ошибка при добавлении комментария: {e}")
            return False
    
    async def get_issue_comments(self, issue_id: int, since: datetime = None) -> Optional[List[Dict]]:
        """Получает комментарии заявки
        
        Args:
            issue_id: ID заявки
            since: Получить комментарии с указанной даты
            
        Returns:
            Список комментариев или None при ошибке
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}/comments"
            params = {'api_token': self.api_key}
            
            # Добавляем фильтр по времени если указан
            if since:
                params['since'] = since.isoformat()
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result if isinstance(result, list) else result.get('comments', [])
                    logger.debug(f"Получено {len(comments)} комментариев для заявки {issue_id}")
                    return comments
                elif response.status == 404:
                    logger.warning(f"Заявка {issue_id} не найдена")
                    return []
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения комментариев: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении комментариев заявки {issue_id}: {e}")
            return None
    
    async def get_issue_details(self, issue_id: int) -> Optional[Dict]:
        """Получает детали заявки
        
        Args:
            issue_id: ID заявки
            
        Returns:
            Информация о заявке или None при ошибке
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}"
            params = {'api_token': self.api_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Получены детали заявки {issue_id}")
                    return result
                elif response.status == 404:
                    logger.warning(f"Заявка {issue_id} не найдена")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения деталей заявки: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении деталей заявки {issue_id}: {e}")
            return None

    async def update_issue_status(self, issue_id: int, status: str) -> bool:
        """Обновляет статус заявки
        
        Args:
            issue_id: ID заявки
            status: Новый статус (opened, in_progress, closed, etc.)
            
        Returns:
            True если статус обновлен успешно
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}"
            params = {'api_token': self.api_key}
            
            data = {
                "issue": {
                    "status": status
                }
            }
            
            async with self.session.patch(url, json=data, params=params) as response:
                if response.status in [200, 204]:
                    logger.info(f"Статус заявки {issue_id} изменен на '{status}'")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка обновления статуса заявки: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса заявки {issue_id}: {e}")
            return False
    
    async def get_issue(self, issue_id: int) -> Optional[Dict]:
        """Получает информацию о заявке
        
        Args:
            issue_id: ID заявки
            
        Returns:
            Dict с информацией о заявке или None при ошибке
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}"
            
            # Добавляем API токен в параметры запроса
            params = {'api_token': self.api_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка получения заявки: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении заявки: {e}")
            return None
    
    async def update_issue_category(self, issue_id: int, category_id: int) -> bool:
        """Обновляет категорию заявки
        
        Args:
            issue_id: ID заявки
            category_id: ID категории в Okdesk
            
        Returns:
            True если категория обновлена успешно
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}"
            
            data = {
                "issue": {
                    "category_id": category_id
                }
            }
            
            # Добавляем API токен в параметры запроса
            params = {'api_token': self.api_key}
            
            async with self.session.patch(url, json=data, params=params) as response:
                if response.status == 200:
                    logger.info(f"Категория заявки {issue_id} обновлена")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка обновления категории: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при обновлении категории: {e}")
            return False

class IssueService:
    """Сервис для обработки заявок с ML классификацией"""
    
    def __init__(self, okdesk_service: OkdeskService):
        self.okdesk_service = okdesk_service
        
    async def create_issue_with_classification(self, title: str, description: str, 
                                             contact_id: int, company_id: int = None,
                                             user_id: int = None) -> Optional[Dict]:
        """Создает заявку с автоматической ML классификацией
        
        Args:
            title: Заголовок заявки
            description: Описание заявки
            contact_id: ID контакта в Okdesk
            company_id: ID компании в Okdesk
            user_id: ID пользователя бота для статистики
            
        Returns:
            Dict с информацией о созданной заявке и классификации
        """
        try:
            # 1. Классифицируем заявку с помощью ML
            from services.ml_service import ml_service
            
            # Для классификации используем только оригинальное описание
            # чтобы избежать дублирования и искажения смысла
            full_text = description.strip() if description.strip() else title.strip()
            
            # Если и то и другое пустое
            if not full_text:
                full_text = "Пустая заявка"
            
            logger.info(f"Заголовок: '{title}'")
            logger.info(f"Описание: '{description}'")
            logger.info(f"Итоговый текст для классификации: '{full_text}'")
            logger.info(f"Классифицируем текст: {full_text[:100]}...")
            
            classification_result = await ml_service.classify_issue(full_text, user_id)
            
            # 2. Создаем заявку в Okdesk
            issue_data = await self.okdesk_service.create_issue(
                title=title,
                description=description,
                contact_id=contact_id,
                company_id=company_id
            )
            
            if not issue_data:
                logger.error("Не удалось создать заявку в Okdesk")
                return None
            
            issue_id = issue_data.get('id')
            
            # 3. Добавляем комментарий с результатами ML классификации
            if issue_id and classification_result.get('success'):
                category = classification_result.get('category', 'Неопределенная')
                confidence = classification_result.get('confidence', 0.0)
                
                # Формируем комментарий с классификацией
                ml_comment = self._format_classification_comment(
                    category, confidence, classification_result
                )
                
                comment_added = await self.okdesk_service.add_comment_to_issue(
                    issue_id, ml_comment, is_public=False  # Внутренний комментарий
                )
                
                if comment_added:
                    logger.info(f"ML классификация добавлена к заявке {issue_id}")
                else:
                    logger.warning(f"Не удалось добавить ML классификацию к заявке {issue_id}")
            
            # 4. Возвращаем полную информацию
            return {
                'issue': issue_data,
                'classification': classification_result,
                'ml_comment_added': comment_added if 'comment_added' in locals() else False
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании заявки с классификацией: {e}")
            return None
    
    def _format_classification_comment(self, category: str, confidence: float, 
                                     classification_result: Dict) -> str:
        """Форматирует комментарий с результатами ML классификации"""
        
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        comment = f"""🤖 Автоматическая классификация ML ({timestamp})

📋 Определенная категория: {category}
📊 Уверенность модели: {confidence:.1%}

ℹ️ Статус классификации: {'✅ Успешно' if classification_result.get('success') else '❌ Ошибка'}"""
        
        # Добавляем рекомендации если есть
        recommendations = classification_result.get('recommendations', [])
        if recommendations:
            comment += f"\n\n💡 Рекомендации:\n"
            for i, rec in enumerate(recommendations[:3], 1):  # Максимум 3 рекомендации
                comment += f"{i}. {rec}\n"
        
        # Добавляем техническую информацию
        comment += f"""
        
🔧 Техническая информация:
• Модель: LightGBM
• Версия классификатора: 1.0
• Количество классов: 118
• Время обработки: < 1 сек

---
Это автоматический комментарий системы ИИ классификации."""
        
        return comment

    async def add_comment_to_issue(self, issue_id: int, comment_text: str, is_public: bool = True, author_type: str = "employee") -> bool:
        """Добавляет комментарий к заявке
        
        Args:
            issue_id: ID заявки
            comment_text: Текст комментария
            is_public: Публичный комментарий или внутренний
            author_type: Тип автора (employee, contact)
            
        Returns:
            True если комментарий добавлен успешно
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}/comments"
            
            # Данные комментария
            comment_data = {
                'content': comment_text,
                'public': is_public,
                'author_type': author_type
            }
            
            params = {'api_token': self.api_key}
            headers = {'Content-Type': 'application/json'}
            
            async with self.session.post(url, json=comment_data, params=params, headers=headers) as response:
                if response.status in [200, 201]:
                    logger.info(f"Комментарий добавлен к заявке {issue_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка добавления комментария: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при добавлении комментария: {e}")
            return False

    async def update_issue_status(self, issue_id: int, status: str) -> bool:
        """Обновляет статус заявки
        
        Args:
            issue_id: ID заявки
            status: Новый статус (new, in_progress, waiting, resolved, closed)
            
        Returns:
            True если статус обновлен успешно
        """
        try:
            url = f"{self.base_url}/api/v1/issues/{issue_id}"
            
            # Данные для обновления
            update_data = {
                'status': status
            }
            
            params = {'api_token': self.api_key}
            headers = {'Content-Type': 'application/json'}
            
            async with self.session.patch(url, json=update_data, params=params, headers=headers) as response:
                if response.status in [200, 201]:
                    logger.info(f"Статус заявки {issue_id} обновлен на {status}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка обновления статуса: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса: {e}")
            return False

# Глобальные экземпляры для использования в боте
okdesk_service = None
issue_service = None

async def initialize_issue_service(api_key: str, company_id: str, base_url: str):
    """Инициализирует сервис заявок"""
    global okdesk_service, issue_service
    
    okdesk_service = OkdeskService(api_key, company_id, base_url)
    await okdesk_service.initialize()  # Инициализируем HTTP сессию
    issue_service = IssueService(okdesk_service)
    
    logger.info("Issue Service инициализирован")
    return issue_service

def get_okdesk_service():
    """Возвращает экземпляр OkdeskService"""
    return okdesk_service

def get_issue_service():
    """Возвращает экземпляр IssueService"""
    return issue_service
