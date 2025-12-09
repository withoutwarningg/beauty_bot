"""
Конфигурация pytest для тестирования Beauty City Bot
Содержит фикстуры для моделей БД, заглушки Telegram API и вспомогательные объекты
"""

import sys
import types
import datetime as dt
import pytest

# ============================================================================
# ЗАГЛУШКИ ДЛЯ TELEGRAM API (Mock для python-telegram-bot)
# ============================================================================

if 'telegram' not in sys.modules:
    telegram = types.ModuleType("telegram")


    class InlineKeyboardButton:
        """Заглушка для telegram.InlineKeyboardButton"""

        def __init__(self, text, callback_data=None, url=None):
            self.text = text
            self.callback_data = callback_data
            self.url = url

        def __repr__(self):
            return f"InlineKeyboardButton(text='{self.text}', callback_data='{self.callback_data}')"


    class InlineKeyboardMarkup:
        """Заглушка для telegram.InlineKeyboardMarkup"""

        def __init__(self, inline_keyboard):
            # inline_keyboard: list[list[InlineKeyboardButton]]
            self.inline_keyboard = inline_keyboard

        def __repr__(self):
            return f"InlineKeyboardMarkup({len(self.inline_keyboard)} rows)"


    class ReplyKeyboardMarkup:
        """Заглушка для telegram.ReplyKeyboardMarkup"""

        def __init__(self, keyboard, resize_keyboard=True, one_time_keyboard=False):
            self.keyboard = keyboard
            self.resize_keyboard = resize_keyboard
            self.one_time_keyboard = one_time_keyboard


    class KeyboardButton:
        """Заглушка для telegram.KeyboardButton"""

        def __init__(self, text, request_contact=False, request_location=False):
            self.text = text
            self.request_contact = request_contact
            self.request_location = request_location


    class ParseMode:
        """Константы режимов парсинга"""
        MARKDOWN = 'Markdown'
        MARKDOWN_V2 = 'MarkdownV2'
        HTML = 'HTML'


    # Регистрируем все классы в модуле
    telegram.InlineKeyboardButton = InlineKeyboardButton
    telegram.InlineKeyboardMarkup = InlineKeyboardMarkup
    telegram.ReplyKeyboardMarkup = ReplyKeyboardMarkup
    telegram.KeyboardButton = KeyboardButton
    telegram.ParseMode = ParseMode

    sys.modules['telegram'] = telegram


# ============================================================================
# ЗАГЛУШКИ ДЛЯ TELEGRAM BOT OBJECTS
# ============================================================================

class DummyBot:
    """
    Заглушка для telegram.Bot
    Сохраняет все отправленные сообщения в список self.sent для проверки в тестах
    """

    def __init__(self):
        self.sent = []
        self.edited = []
        self.deleted = []

    def send_message(self, chat_id, text, reply_markup=None, parse_mode=None, disable_web_page_preview=None):
        """Имитация отправки сообщения"""
        message = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup': reply_markup,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_web_page_preview
        }
        self.sent.append(message)
        return DummySentMessage(chat_id=chat_id, text=text, message_id=len(self.sent))

    def edit_message_text(self, text, chat_id=None, message_id=None, reply_markup=None):
        """Имитация редактирования сообщения"""
        self.edited.append({
            'text': text,
            'chat_id': chat_id,
            'message_id': message_id,
            'reply_markup': reply_markup
        })
        return True

    def delete_message(self, chat_id, message_id):
        """Имитация удаления сообщения"""
        self.deleted.append({'chat_id': chat_id, 'message_id': message_id})
        return True

    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        """Имитация ответа на callback query"""
        return True


class DummySentMessage:
    """Заглушка для отправленного сообщения"""

    def __init__(self, chat_id, text, message_id):
        self.chat_id = chat_id
        self.text = text
        self.message_id = message_id
        self.chat = DummyChat(chat_id)


class DummyChat:
    """Заглушка для telegram.Chat"""

    def __init__(self, chat_id, first_name="TestUser", last_name=None, username=None):
        self.id = chat_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.type = "private"


class DummyUser:
    """Заглушка для telegram.User"""

    def __init__(self, user_id, first_name="TestUser", last_name=None, username=None, is_bot=False):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = is_bot


class DummyMessage:
    """Заглушка для telegram.Message"""

    def __init__(self, text, chat_id, message_id=1, first_name="TestUser", user_id=None):
        self.text = text
        self.chat_id = chat_id
        self.message_id = message_id
        self.chat = DummyChat(chat_id, first_name=first_name)
        self.from_user = DummyUser(user_id or chat_id, first_name=first_name)
        self.date = dt.datetime.now()

    def reply_text(self, text, reply_markup=None, parse_mode=None):
        """Имитация ответа на сообщение"""
        return DummySentMessage(self.chat_id, text, self.message_id + 1)


