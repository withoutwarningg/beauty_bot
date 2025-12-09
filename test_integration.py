import datetime as dt
import pytest
from django.urls import reverse  # ДОБАВЛЕНО

pytestmark = pytest.mark.django_db


def test_I1_get_salon_keyboard_lists_salons(salon, salon_b):
    from keyboards import get_salon_keyboard
    kb = get_salon_keyboard()
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert salon.name in "".join(texts)
    assert salon_b.name in "".join(texts)


def test_I2_phone_handler_creates_appointment(Models, salon, specialist, procedure_cut, monkeypatch):
    from handlers import USER_DATA, phone_handler
    from tests.conftest import DummyUpdate, DummyContext, DummyBot, DummyMessage

    chat_id = 777
    USER_DATA[chat_id] = {
        "salon": str(salon.id),
        "master": str(specialist.id),
        "procedure": str(procedure_cut.id),
        "date": "2025-01-15",
        "time": dt.time(14, 0),
        "start_time": dt.time(14, 0),
        "end_time": dt.time(15, 0),
    }

    bot = DummyBot()
    # ИСПРАВЛЕНО: message вместо msg, правильный порядок аргументов
    message = DummyMessage(text="+7 912 345 67 89", chat_id=chat_id, first_name="Ivan")
    update = DummyUpdate(message=message)
    context = DummyContext(bot=bot)

    phone_handler(update, context)

    Appointment = Models["Appointment"]
    a = Appointment.objects.get()
    assert a.salon_id == salon.id
    assert a.specialist_id == specialist.id
    assert a.procedure_id == procedure_cut.id
    assert str(a.date) == "2025-01-15"
    assert a.start_time == dt.time(14, 0)
    assert a.end_time == dt.time(15, 0)
    assert a.client_phone == "+7 912 345 67 89"
    assert any("подтверждена" in m["text"].lower() for m in bot.sent)


def test_I3_is_free_time_integration_with_orm(specialist, appointment):
    from funcs import is_free_time
    result = is_free_time("master", specialist.id, appointment.date)
    assert result.get(dt.time(14, 0)) is False
    assert result.get(dt.time(13, 0)) is True


def test_I5_full_user_data_flow_creates_appointment(Models, salon, procedure_cut, monkeypatch):
    # Пробежим по основным этапам: salon -> procedure -> date -> time -> phone
    from handlers import USER_DATA, button_handler, phone_handler
    from tests.conftest import DummyBot, DummyCallbackQuery, DummyUpdate, DummyContext, DummyMessage

    Appointment = Models["Appointment"]

    chat_id = 991
    bot = DummyBot()
    ctx = DummyContext(bot=bot)

    # agree
    update = DummyUpdate(cq=DummyCallbackQuery("agree", chat_id=chat_id))
    button_handler(update, ctx)

    # salon list -> pick salon
    update = DummyUpdate(cq=DummyCallbackQuery(f"salon_{1}", chat_id=chat_id))
    button_handler(update, ctx)
    # сохраним правильный id салона
    from bot.models import Salon
    first_salon = Salon.objects.first()
    USER_DATA[chat_id]["salon"] = str(first_salon.id)

    # choose_procedure -> pick procedure
    button_handler(DummyUpdate(cq=DummyCallbackQuery("choose_procedure", chat_id=chat_id)), ctx)

    # создадим процедуру и выберем ее
    from bot.models import Procedure
    proc = Procedure.objects.create(name="TestProc", price=1111)
    button_handler(DummyUpdate(cq=DummyCallbackQuery(f"procedure_{proc.id}", chat_id=chat_id)), ctx)

    # date -> time
    button_handler(DummyUpdate(cq=DummyCallbackQuery("date_2025-01-15", chat_id=chat_id)), ctx)
    button_handler(DummyUpdate(cq=DummyCallbackQuery("time_2025-01-15_10:00", chat_id=chat_id)), ctx)

    # phone -> create appointment
    # ИСПРАВЛЕНО: message вместо msg, правильный порядок аргументов
    message = DummyMessage(text="+7 000 000-00-00", chat_id=chat_id, first_name="Ivan")
    phone_handler(DummyUpdate(message=message), ctx)

    assert Appointment.objects.count() == 1
    a = Appointment.objects.first()
    assert a.salon_id == first_salon.id
    assert a.procedure_id == proc.id
    assert str(a.date) == "2025-01-15"
    assert a.time == dt.time(10, 0)


def test_I6_get_procedure_keyboard_lists_procedures(procedure_cut, procedure_manicure):
    from keyboards import get_procedure_keyboard
    kb = get_procedure_keyboard()
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    content = " ".join(texts)
    assert "Стрижка" in content
    assert "Маникюр" in content


# =====================================================
# ТЕСТ И7: Django Admin Panel — управление салонами
# =====================================================
@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser("admin", "admin@example.com", "pass")


