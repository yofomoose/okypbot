"""
Webhook сервер для получения уведомлений от okdesk
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import asyncio
import json
import logging
import hashlib
import hmac
import os
from typing import Dict, Any, Optional
from aiogram import Bot
from config import BOT_TOKEN, OKDESK_WEBHOOK_SECRET, OKDESK_API_TOKEN, OKDESK_BASE_URL
from database.models import db
from api.okdesk_api import OkdeskAPI
# Удален импорт отсутствующего модуля: from services.security import IPSecurityMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(title="Okdesk Webhook Handler")
bot = Bot(token=BOT_TOKEN)

# Проверка IP отключена
# allowed_ips = [ip.strip() for ip in os.environ.get('ALLOWED_WEBHOOK_IPS', '').split(',') if ip.strip()]
# ip_security = IPSecurityMiddleware(allowed_ips)

class WebhookHandler:
    """Обработчик webhook событий от okdesk"""
    
    def __init__(self):
        self.bot = bot
        # OkdeskAPI использует переменные окружения, поэтому не передаем параметры
        self.okdesk_api = OkdeskAPI()
    
    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Проверка подписи webhook для безопасности"""
        if not OKDESK_WEBHOOK_SECRET:
            return True  # Если секрет не настроен, пропускаем проверку
        
        expected_signature = hmac.new(
            OKDESK_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def handle_comment_added(self, data: Dict[Any, Any]):
        """Обработка нового комментария"""
        try:
            # Структура согласно документации Okdesk
            event = data.get('event', {})
            issue = data.get('issue', {})
            
            # Получаем информацию о комментарии
            comment = event.get('comment', {})
            author = event.get('author', {})
            
            issue_id = issue.get('id')
            comment_text = comment.get('content', '')
            comment_id = comment.get('id')
            is_public = comment.get('is_public', True)
            
            # Информация об авторе
            author_type = author.get('type')  # 'employee' или 'contact'
            author_first_name = author.get('first_name', '')
            author_last_name = author.get('last_name', '')
            author_name = f"{author_first_name} {author_last_name}".strip()
            if not author_name:
                author_name = 'Неизвестный'
            
            logger.info(f"Новый комментарий в заявке {issue_id} от {author_type}: {author_name}")
            
            # Определяем направление сообщения
            if author_type == 'employee':
                # Сообщение от специалиста → отправляем клиенту
                await self.notify_client_about_specialist_message(
                    issue_id, comment_text, author_name, is_public
                )
            elif author_type == 'contact':
                # Сообщение от клиента → отправляем специалисту
                await self.notify_specialist_about_client_message(
                    issue_id, comment_text, author_name
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки комментария: {e}")
    
    async def notify_client_about_specialist_message(
        self, issue_id: int, message: str, specialist_name: str, is_public: bool
    ):
        """Уведомление клиента о сообщении от специалиста"""
        try:
            # Находим клиента по issue_id
            client_telegram_id = await self.get_client_telegram_id(issue_id)
            
            if not client_telegram_id:
                logger.warning(f"Клиент не найден для заявки {issue_id}")
                return
            
            # Формируем сообщение
            visibility_text = "🔒 Внутреннее" if not is_public else "📢 Публичное"
            text = (
                f"💬 **Новое сообщение по заявке #{issue_id}**\n\n"
                f"👨‍💼 **{specialist_name}:** {message}\n\n"
                f"{visibility_text} сообщение\n\n"
                f"💡 *Нажмите \"Ответить\" для отправки ответа*"
            )
            
            # Создаем клавиатуру
            from keyboards.main import get_issue_reply_keyboard
            keyboard = get_issue_reply_keyboard(issue_id)
            
            # Отправляем уведомление
            await self.bot.send_message(
                chat_id=client_telegram_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            logger.info(f"Уведомление отправлено клиенту {client_telegram_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления клиенту: {e}")
    
    async def notify_specialist_about_client_message(
        self, issue_id: int, message: str, client_name: str
    ):
        """Уведомление специалиста о сообщении от клиента"""
        try:
            # Находим специалиста по issue_id
            specialist_telegram_id = await self.get_specialist_telegram_id(issue_id)
            
            if not specialist_telegram_id:
                logger.warning(f"Специалист не найден для заявки {issue_id}")
                return
            
            # Формируем сообщение
            text = (
                f"📢 **Новое сообщение от клиента**\n\n"
                f"📋 **Заявка:** #{issue_id}\n"
                f"👤 **{client_name}:** {message}\n\n"
                f"💡 *Ответьте через okdesk или нажмите \"Ответить\" здесь*"
            )
            
            # Создаем клавиатуру для специалиста
            from keyboards.specialist import get_specialist_reply_keyboard
            keyboard = get_specialist_reply_keyboard(issue_id)
            
            # Отправляем уведомление
            await self.bot.send_message(
                chat_id=specialist_telegram_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            logger.info(f"Уведомление отправлено специалисту {specialist_telegram_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления специалисту: {e}")
    
    async def handle_status_changed(self, data: Dict[Any, Any]):
        """Обработка изменения статуса заявки"""
        try:
            # Структура согласно документации Okdesk
            event = data.get('event', {})
            issue = data.get('issue', {})
            
            issue_id = issue.get('id')
            
            # Получаем информацию о старом и новом статусе
            old_status = event.get('old_status', {})
            new_status = event.get('new_status', {})
            
            old_status_name = old_status.get('code', old_status.get('name', 'Неизвестно'))
            new_status_name = new_status.get('code', new_status.get('name', 'Неизвестно'))
            
            logger.info(f"Статус заявки {issue_id}: {old_status_name} → {new_status_name}")
            
            # Уведомляем клиента об изменении статуса
            await self.notify_status_change(issue_id, old_status_name, new_status_name)
            
        except Exception as e:
            logger.error(f"Ошибка обработки изменения статуса: {e}")
    
    async def notify_status_change(self, issue_id: int, old_status: str, new_status: str):
        """Уведомление об изменении статуса"""
        try:
            client_telegram_id = await self.get_client_telegram_id(issue_id)
            
            if not client_telegram_id:
                logger.warning(f"Клиент не найден для заявки {issue_id}")
                return
            
            # Определяем эмодзи для статуса
            status_emoji = {
                'новая': '🆕',
                'в работе': '⚙️',
                'ожидание': '⏳',
                'решена': '✅',
                'закрыта': '🔒'
            }
            
            emoji = status_emoji.get(new_status.lower(), '📋')
            
            text = (
                f"{emoji} **Статус заявки #{issue_id} изменен**\n\n"
                f"📊 **Было:** {old_status}\n"
                f"📊 **Стало:** {new_status}\n\n"
                f"💡 *Если у вас есть вопросы, нажмите \"Ответить\"*"
            )
            
            from keyboards.main import get_issue_reply_keyboard
            keyboard = get_issue_reply_keyboard(issue_id)
            
            await self.bot.send_message(
                chat_id=client_telegram_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            logger.info(f"Уведомление о статусе отправлено клиенту {client_telegram_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о статусе: {e}")
    
    async def handle_issue_assigned(self, data: Dict[Any, Any]):
        """Обработка назначения заявки"""
        try:
            # Структура согласно документации Okdesk
            event = data.get('event', {})
            issue = data.get('issue', {})
            
            issue_id = issue.get('id')
            
            # Получаем информацию о новом ответственном
            new_assignee = event.get('new_assignee', {})
            assignee_name = f"{new_assignee.get('first_name', '')} {new_assignee.get('last_name', '')}".strip()
            
            if not assignee_name:
                assignee_name = 'Неизвестный специалист'
            
            logger.info(f"Заявка {issue_id} назначена специалисту: {assignee_name}")
            
            # Уведомляем клиента о назначении
            await self.notify_assignment(issue_id, assignee_name)
            
        except Exception as e:
            logger.error(f"Ошибка обработки назначения: {e}")
    
    async def notify_assignment(self, issue_id: int, assignee_name: str):
        """Уведомление о назначении специалиста"""
        try:
            client_telegram_id = await self.get_client_telegram_id(issue_id)
            
            if not client_telegram_id:
                logger.warning(f"Клиент не найден для заявки {issue_id}")
                return
            
            text = (
                f"👨‍💼 **Заявка #{issue_id} назначена специалисту**\n\n"
                f"🎯 **Исполнитель:** {assignee_name}\n\n"
                f"💡 *Специалист скоро свяжется с вами для решения вопроса*"
            )
            
            from keyboards.main import get_issue_reply_keyboard
            keyboard = get_issue_reply_keyboard(issue_id)
            
            await self.bot.send_message(
                chat_id=client_telegram_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            logger.info(f"Уведомление о назначении отправлено клиенту {client_telegram_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о назначении: {e}")
    
    async def get_client_telegram_id(self, issue_id: int) -> Optional[int]:
        """Получить Telegram ID клиента по ID заявки"""
        try:
            logger.info(f"Поиск клиента для заявки {issue_id}")
            
            # Ищем пользователя, связанного с данной заявкой
            # 1. Проверяем в записях UserIssue (связь заявок с пользователями)
            active_issues = await db.get_active_user_issues()
            for issue_record in active_issues:
                if issue_record['issue_id'] == issue_id:
                    user_id = issue_record['user_id']
                    logger.info(f"Найден пользователь {user_id} для заявки {issue_id} в активных заявках")
                    return user_id
            
            # 2. Проверяем все зарегистрированные заявки в профилях пользователей
            for telegram_id, user in db.users.items():
                if user.okdesk_issue_id == issue_id:
                    logger.info(f"Найден пользователь {telegram_id} для заявки {issue_id} в профилях")
                    return telegram_id
            
            # Если не нашли, запрашиваем данные из Okdesk API
            try:
                issue_data = await self.okdesk_api.get_issue(issue_id)
                if issue_data:
                    # Ищем контакт в данных заявки
                    contact_id = None
                    contacts_data = issue_data.get('contacts', [])
                    if contacts_data:
                        contact_id = contacts_data[0].get('id')
                    
                    if contact_id:
                        # Ищем пользователя с таким okdesk_contact_id
                        for telegram_id, user in db.users.items():
                            if user.okdesk_contact_id == contact_id:
                                logger.info(f"Найден пользователь {telegram_id} по contact_id {contact_id}")
                                
                                # Сохраняем связь для будущих запросов
                                await db.add_user_issue_for_monitoring(issue_id, telegram_id)
                                
                                return telegram_id
            except Exception as api_error:
                logger.error(f"Ошибка при запросе данных из Okdesk API: {api_error}")
            
            logger.warning(f"Клиент не найден для заявки {issue_id}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения telegram_id клиента: {e}")
            return None
    
    async def get_specialist_telegram_id(self, issue_id: int) -> Optional[int]:
        """Получить Telegram ID специалиста по ID заявки"""
        try:
            logger.info(f"Поиск специалиста для заявки {issue_id}")
            
            # Получаем информацию о заявке из Okdesk API
            try:
                issue_data = await self.okdesk_api.get_issue(issue_id)
                if issue_data:
                    # Получаем ID ответственного
                    assignee = issue_data.get('assignee', {})
                    assignee_id = assignee.get('id')
                    
                    if assignee_id:
                        # Используем систему сопоставления сотрудников
                        from services.employee_mapping import EmployeeMappingService
                        
                        # Создаем экземпляр сервиса маппинга
                        mapping_service = EmployeeMappingService()
                        
                        # Ищем Telegram ID специалиста по его ID в OkDesk
                        telegram_id = mapping_service.get_telegram_id(str(assignee_id))
                        
                        if telegram_id:
                            logger.info(f"Найден Telegram ID {telegram_id} для сотрудника OkDesk {assignee_id}")
                            return telegram_id
                        
                        # Если сопоставление не найдено, используем ID по умолчанию
                        from config import ADMIN_IDS
                        
                        if ADMIN_IDS:
                            try:
                                admin_id = int(ADMIN_IDS.split(',')[0])
                                logger.info(f"Сопоставление не найдено, используем админа {admin_id}")
                                return admin_id
                            except (ValueError, IndexError):
                                logger.error("Не удалось получить ID администратора")
            except Exception as api_error:
                logger.error(f"Ошибка при запросе данных из Okdesk API: {api_error}")
            
            logger.warning(f"Специалист не найден для заявки {issue_id}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения telegram_id специалиста: {e}")
            return None

# Создаем глобальный экземпляр обработчика
webhook_handler = WebhookHandler()

# Проверка IP отключена
# async def check_ip_security(request: Request):
#     """Зависимость для проверки IP-адреса"""
#     if not await ip_security.check_ip(request):
#         raise HTTPException(status_code=403, detail="Access denied: IP not allowed")
#     return True

@app.post("/okdesk-webhook")
async def handle_okdesk_webhook(request: Request):
    """Основной эндпоинт для получения webhooks от okdesk"""
    try:
        # Получаем тело запроса
        body = await request.body()
        
        # Примечание: Согласно документации OkDesk, вебхуки не используют подпись и не требуют проверки IP
        
        # Парсим JSON
        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Получаем тип события согласно документации Okdesk
        event = data.get('event', {})
        event_type = event.get('event_type')
        
        logger.info(f"Получен webhook: {event_type}")
        
        # Обрабатываем событие согласно официальной документации
        if event_type == 'new_comment':
            await webhook_handler.handle_comment_added(data)
        elif event_type == 'status_changed':
            await webhook_handler.handle_status_changed(data)
        elif event_type == 'assignee_changed':
            await webhook_handler.handle_issue_assigned(data)
        elif event_type == 'new_issue':
            # Можно добавить обработку создания новой заявки
            logger.info(f"Создана новая заявка: {data.get('issue', {}).get('id')}")
        else:
            logger.info(f"Неизвестный тип события: {event_type}")
        
        return JSONResponse({"status": "ok"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "healthy", "service": "okdesk-webhook-handler"}

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "Okdesk Webhook Handler is running"}