class DummyCallbackQuery:
    """Заглушка для telegram.CallbackQuery"""

    def __init__(self, data, chat_id=1, message_id=1, user_id=None):
        self.data = data
        self.id = f"cbq_{chat_id}_{message_id}"
        self.from_user = DummyUser(user_id or chat_id)
        self.message = DummyMessage(
            text="Previous message",
            chat_id=chat_id,
            message_id=message_id
        )
        self.chat_instance = f"instance_{chat_id}"
        self.answered = False

    def answer(self, text=None, show_alert=False):
        """Имитация ответа на callback query"""
        self.answered = True
        return True

    def edit_message_text(self, text, reply_markup=None, parse_mode=None):
        """Имитация редактирования сообщения через callback"""
        self.message.text = text
        return True


class DummyUpdate:
    """Заглушка для telegram.Update"""

    def __init__(self, cq=None, message=None):
        self.callback_query = cq
        self.message = message

        # Определяем effective_chat
        if cq:
            self.effective_chat = cq.message.chat
            self.effective_user = cq.from_user
        elif message:
            self.effective_chat = message.chat
            self.effective_user = message.from_user
        else:
            self.effective_chat = DummyChat(1)
            self.effective_user = DummyUser(1)

        self.update_id = 12345


class DummyContext:
    """Заглушка для telegram.ext.CallbackContext"""

    def __init__(self, bot=None):
        self.bot = bot or DummyBot()
        self.user_data = {}
        self.chat_data = {}
        self.bot_data = {}
        self.args = []
        self.error = None


# ============================================================================
# PYTEST FIXTURES: СЛУЖЕБНЫЕ
# ============================================================================

@pytest.fixture
def dummy_bot():
    """Возвращает заглушку для telegram.Bot"""
    return DummyBot()


@pytest.fixture
def dummy_context(dummy_bot):
    """Возвращает заглушку для CallbackContext с ботом"""
    return DummyContext(bot=dummy_bot)


@pytest.fixture
def dummy_update_message():
    """Возвращает заглушку для Update с текстовым сообщением"""
    message = DummyMessage(text="Test message", chat_id=12345)
    return DummyUpdate(message=message)


@pytest.fixture
def dummy_update_callback():
    """Возвращает заглушку для Update с callback query"""
    callback = DummyCallbackQuery(data="test_callback", chat_id=12345)
    return DummyUpdate(cq=callback)


# ============================================================================
# PYTEST FIXTURES: МОДЕЛИ БД
# ============================================================================

pytestmark = pytest.mark.django_db


@pytest.fixture
def Models():
    """
    Возвращает словарь со всеми моделями приложения
    Удобно для динамического доступа к моделям в тестах
    """
    from bot.models import Salon, Specialist, Procedure, Client, Booking, Appointment
    return {
        'Salon': Salon,
        'Specialist': Specialist,
        'Procedure': Procedure,
        'Client': Client,
        'Booking': Booking,
        'Appointment': Appointment
    }


# ============================================================================
# PYTEST FIXTURES: БАЗОВЫЕ ОБЪЕКТЫ БД
# ============================================================================

@pytest.fixture
def salon(Models):
    """Создает тестовый салон 'Beauty Salon A'"""
    Salon = Models["Salon"]
    return Salon.objects.create(
        name="Beauty Salon A",
        address="ул. Ленина, 10",
        phone="+7 999 000-00-00",
        email="salon.a@example.com",
        opening_time=dt.time(10, 0),
        closing_time=dt.time(19, 0),
    )


@pytest.fixture
def salon_b(Models):
    """Создает второй тестовый салон 'Beauty Salon B'"""
    Salon = Models["Salon"]
    return Salon.objects.create(
        name="Beauty Salon B",
        address="ул. Кирова, 25",
        phone="+7 999 111-11-11",
        email="salon.b@example.com",
        opening_time=dt.time(9, 0),
        closing_time=dt.time(20, 0),
    )


@pytest.fixture
def salon_c(Models):
    """Создает третий тестовый салон 'Beauty Salon C'"""
    Salon = Models["Salon"]
    return Salon.objects.create(
        name="Beauty Salon C",
        address="пр. Победы, 100",
        phone="+7 999 222-22-22",
        email="salon.c@example.com",
        opening_time=dt.time(10, 0),
        closing_time=dt.time(18, 0),
    )


@pytest.fixture
def specialist(Models):
    """Создает тестового мастера (парикмахер)"""
    Specialist = Models["Specialist"]
    return Specialist.objects.create(
        name="Иван Иванов",
        specialization="Парикмахер",
        phone="+7 911 000-00-00",
        email="ivan@example.com"
    )