def test_I7_admin_crud_operations_on_salons(client, admin_user):
    """
    Проверка полного цикла CRUD операций с салонами через Django Admin
    """
    from bot.models import Salon
    import datetime as dt

    # Авторизация
    client.login(username="admin", password="pass")

    app_label = Salon._meta.app_label

    # CREATE: Создание нового салона через админку
    add_url = reverse(f"admin:{app_label}_salon_add")
    response = client.post(add_url, {
        'name': 'Test Admin Salon',
        'address': 'Admin Test Address, 123',
        'phone': '+7 999 888-77-66',
        'email': 'test@salon.com',
        'opening_time': '09:00',
        'closing_time': '20:00',
    })

    # Проверяем, что салон создался
    assert Salon.objects.filter(name='Test Admin Salon').exists()
    created_salon = Salon.objects.get(name='Test Admin Salon')
    assert created_salon.address == 'Admin Test Address, 123'

    # READ: Проверка отображения в списке
    list_url = reverse(f"admin:{app_label}_salon_changelist")
    response = client.get(list_url)
    assert response.status_code == 200
    assert 'Test Admin Salon' in response.content.decode('utf-8')

    # UPDATE: Изменение салона
    change_url = reverse(f"admin:{app_label}_salon_change", args=[created_salon.id])
    response = client.post(change_url, {
        'name': 'Updated Admin Salon',
        'address': 'Updated Address',
        'phone': '+7 999 888-77-66',
        'email': 'updated@salon.com',
        'opening_time': '10:00',
        'closing_time': '19:00',
    })

    # Проверяем изменения
    created_salon.refresh_from_db()
    assert created_salon.name == 'Updated Admin Salon'
    assert created_salon.opening_time == dt.time(10, 0)

    # DELETE: Удаление салона
    delete_url = reverse(f"admin:{app_label}_salon_delete", args=[created_salon.id])
    response = client.post(delete_url, {'post': 'yes'})

    # Проверяем, что салон удален
    assert not Salon.objects.filter(id=created_salon.id).exists()


# =====================================================
# ТЕСТ И8: Циркулярные импорты между модулями
# =====================================================
def test_I8_no_circular_import_errors():
    """
    Проверка отсутствия ошибок циркулярного импорта при загрузке модулей
    """
    import sys
    import importlib

    # Очищаем кеш импортов для чистого теста
    modules_to_reload = ['handlers', 'keyboards', 'funcs']
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]

    # Пытаемся импортировать модули в разном порядке
    try:
        import handlers
        assert hasattr(handlers, 'button_handler')
        assert hasattr(handlers, 'phone_handler')
        assert hasattr(handlers, 'USER_DATA')

        import keyboards
        assert hasattr(keyboards, 'get_salon_keyboard')
        assert hasattr(keyboards, 'get_time_slots_keyboard')
        assert hasattr(keyboards, 'get_procedure_keyboard')

        import funcs
        assert hasattr(funcs, 'is_free_time')

    except ImportError as e:
        pytest.fail(f"Circular import error detected: {e}")

    # Проверяем, что функции вызываются без ошибок
    try:
        from handlers import USER_DATA
        from keyboards import get_salon_keyboard

        # Вызов не должен вызвать ошибку импорта
        kb = get_salon_keyboard()
        assert kb is not None

    except Exception as e:
        pytest.fail(f"Error calling imported functions: {e}")


# =====================================================
# ТЕСТ И9: Интеграция между USER_DATA и базой данных
# =====================================================
def test_I9_user_data_to_database_integration(Models, salon, specialist, procedure_cut):
    """
    Проверка полной интеграции: USER_DATA → handlers → database
    """
    from handlers import USER_DATA, phone_handler
    from tests.conftest import DummyUpdate, DummyContext, DummyBot, DummyMessage
    import datetime as dt

    chat_id = 9999

    # Симулируем заполнение USER_DATA через последовательность кнопок
    USER_DATA[chat_id] = {
        "salon": str(salon.id),
        "master": str(specialist.id),
        "procedure": str(procedure_cut.id),
        "date": "2025-01-15",
        "time": dt.time(14, 0),
        "start_time": dt.time(14, 0),
        "end_time": dt.time(15, 0)
    }

    # Симулируем ввод телефона
    bot = DummyBot()
    message = DummyMessage(text="+7 912 345 67 89", chat_id=chat_id, first_name="TestUser")
    update = DummyUpdate(message=message)
    context = DummyContext(bot=bot)

    # Вызываем обработчик телефона
    phone_handler(update, context)

    # Проверяем, что запись создалась в БД
    Appointment = Models["Appointment"]
    appointment = Appointment.objects.filter(
        salon=salon,
        specialist=specialist,
        client_phone="+7 912 345 67 89"
    ).first()

    assert appointment is not None, "Запись не создалась в БД"
    assert appointment.date == dt.date(2025, 1, 15)
    assert appointment.time == dt.time(14, 0)
    assert appointment.client_name == "TestUser"

    # Проверяем, что пользователю отправлено подтверждение
    assert any("подтверждена" in m["text"].lower() for m in bot.sent)
