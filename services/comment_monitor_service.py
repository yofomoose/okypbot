"""
Сервис мониторинга комментариев в Okdesk CRM
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)

class OkdeskCommentMonitor:
    """Мониторинг комментариев в заявках Okdesk"""
    
    def __init__(self, okdesk_service, bot, database_service):
        self.okdesk_service = okdesk_service
        self.bot = bot
        self.db = database_service
        self.is_running = False
        self.monitor_task = None
        self.check_interval = 30  # Проверка каждые 30 секунд
        self.last_check_time = datetime.now() - timedelta(minutes=5)
        
        # Кеш обработанных комментариев для избежания дубликатов
        self.processed_comments: Set[str] = set()
        
    async def start_monitoring(self):
        """Запускает мониторинг комментариев"""
        if self.is_running:
            logger.warning("Мониторинг комментариев уже запущен")
            return
            
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("🔄 Запущен мониторинг комментариев Okdesk")
        
    async def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Мониторинг комментариев остановлен")
        
    async def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.is_running:
            try:
                await self._check_new_comments()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга комментариев: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
                
    async def _check_new_comments(self):
        """Проверяет новые комментарии"""
        try:
            # Получаем активные заявки пользователей из БД
            active_issues = await self.db.get_active_user_issues()
            
            logger.info(f"🔍 Проверка комментариев: найдено {len(active_issues)} активных заявок")
            
            if not active_issues:
                logger.info("📝 Нет активных заявок для мониторинга")
                return
                
            for issue_data in active_issues:
                logger.info(f"📋 Проверяем заявку {issue_data['issue_id']} пользователя {issue_data['user_id']}")
                await self._check_issue_comments(
                    issue_data['issue_id'], 
                    issue_data['user_id']
                )
                
            # Обновляем время последней проверки
            self.last_check_time = datetime.now()
            logger.info(f"✅ Проверка комментариев завершена в {self.last_check_time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки комментариев: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        except Exception as e:
            logger.error(f"Ошибка проверки новых комментариев: {e}")
            
    async def _check_issue_comments(self, issue_id: int, user_id: int):
        """Проверяет комментарии конкретной заявки"""
        try:
            logger.info(f"📨 Проверяем комментарии заявки {issue_id}")
            
            # Получаем комментарии заявки из Okdesk
            comments = await self.okdesk_service.get_issue_comments(
                issue_id, 
                since=self.last_check_time
            )
            
            logger.info(f"📝 Получено {len(comments) if comments else 0} комментариев для заявки {issue_id}")
            
            if not comments:
                logger.info(f"📭 Нет новых комментариев для заявки {issue_id}")
                return
                
            # Фильтруем новые комментарии от поддержки
            logger.info(f"🔍 Анализируем {len(comments)} комментариев:")
            
            for i, comment in enumerate(comments, 1):
                author = comment.get('author', {})
                # Показываем все поля комментария для отладки
                logger.info(f"   📝 Комментарий {i}: ID={comment.get('id')}, "
                          f"автор={author.get('name', 'Неизвестно')}, "
                          f"публичный={comment.get('public', False)}, "
                          f"роли={author.get('roles', [])}, "
                          f"тип={author.get('type', 'Неизвестно')}")
                logger.info(f"      🕐 Поля времени: created_at='{comment.get('created_at')}', "
                          f"updated_at='{comment.get('updated_at')}', "
                          f"date='{comment.get('date')}', "
                          f"timestamp='{comment.get('timestamp')}'")
                if i <= 2:  # Показываем полную структуру только для первых 2 комментариев
                    logger.info(f"      📋 Полная структура: {comment}")
            
            new_support_comments = [
                comment for comment in comments
                if self._is_support_comment(comment) and 
                   self._is_new_comment(comment)
            ]
            
            logger.info(f"💬 Найдено {len(new_support_comments)} новых комментариев от поддержки")
            
            # Отправляем уведомления пользователю
            for comment in new_support_comments:
                logger.info(f"📤 Отправляем уведомление пользователю {user_id} о комментарии {comment.get('id')}")
                await self._notify_user_about_comment(
                    user_id, issue_id, comment
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки комментариев заявки {issue_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
    def _is_support_comment(self, comment: Dict) -> bool:
        """Определяет, является ли комментарий от поддержки"""
        # Упрощенная логика: комментарий от поддержки если:
        # 1. Он публичный
        # 2. Автор имеет тип 'employee' (сотрудник)
        
        author = comment.get('author', {})
        is_public = comment.get('public', False)
        author_type = author.get('type', '').lower()
        author_name = author.get('name', '')
        
        # Комментарий от поддержки если он публичный и от сотрудника
        is_employee = author_type == 'employee'
        
        result = is_public and is_employee
        
        logger.info(f"🔍 Проверка комментария {comment.get('id')}: "
                   f"автор='{author_name}', публичный={is_public}, тип={author_type}, "
                   f"от_поддержки={result}")
        
        return result
        
    def _is_new_comment(self, comment: Dict) -> bool:
        """Проверяет, является ли комментарий новым"""
        comment_id = str(comment.get('id', ''))
        created_at_str = comment.get('created_at', '')
        
        # Проверяем, не обрабатывали ли уже этот комментарий
        if comment_id in self.processed_comments:
            logger.info(f"⚠️ Комментарий {comment_id} уже был обработан")
            return False
        
        # ВРЕМЕННО: упрощаем логику времени - считаем новыми все необработанные комментарии
        # TODO: Исправить после выяснения формата времени в API
        if not created_at_str:
            logger.warning(f"⏰ Нет данных о времени для комментария {comment_id}, считаем новым")
            # Добавляем в кеш обработанных
            self.processed_comments.add(comment_id)
            return True
            
        # Проверяем время создания (если есть)
        try:
            # Пробуем разные форматы времени
            for time_field in ['created_at', 'updated_at', 'date', 'timestamp']:
                time_str = comment.get(time_field, '')
                if time_str:
                    logger.info(f"🕐 Используем поле {time_field}: {time_str}")
                    created_at = datetime.fromisoformat(
                        time_str.replace('Z', '+00:00')
                    )
                    if created_at <= self.last_check_time:
                        logger.info(f"📅 Комментарий {comment_id} старый: {created_at} <= {self.last_check_time}")
                        return False
                    break
            else:
                logger.warning(f"⚠️ Не найдено ни одного поля времени для комментария {comment_id}")
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"❌ Не удалось разобрать время комментария {comment_id}: {e}")
            
        # Добавляем в кеш обработанных
        self.processed_comments.add(comment_id)
        
        # Ограничиваем размер кеша
        if len(self.processed_comments) > 10000:
            # Очищаем половину старых записей
            old_comments = list(self.processed_comments)[:5000]
            for old_id in old_comments:
                self.processed_comments.discard(old_id)
                
        logger.info(f"✅ Комментарий {comment_id} считается новым")
        return True
        
    async def _notify_user_about_comment(self, user_id: int, issue_id: int, comment: Dict):
        """Отправляет уведомление пользователю о новом комментарии"""
        try:
            author = comment.get('author', {})
            author_name = author.get('name', 'Сотрудник поддержки')
            comment_text = comment.get('content', 'Без текста')
            created_at = comment.get('created_at', '')
            
            # Очищаем HTML теги из текста комментария
            import re
            comment_text = re.sub(r'<[^>]+>', '', comment_text)  # Удаляем все HTML теги
            comment_text = comment_text.replace('&nbsp;', ' ')  # Заменяем HTML пробелы
            comment_text = comment_text.replace('&lt;', '<')
            comment_text = comment_text.replace('&gt;', '>')
            comment_text = comment_text.replace('&amp;', '&')
            comment_text = comment_text.strip()  # Убираем лишние пробелы
            
            # Форматируем время
            time_str = "недавно"
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M")
                except ValueError:
                    pass
            
            # Обрезаем длинный комментарий
            if len(comment_text) > 300:
                comment_text = comment_text[:297] + "..."
                
            message = (
                f"💬 <b>Новый комментарий к заявке #{issue_id}</b>\n\n"
                f"👤 <b>От:</b> {author_name}\n"
                f"🕐 <b>Время:</b> {time_str}\n\n"
                f"💭 <b>Сообщение:</b>\n<i>{comment_text}</i>\n\n"
                f"Вы можете ответить, отправив сообщение в этот чат."
            )
            
            # Создаем клавиатуру для быстрых действий
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Ответить", 
                        callback_data=f"reply_to_issue_{issue_id}"
                    ),
                    InlineKeyboardButton(
                        text="📋 Детали заявки", 
                        callback_data=f"issue_details_{issue_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Закрыть заявку", 
                        callback_data=f"close_issue_{issue_id}"
                    )
                ]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            logger.info(f"Отправлено уведомление пользователю {user_id} о комментарии к заявке {issue_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о комментарии: {e}")
            
    async def add_issue_for_monitoring(self, issue_id: int, user_id: int):
        """Добавляет заявку в мониторинг"""
        try:
            await self.db.add_user_issue_for_monitoring(issue_id, user_id)
            logger.info(f"Заявка {issue_id} добавлена в мониторинг для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка добавления заявки в мониторинг: {e}")
            
    async def remove_issue_from_monitoring(self, issue_id: int):
        """Удаляет заявку из мониторинга"""
        try:
            await self.db.remove_user_issue_from_monitoring(issue_id)
            logger.info(f"Заявка {issue_id} удалена из мониторинга")
        except Exception as e:
            logger.error(f"Ошибка удаления заявки из мониторинга: {e}")


# Глобальный экземпляр мониторинга
comment_monitor = None

def get_comment_monitor():
    """Получает экземпляр мониторинга комментариев"""
    return comment_monitor

def initialize_comment_monitor(okdesk_service, bot, database_service):
    """Инициализирует мониторинг комментариев"""
    global comment_monitor
    comment_monitor = OkdeskCommentMonitor(okdesk_service, bot, database_service)
    return comment_monitor
