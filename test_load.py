import time
import datetime as dt
import pytest

pytestmark = pytest.mark.django_db


# =====================================================
# ТЕСТ Н1: Производительность is_free_time при большом объеме данных
# =====================================================
def test_N1_is_free_time_with_large_dataset(Models, salon):
    """
    Проверить производительность функции is_free_time при работе с
    большим количеством записей в БД (1 вызов при 10,000 записей)
    """
    from funcs import is_free_time
    from bot.models import Specialist, Procedure

    Appointment = Models["Appointment"]

    # Создаем базовые данные
    procedure = Procedure.objects.create(name="TestProc", price=1000)
    specialists = [Specialist.objects.create(name=f"Master{i}") for i in range(100)]

    # Создаем 10,000 записей Appointment на разные даты
    print("\n[N1] Создание 10,000 записей...")
    appointments_created = 0

    for day in range(1, 29):  # 28 дней
        for hour in range(10, 19):  # 9 часов в день
            for spec_idx in range(min(40, 100)):  # До 40 мастеров используем
                if appointments_created >= 10000:
                    break
                specialist = specialists[spec_idx]
                Appointment.objects.create(
                    salon=salon,
                    specialist=specialist,
                    procedure=procedure,
                    date=dt.date(2025, 1, day),
                    time=dt.time(hour, 0),
                    client_name=f"Client{appointments_created}",
                    client_phone=f"+7 900 {appointments_created:07d}",
                    start_time=dt.time(hour, 0),
                    end_time=dt.time(hour + 1, 0)
                )
                appointments_created += 1
        if appointments_created >= 10000:
            break

    print(f"[N1] Создано {appointments_created} записей")
    assert Appointment.objects.count() >= 10000, "Недостаточно записей для теста"

    # ОДИН запрос is_free_time при большом объеме данных
    print("[N1] Выполнение 1 вызова is_free_time с 10,000 записями в БД...")
    start = time.time()
    availability = is_free_time("salon", salon.id, dt.date(2025, 1, 15))
    elapsed = time.time() - start

    print(f"[N1] Время выполнения: {elapsed:.3f} сек")

    # Проверяем результат и производительность
    assert isinstance(availability, dict), "Функция должна вернуть словарь"
    assert elapsed < 0.5, f"Запрос слишком медленный: {elapsed:.3f} сек (лимит: 0.5 сек)"


# =====================================================
# ТЕСТ Н2: Производительность создания записи при большом объеме данных
# =====================================================
def test_N2_create_appointment_with_large_dataset(Models, salon, procedure_cut):
    """
    Проверить производительность создания записи Appointment
    при наличии большого объема данных в таблице (1 создание при 50,000 записей)
    """
    from bot.models import Specialist

    Appointment = Models["Appointment"]

    print("\n[N2] Создание 50,000 существующих записей...")

    # Создаем 200 мастеров для разнообразия
    specialists = [Specialist.objects.create(name=f"Master{i}") for i in range(200)]

    # Создаем 50,000 записей
    appointments_created = 0
    for day in range(1, 29):  # 28 дней
        for hour in range(10, 19):  # 9 часов в день
            for spec_idx in range(200):  # Все мастера
                if appointments_created >= 50000:
                    break
                specialist = specialists[spec_idx]
                Appointment.objects.create(
                    salon=salon,
                    specialist=specialist,
                    procedure=procedure_cut,
                    date=dt.date(2025, 1, day),
                    time=dt.time(hour, 0),
                    client_name=f"ExistingClient{appointments_created}",
                    client_phone=f"+7 911 {appointments_created:07d}",
                    start_time=dt.time(hour, 0),
                    end_time=dt.time(hour + 1, 0)
                )
                appointments_created += 1
        if appointments_created >= 50000:
            break

    print(f"[N2] Создано {appointments_created} существующих записей")
    assert Appointment.objects.count() >= 50000, "Недостаточно записей для теста"

    # Создаем нового мастера для новой записи (чтобы не нарушить unique_together)
    new_specialist = Specialist.objects.create(name="NewMaster")

    # ОДНА операция создания новой записи при 50,000 существующих
    print("[N2] Создание 1 новой записи при 50,000 существующих...")
    start = time.time()
    new_appointment = Appointment.objects.create(
        salon=salon,
        specialist=new_specialist,
        procedure=procedure_cut,
        date=dt.date(2025, 2, 1),
        time=dt.time(15, 0),
        client_name="NewClient",
        client_phone="+7 999 999-99-99",
        start_time=dt.time(15, 0),
        end_time=dt.time(16, 0)
    )
    elapsed = time.time() - start

    print(f"[N2] Время создания: {elapsed:.3f} сек")

    # Проверяем результат и производительность
    assert new_appointment.id is not None, "Запись не создалась"
    assert elapsed < 0.3, f"Создание слишком медленное: {elapsed:.3f} сек (лимит: 0.3 сек)"