@pytest.fixture
def specialist2(Models):
    """Создает второго тестового мастера (мастер маникюра)"""
    Specialist = Models["Specialist"]
    return Specialist.objects.create(
        name="Мария Петрова",
        specialization="Мастер маникюра",
        phone="+7 911 111-11-11",
        email="maria@example.com"
    )


@pytest.fixture
def specialist3(Models):
    """Создает третьего тестового мастера (стилист)"""
    Specialist = Models["Specialist"]
    return Specialist.objects.create(
        name="Ольга Сидорова",
        specialization="Стилист",
        phone="+7 911 222-22-22",
        email="olga@example.com"
    )


@pytest.fixture
def procedure_cut(Models):
    """Создает процедуру 'Стрижка'"""
    Procedure = Models["Procedure"]
    return Procedure.objects.create(name="Стрижка", price=1500.0)


@pytest.fixture
def procedure_manicure(Models):
    """Создает процедуру 'Маникюр'"""
    Procedure = Models["Procedure"]
    return Procedure.objects.create(name="Маникюр", price=2000.0)


@pytest.fixture
def procedure_coloring(Models):
    """Создает процедуру 'Покраска волос'"""
    Procedure = Models["Procedure"]
    return Procedure.objects.create(name="Покраска волос", price=3500.0)


@pytest.fixture
def procedure_massage(Models):
    """Создает процедуру 'Массаж лица'"""
    Procedure = Models["Procedure"]
    return Procedure.objects.create(name="Массаж лица", price=2500.0)


@pytest.fixture
def test_client(Models):
    """Создает тестового клиента"""
    Client = Models["Client"]
    return Client.objects.create(
        name="Тестовый Клиент",
        phone_number="+7 912 345-67-89",
        email="client@example.com",
        loyalty_points=100
    )



@pytest.fixture
def appointment(Models, salon, specialist, procedure_cut):
    """
    Создает тестовую запись (Appointment) на 15 января 2025, 14:00
    """
    Appointment = Models["Appointment"]
    return Appointment.objects.create(
        salon=salon,
        specialist=specialist,
        procedure=procedure_cut,
        date=dt.date(2025, 1, 15),
        time=dt.time(14, 0),
        client_name="Иван Петров",
        client_phone="+7 912 345-67-89",
        start_time=dt.time(14, 0),
        end_time=dt.time(15, 0)
    )


# ============================================================================
# PYTEST FIXTURES: ВСПОМОГАТЕЛЬНЫЕ ДАТЫ И ВРЕМЯ
# ============================================================================

@pytest.fixture
def date_2025():
    """Возвращает тестовую дату: 15 января 2025"""
    return dt.date(2025, 1, 15)


@pytest.fixture
def date_today():
    """Возвращает сегодняшнюю дату"""
    return dt.date.today()


@pytest.fixture
def date_tomorrow():
    """Возвращает завтрашнюю дату"""
    return dt.date.today() + dt.timedelta(days=1)


@pytest.fixture
def time_morning():
    """Возвращает утреннее время: 10:00"""
    return dt.time(10, 0)


@pytest.fixture
def time_afternoon():
    """Возвращает дневное время: 14:00"""
    return dt.time(14, 0)


@pytest.fixture
def time_evening():
    """Возвращает вечернее время: 18:00"""
    return dt.time(18, 0)


# ============================================================================
# PYTEST FIXTURES: МАССОВОЕ СОЗДАНИЕ ДАННЫХ ДЛЯ НАГРУЗОЧНЫХ ТЕСТОВ
# ============================================================================

@pytest.fixture
def bulk_salons(Models):
    """
    Создает 50 салонов для нагрузочного тестирования
    Возвращает список созданных объектов Salon
    """
    Salon = Models["Salon"]
    salons = []
    for i in range(1, 51):
        salon = Salon.objects.create(
            name=f"Salon {i}",
            address=f"Address {i}",
            phone=f"+7 900 {i:07d}",
            email=f"salon{i}@example.com",
            opening_time=dt.time(10, 0),
            closing_time=dt.time(19, 0),
        )
        salons.append(salon)
    return salons


@pytest.fixture
def bulk_specialists(Models):
    """
    Создает 100 мастеров для нагрузочного тестирования
    Возвращает список созданных объектов Specialist
    """
    Specialist = Models["Specialist"]
    specialists = []
    specializations = ["Парикмахер", "Мастер маникюра", "Стилист", "Косметолог", "Визажист"]

    for i in range(1, 101):
        specialist = Specialist.objects.create(
            name=f"Мастер {i}",
            specialization=specializations[i % len(specializations)],
            phone=f"+7 911 {i:07d}",
            email=f"master{i}@example.com"
        )
        specialists.append(specialist)
    return specialists


