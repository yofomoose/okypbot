"""
Система уведомлений администраторов о ML классификации
"""

import logging
from typing import List, Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

class AdminNotificationService:
    """Сервис уведомлений администраторов"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        
    async def notify_classification(self, 
                                  issue_id: int,
                                  title: str,
                                  description: str,
                                  predicted_category: str,
                                  confidence: float,
                                  classification_id: int,
                                  user_id: Optional[int] = None) -> bool:
        """
        Отправляет уведомление админам о новой классификации
        
        Args:
            issue_id: ID заявки в Okdesk
            title: Заголовок заявки
            description: Описание заявки
            predicted_category: Предсказанная категория
            confidence: Уверенность модели
            classification_id: ID записи классификации в БД
            user_id: ID пользователя, создавшего заявку
            
        Returns:
            True если уведомления отправлены успешно
        """
        
        if not ADMIN_IDS:
            logger.warning("Нет настроенных админов для уведомлений")
            return False
            
        # Определяем уровень уверенности
        confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
        confidence_text = "Высокая" if confidence > 0.8 else "Средняя" if confidence > 0.5 else "Низкая"
        
        # Формируем текст уведомления
        notification_text = (
            f"🤖 <b>Новая ML классификация</b>\n\n"
            f"🎫 <b>Заявка:</b> #{issue_id}\n"
            f"📝 <b>Заголовок:</b> {title}\n"
            f"📄 <b>Описание:</b> {description[:150]}{'...' if len(description) > 150 else ''}\n\n"
            f"🏷️ <b>Предсказанная категория:</b>\n{predicted_category}\n\n"
            f"{confidence_emoji} <b>Уверенность:</b> {confidence:.1%} ({confidence_text})\n"
        )
        
        if user_id:
            notification_text += f"👤 <b>Пользователь ID:</b> {user_id}\n"
            
        notification_text += f"\n❓ <b>Правильная ли классификация?</b>"
        
        # Создаем клавиатуру для подтверждения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Правильно", 
                    callback_data=f"admin_correct_{classification_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Неправильно", 
                    callback_data=f"admin_incorrect_{classification_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Открыть заявку в Okdesk", 
                    url=f"https://yapomogu55.okdesk.ru/issues/{issue_id}"
                )
            ]
        ])
        
        # Отправляем уведомления всем админам
        success_count = 0
        for admin_id in ADMIN_IDS:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                success_count += 1
                logger.info(f"Уведомление отправлено админу {admin_id}")
                
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")
        
        return success_count > 0
    
    async def notify_category_updated(self, 
                                    issue_id: int,
                                    old_category: str,
                                    new_category: str,
                                    admin_id: int) -> bool:
        """Уведомляет о смене категории заявки"""
        
        notification_text = (
            f"✅ <b>Категория заявки обновлена</b>\n\n"
            f"🎫 <b>Заявка:</b> #{issue_id}\n"
            f"📊 <b>Было:</b> {old_category}\n"
            f"🎯 <b>Стало:</b> {new_category}\n"
            f"👤 <b>Изменил админ:</b> {admin_id}\n\n"
            f"🧠 Модель будет обучена на этом примере"
        )
        
        # Уведомляем других админов
        for other_admin_id in ADMIN_IDS:
            if other_admin_id != admin_id:
                try:
                    await self.bot.send_message(
                        chat_id=other_admin_id,
                        text=notification_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления админа {other_admin_id}: {e}")
        
        return True

# Глобальный экземпляр сервиса
_admin_service: Optional[AdminNotificationService] = None

def get_admin_service() -> Optional[AdminNotificationService]:
    """Получить экземпляр сервиса админов"""
    return _admin_service

def set_admin_service(service: AdminNotificationService):
    """Установить экземпляр сервиса админов"""
    global _admin_service
    _admin_service = service