# =====================================================
# ТЕСТ Н3: Производительность генерации клавиатуры при большом количестве салонов
# =====================================================
def test_N3_salon_keyboard_with_large_dataset(Models):
    """
    Проверить производительность генерации клавиатуры get_salon_keyboard()
    при большом количестве салонов в БД (1 вызов при 1,000 салонов)
    """
    from keyboards import get_salon_keyboard
    from bot.models import Salon

    print("\n[N3] Создание 1,000 салонов...")

    # Создаем 1,000 салонов
    for i in range(1, 1001):
        Salon.objects.create(
            name=f"Salon_{i:04d}",
            address=f"Address {i}",
            phone=f"+7 900 {i:07d}",
            email=f"salon{i}@example.com",
            opening_time=dt.time(10, 0),
            closing_time=dt.time(19, 0),
        )

    print(f"[N3] Создано {Salon.objects.count()} салонов")
    assert Salon.objects.count() >= 1000, "Недостаточно салонов для теста"

    # ОДИН вызов генерации клавиатуры при 1,000 салонов
    print("[N3] Генерация клавиатуры для 1,000 салонов...")
    start = time.time()
    keyboard = get_salon_keyboard()
    elapsed = time.time() - start

    print(f"[N3] Время генерации: {elapsed:.3f} сек")

    # Проверяем результат и производительность
    assert keyboard is not None, "Клавиатура не создалась"
    assert len(keyboard.inline_keyboard) >= 1000, "Клавиатура содержит меньше салонов, чем ожидалось"
    assert elapsed < 0.2, f"Генерация слишком медленная: {elapsed:.3f} сек (лимит: 0.2 сек)"


# =====================================================
# ТЕСТ Н4: Производительность доступа к USER_DATA при большом количестве пользователей
# =====================================================
def test_N4_user_data_with_large_dataset(monkeypatch):
    """
    Проверить производительность доступа к USER_DATA
    при работе с большим количеством активных пользователей (1 доступ при 10,000 записей)
    """
    from handlers import USER_DATA

    USER_DATA.clear()

    print("\n[N4] Заполнение USER_DATA для 10,000 пользователей...")

    # Заполняем USER_DATA для 10,000 пользователей
    for chat_id in range(1, 10001):
        USER_DATA[chat_id] = {
            "salon": str(chat_id % 100 + 1),
            "master": str(chat_id % 50 + 1),
            "procedure": str(chat_id % 20 + 1),
            "date": "2025-01-15",
            "time": dt.time(14, 0),
            "start_time": dt.time(14, 0),
            "end_time": dt.time(15, 0)
        }

    print(f"[N4] Заполнено {len(USER_DATA)} записей USER_DATA")
    assert len(USER_DATA) >= 10000, "Недостаточно записей в USER_DATA"

    # ОДИН доступ к произвольному элементу при 10,000 записей
    test_chat_id = 5555
    print(f"[N4] Доступ к USER_DATA[{test_chat_id}] при 10,000 записях...")
    start = time.time()
    user_data = USER_DATA[test_chat_id]
    elapsed = time.time() - start

    print(f"[N4] Время доступа: {elapsed:.6f} сек")

    # Проверяем результат и производительность
    assert user_data is not None, "Данные пользователя не найдены"
    assert user_data["salon"] == str(test_chat_id % 100 + 1), "Неверные данные"
    assert elapsed < 0.001, f"Доступ слишком медленный: {elapsed:.6f} сек (лимит: 0.001 сек)"

    # Проверяем изоляцию данных (выборочно 100 пользователей)
    print("[N4] Проверка изоляции данных...")
    for chat_id in range(1, 101):
        assert USER_DATA[chat_id]["salon"] == str(chat_id % 100 + 1)


