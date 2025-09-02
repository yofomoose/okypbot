"""
Модуль для регистрации всех обработчиков в main.py
"""

from handlers.admin_handlers import router as admin_router
from handlers.registration import router as registration_router
from handlers.issue_handlers import router as issue_router
from handlers.feedback_handlers import router as feedback_router
from handlers.comment_handlers import router as comment_router
from handlers.bot_model_handlers import router as bot_model_router
from handlers.ml_handlers import router as ml_router
from handlers.webhook_handlers import router as webhook_router
from handlers.admin_stats import router as admin_stats_router
from handlers.employee_mapping_handlers import router as employee_mapping_router

routers = [
    admin_router,
    registration_router,
    issue_router,
    feedback_router,
    comment_router,
    bot_model_router,
    ml_router,
    webhook_router,
    admin_stats_router,
    employee_mapping_router
]

def setup_routers(dp):
    """Регистрация всех обработчиков в диспетчере"""
    for router in routers:
        dp.include_router(router)

__all__ = ['setup_routers']