@pytest.fixture
def bulk_procedures(Models):
    """
    Создает 50 процедур для нагрузочного тестирования
    Возвращает список созданных объектов Procedure
    """
    Procedure = Models["Procedure"]
    procedures = []
    base_prices = [1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000]

    for i in range(1, 51):
        procedure = Procedure.objects.create(
            name=f"Процедура {i}",
            price=base_prices[i % len(base_prices)] + (i * 10)
        )
        procedures.append(procedure)
    return procedures


@pytest.fixture
def bulk_appointments(Models, salon, specialist, procedure_cut):
    """
    Создает 100 записей для нагрузочного тестирования
    Распределяет по разным датам и временам
    """
    Appointment = Models["Appointment"]
    Specialist = Models["Specialist"]

    # Создаем дополнительных мастеров для избежания конфликтов unique_together
    specialists = [specialist]
    for i in range(2, 11):
        specialists.append(Specialist.objects.create(
            name=f"Load Test Master {i}",
            specialization="Тестовый"
        ))

    appointments = []
    start_date = dt.date(2025, 1, 10)

    for i in range(100):
        day_offset = i // 9  # 9 слотов в день (10:00-18:00)
        hour = 10 + (i % 9)  # Время от 10 до 18
        current_date = start_date + dt.timedelta(days=day_offset)
        specialist_idx = i % len(specialists)

        appointment = Appointment.objects.create(
            salon=salon,
            specialist=specialists[specialist_idx],
            procedure=procedure_cut,
            date=current_date,
            time=dt.time(hour, 0),
            client_name=f"LoadClient{i}",
            client_phone=f"+7 900 {i:07d}",
            start_time=dt.time(hour, 0),
            end_time=dt.time(hour + 1, 0)
        )
        appointments.append(appointment)

    return appointments


# ============================================================================
# PYTEST FIXTURES: ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ ДЛЯ ХЕНДЛЕРОВ
# ============================================================================

@pytest.fixture
def user_data_complete(salon, specialist, procedure_cut, date_2025):
    """
    Возвращает полностью заполненный словарь USER_DATA для создания записи
    """
    return {
        "salon": str(salon.id),
        "master": str(specialist.id),
        "procedure": str(procedure_cut.id),
        "date": str(date_2025),
        "time": dt.time(14, 0),
        "start_time": dt.time(14, 0),
        "end_time": dt.time(15, 0)
    }


@pytest.fixture
def user_data_partial(salon):
    """
    Возвращает частично заполненный USER_DATA (только салон выбран)
    """
    return {
        "salon": str(salon.id),
    }


@pytest.fixture(autouse=True)
def clear_user_data():
    """
    Автоматически очищает глобальный USER_DATA перед каждым тестом
    """
    from handlers import USER_DATA
    USER_DATA.clear()
    yield
    USER_DATA.clear()


# ============================================================================
# PYTEST FIXTURES: DJANGO ADMIN
# ============================================================================

@pytest.fixture
def admin_user(django_user_model):
    """
    Создает суперпользователя для тестирования Django Admin
    """
    return django_user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123"
    )


@pytest.fixture
def admin_client(client, admin_user):
    """
    Возвращает клиент Django с авторизованным администратором
    """
    client.login(username="admin", password="adminpass123")
    return client


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


# ============================================================================
# PYTEST MARKERS
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """
    Автоматически маркирует тесты, использующие БД
    """
    for item in items:
        if 'django_db' in item.keywords:
            item.add_marker(pytest.mark.django_db)


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТЕСТОВ
# ============================================================================

def create_test_appointment(Models, **kwargs):
    """
    Вспомогательная функция для создания тестовой записи с дефолтными значениями

    Args:
        Models: словарь моделей из фикстуры
        **kwargs: переопределение полей записи

    Returns:
        Appointment: созданная запись
    """
    Appointment = Models["Appointment"]
    defaults = {
        'date': dt.date(2025, 1, 15),
        'time': dt.time(14, 0),
        'start_time': dt.time(14, 0),
        'end_time': dt.time(15, 0),
        'client_name': 'Test Client',
        'client_phone': '+7 999 000-00-00',
    }
    defaults.update(kwargs)
    return Appointment.objects.create(**defaults)


def assert_keyboard_contains_text(keyboard, expected_text):
    """
    Проверяет, что клавиатура содержит кнопку с определенным текстом

    Args:
        keyboard: InlineKeyboardMarkup
        expected_text: ожидаемый текст кнопки

    Returns:
        bool: True если текст найден
    """
    all_texts = [
        btn.text
        for row in keyboard.inline_keyboard
        for btn in row
    ]
    return expected_text in all_texts


def get_callback_data_list(keyboard):
    """
    Извлекает все callback_data из клавиатуры

    Args:
        keyboard: InlineKeyboardMarkup

    Returns:
        list: список всех callback_data
    """
    return [
        btn.callback_data
        for row in keyboard.inline_keyboard
        for btn in row
        if btn.callback_data
    ]
