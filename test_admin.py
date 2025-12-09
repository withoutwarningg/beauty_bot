import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser("admin", "admin@example.com", "pass")


def test_I4_admin_lists_salons(client, admin_user, salon):
    # Определяем правильный app_label динамически (на случай bot/scripts)
    from bot.models import Salon
    app_label = Salon._meta.app_label  # обычно 'bot'
    client.login(username="admin", password="pass")
    url = reverse(f"admin:{app_label}_salon_changelist")
    resp = client.get(url)
    assert resp.status_code == 200
    assert salon.name in resp.content.decode("utf-8")
