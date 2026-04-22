import pytest

from support.models import ContactRequest


pytestmark = pytest.mark.django_db


def contact_payload(**overrides):
    payload = {
        "name": "Анна Покупатель",
        "email": "anna@example.com",
        "phone": "+79991234567",
        "topic": ContactRequest.Topic.DELIVERY,
        "order_number": "AA-1001",
        "message": "Подскажите, пожалуйста, когда заказ будет передан в доставку?",
    }
    payload.update(overrides)
    return payload


def test_guest_can_create_contact_request(api_client):
    response = api_client.post(
        "/api/contact-requests/",
        contact_payload(),
        format="json",
        HTTP_USER_AGENT="pytest browser",
        REMOTE_ADDR="203.0.113.10",
    )

    assert response.status_code == 201
    request = ContactRequest.objects.get()
    assert request.user is None
    assert request.status == ContactRequest.Status.NEW
    assert request.email == "anna@example.com"
    assert request.ip_address == "203.0.113.10"
    assert request.user_agent == "pytest browser"
    assert response.data["status"] == ContactRequest.Status.NEW


def test_authenticated_contact_request_is_linked_to_user(authenticated_client, user):
    response = authenticated_client.post(
        "/api/contact-requests/",
        contact_payload(email=user.email),
        format="json",
    )

    assert response.status_code == 201
    assert ContactRequest.objects.get().user == user


def test_contact_request_requires_meaningful_message(api_client):
    response = api_client.post(
        "/api/contact-requests/",
        contact_payload(message="Коротко"),
        format="json",
    )

    assert response.status_code == 400
    assert "message" in response.data
