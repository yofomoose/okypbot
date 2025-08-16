"""
Система мониторинга изменений статусов заявок в Okdesk
"""
import asyncio
import logging
from typing import Dict, Set, Optional
from aiogram import Bot
from database.models import db, User
from api.okdesk_api import OkdeskAPI

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра мониторинга
_monitor_instance: Optional['IssueStatusMonitor'] = None

def get_monitor() -> Optional['IssueStatusMonitor']:
    """Получить экземпляр мониторинга"""
    return _monitor_instance

def set_monitor(monitor: 'IssueStatusMonitor'):
    """Установить экземпляр мониторинга"""
    global _monitor_instance
    _monitor_instance = monitor

class IssueStatusMonitor:
    """Монитор статусов заявок"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.tracked_issues: Dict[int, Dict] = {}  # issue_id -> {user_id, last_status}
        self.running = False
        
    async def start_monitoring(self):
        """Запуск мониторинга"""
        self.running = True
        logger.info("Запуск мониторинга статусов заявок")
        
        while self.running:
            try:
                await self.check_status_changes()
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Ошибка в мониторинге: {e}")
                await asyncio.sleep(30)  # Короткая пауза при ошибке
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("Остановка мониторинга статусов заявок")
    
    def add_issue_to_tracking(self, issue_id: int, user_id: int, initial_status: str = None):
        """Добавить заявку в отслеживание"""
        self.tracked_issues[issue_id] = {
            'user_id': user_id,
            'last_status': initial_status or 'Новая'
        }
        logger.info(f"Добавлена заявка {issue_id} в отслеживание для пользователя {user_id}")
    
    def remove_issue_from_tracking(self, issue_id: int):
        """Удалить заявку из отслеживания"""
        if issue_id in self.tracked_issues:
            del self.tracked_issues[issue_id]
            logger.info(f"Заявка {issue_id} удалена из отслеживания")
    
    async def check_status_changes(self):
        """Проверка изменений статусов"""
        if not self.tracked_issues:
            return
            
        okdesk = OkdeskAPI()
        
        try:
            # Загружаем все отслеживаемые заявки из базы
            await self.load_tracked_issues_from_db()
            
            for issue_id, tracking_data in list(self.tracked_issues.items()):
                try:
                    # Получаем актуальную информацию о заявке
                    issue = await okdesk.get_issue(issue_id)
                    
                    if not issue:
                        continue
                    
                    # Извлекаем текущий статус
                    current_status = self.extract_status_name(issue.get('status'))
                    last_status = tracking_data['last_status']
                    
                    # Если статус изменился
                    if current_status != last_status:
                        await self.notify_status_change(
                            issue_id=issue_id,
                            user_id=tracking_data['user_id'],
                            old_status=last_status,
                            new_status=current_status,
                            issue_data=issue
                        )
                        
                        # Обновляем последний статус
                        self.tracked_issues[issue_id]['last_status'] = current_status
                        
                except Exception as e:
                    logger.error(f"Ошибка при проверке заявки {issue_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка при проверке статусов: {e}")
        finally:
            await okdesk.close()
    
    async def load_tracked_issues_from_db(self):
        """Загрузка отслеживаемых заявок из базы данных"""
        for user_id, user in db.users.items():
            if user.okdesk_issue_id and user.okdesk_issue_id not in self.tracked_issues:
                self.add_issue_to_tracking(
                    issue_id=user.okdesk_issue_id,
                    user_id=user_id
                )
    
    def extract_status_name(self, status_data):
        """Извлечение названия статуса из данных API"""
        if isinstance(status_data, dict):
            return status_data.get('name', 'Неизвестный статус')
        elif isinstance(status_data, str):
            return status_data
        else:
            return 'Неизвестный статус'
    
    async def notify_status_change(self, issue_id: int, user_id: int, old_status: str, 
                                 new_status: str, issue_data: Dict):
        """Уведомление пользователя об изменении статуса"""
        try:
            # Определяем эмодзи для статуса
            status_emoji = self.get_status_emoji(new_status)
            
            # Формируем сообщение
            message = (
                f"{status_emoji} **Статус заявки изменен**\n\n"
                f"📋 Заявка: #{issue_id}\n"
                f"📝 Название: {issue_data.get('title', 'Без названия')}\n"
                f"📊 Статус: {old_status} → **{new_status}**\n"
            )
            
            # Добавляем дополнительную информацию в зависимости от статуса
            if new_status.lower() in ['выполнена', 'закрыта', 'решена']:
                message += "\n✅ Ваша заявка была выполнена!"
            elif new_status.lower() in ['в работе', 'назначена']:
                message += "\n🔄 Ваша заявка взята в работу!"
            elif new_status.lower() in ['отклонена', 'отменена']:
                message += "\n❌ Ваша заявка была отклонена."
            
            # Отправляем уведомление
            await self.bot.send_message(
                chat_id=user_id,
                text=message
            )
            
            logger.info(f"Отправлено уведомление пользователю {user_id} о статусе заявки {issue_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
    
    def get_status_emoji(self, status: str) -> str:
        """Получение эмодзи для статуса"""
        status_lower = status.lower()
        
        if status_lower in ['новая', 'создана']:
            return '🆕'
        elif status_lower in ['в работе', 'назначена']:
            return '🔄'
        elif status_lower in ['выполнена', 'закрыта', 'решена']:
            return '✅'
        elif status_lower in ['отклонена', 'отменена']:
            return '❌'
        elif status_lower in ['ожидает', 'пауза']:
            return '⏸️'
        else:
            return '📋'

# Глобальный экземпляр монитора
monitor: IssueStatusMonitor = None

def init_monitor(bot: Bot) -> IssueStatusMonitor:
    """Инициализация монитора"""
    global monitor
    monitor = IssueStatusMonitor(bot)
    return monitor

def get_monitor() -> IssueStatusMonitor:
    """Получение экземпляра монитора"""
    return monitor
