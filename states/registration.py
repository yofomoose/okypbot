"""
Состояния для FSM (Finite State Machine)
"""
from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации"""
    waiting_for_user_type = State()
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_position = State()
    waiting_for_company_inn = State()

class IssueStates(StatesGroup):
    """Состояния для работы с заявками"""
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_company_search = State()
    waiting_for_contact_search = State()

class SearchStates(StatesGroup):
    """Состояния для поиска"""
    waiting_for_search_query = State()
    waiting_for_company_query = State()
    waiting_for_contact_query = State()
    waiting_for_issue_query = State()