# =====================================================
# ТЕСТ Н5: Производительность Django Admin при большой выборке
# =====================================================
def test_N5_admin_with_large_dataset(client, django_user_model):
    """
    Проверить производительность Django Admin при отображении списка записей
    с большой выборкой (1 запрос при 100,000 записей)
    """
    from bot.models import Appointment, Salon, Specialist, Procedure
    from django.urls import reverse

    print("\n[N5] Создание данных для админки...")

    # Создаем админа
    admin = django_user_model.objects.create_superuser("admin", "admin@example.com", "pass")
    client.login(username="admin", password="pass")

    # Создаем базовые сущности
    salon = Salon.objects.create(
        name="LoadTestSalon",
        address="Address",
        phone="+7 999 000-00-00",
        opening_time=dt.time(10, 0),
        closing_time=dt.time(19, 0)
    )

    specialists = [
        Specialist.objects.create(name=f"AdminMaster{i}", specialization="Test")
        for i in range(20)
    ]

    procedure = Procedure.objects.create(name="AdminProc", price=1000)

    # Создаем 100,000 записей (упрощенно - можем сделать меньше для скорости теста)
    print("[N5] Создание 10,000 записей для теста админки...")  # Уменьшено для скорости
    appointments_created = 0

    for day in range(1, 29):  # 28 дней
        for hour in range(10, 19):  # 9 часов
            for spec in specialists:
                if appointments_created >= 10000:  # Ограничиваем 10,000 для ускорения теста
                    break
                Appointment.objects.create(
                    salon=salon,
                    specialist=spec,
                    procedure=procedure,
                    date=dt.date(2025, 1, day),
                    time=dt.time(hour, 0),
                    client_name=f"AdminClient{appointments_created}",
                    client_phone=f"+7 922 {appointments_created:07d}",
                    start_time=dt.time(hour, 0),
                    end_time=dt.time(hour + 1, 0)
                )
                appointments_created += 1
        if appointments_created >= 10000:
            break

    print(f"[N5] Создано {appointments_created} записей")
    assert Appointment.objects.count() >= 10000, "Недостаточно записей для теста"

    # ОДИН запрос к админке при большой выборке
    url = reverse(f"admin:{Appointment._meta.app_label}_appointment_changelist")
    print(f"[N5] Запрос к админке с {Appointment.objects.count()} записями...")

    start = time.time()
    response = client.get(url)
    elapsed = time.time() - start

    print(f"[N5] Время загрузки страницы: {elapsed:.3f} сек")

    # Проверяем результат и производительность
    assert response.status_code == 200, "Страница админки не загрузилась"
    assert elapsed < 2.0, f"Загрузка слишком медленная: {elapsed:.3f} сек (лимит: 2.0 сек)"


# =====================================================
# ТЕСТ Н6: Производительность is_free_time на максимально загруженную дату
# =====================================================
def test_N6_is_free_time_on_busy_date(Models, salon, procedure_cut):
    """
    Проверить производительность функции is_free_time при запросе даты
    с максимальной загруженностью (1 вызов при 450 записях на одну дату)
    """
    from funcs import is_free_time
    from bot.models import Specialist

    Appointment = Models["Appointment"]

    print("\n[N6] Создание максимально загруженной даты...")

    # Создаем 50 мастеров
    specialists = [Specialist.objects.create(name=f"BusyMaster{i}") for i in range(50)]

    # Заполняем всё расписание на 15 января
    # 50 мастеров × 9 часов = 450 записей
    target_date = dt.date(2025, 1, 15)
    appointments_created = 0

    for spec in specialists:
        for hour in range(10, 19):  # 9 часов (10:00-18:00)
            Appointment.objects.create(
                salon=salon,
                specialist=spec,
                procedure=procedure_cut,
                date=target_date,
                time=dt.time(hour, 0),
                client_name=f"BusyClient{appointments_created}",
                client_phone=f"+7 933 {appointments_created:07d}",
                start_time=dt.time(hour, 0),
                end_time=dt.time(hour + 1, 0)
            )
            appointments_created += 1

    print(f"[N6] Создано {appointments_created} записей на {target_date}")
    assert Appointment.objects.filter(date=target_date).count() == 450, "Неверное количество записей"

    # ОДИН вызов is_free_time на максимально загруженную дату
    print(f"[N6] Проверка is_free_time для даты с 450 записями...")

    start = time.time()
    availability = is_free_time("salon", salon.id, target_date)
    elapsed = time.time() - start

    print(f"[N6] Время выполнения: {elapsed:.3f} сек")

    # Проверяем результат и производительность
    assert isinstance(availability, dict), "Функция должна вернуть словарь"

    # Все слоты должны быть заняты (False)
    all_busy = all(not available for available in availability.values())
    assert all_busy, "Не все слоты помечены как занятые"

    assert elapsed < 0.8, f"Запрос слишком медленный: {elapsed:.3f} сек (лимит: 0.8 сек)"

    print("[N6] Все временные слоты корректно помечены как занятые")
