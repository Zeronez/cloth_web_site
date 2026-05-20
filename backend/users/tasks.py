from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from config.celery import app

import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def _frontend_url(base_path, *, uid, token):
    base_url = settings.FRONTEND_APP_URL.rstrip("/")
    path = base_path if base_path.startswith("/") else f"/{base_path}"
    return f"{base_url}{path}?uid={uid}&token={token}"


def build_email_confirmation_message(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    confirmation_url = _frontend_url(
        settings.AUTH_EMAIL_CONFIRMATION_PATH,
        uid=uid,
        token=token,
    )
    subject = "AnimeAttire: подтвердите email"
    body = (
        f"Здравствуйте, {user.first_name or user.username}!\n\n"
        "Подтвердите ваш email для аккаунта AnimeAttire:\n"
        f"{confirmation_url}\n\n"
        "Если это были не вы, просто проигнорируйте это письмо."
    )
    return subject, body


def build_password_reset_message(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = _frontend_url(
        settings.AUTH_PASSWORD_RESET_PATH,
        uid=uid,
        token=token,
    )
    subject = "AnimeAttire: восстановление пароля"
    body = (
        f"Здравствуйте, {user.first_name or user.username}!\n\n"
        "Мы получили запрос на смену пароля для вашего аккаунта AnimeAttire.\n"
        f"Перейдите по ссылке, чтобы задать новый пароль:\n{reset_url}\n\n"
        "Если вы не запрашивали смену пароля, просто проигнорируйте это письмо."
    )
    return subject, body


def _send_plain_email(user, subject, body):
    EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    ).send(fail_silently=False)


@app.task(name="users.send_email_confirmation_email")
def send_email_confirmation_email(user_id):
    user = User.objects.get(pk=user_id)
    if not user.email:
        return {"status": "skipped", "reason": "missing_email"}
    if user.is_email_verified:
        return {"status": "skipped", "reason": "already_verified"}
    subject, body = build_email_confirmation_message(user)
    _send_plain_email(user, subject, body)
    return {"status": "sent", "email": user.email}


@app.task(name="users.send_password_reset_email")
def send_password_reset_email(user_id):
    user = User.objects.get(pk=user_id)
    if not user.email:
        return {"status": "skipped", "reason": "missing_email"}
    subject, body = build_password_reset_message(user)
    _send_plain_email(user, subject, body)
    return {"status": "sent", "email": user.email}


@app.task(name="users.send_phone_confirmation_sms")
def send_phone_confirmation_sms(*, user_id, phone, code):
    """
    Stub SMS sender.

    Replace with a real provider integration when selected.
    """
    logger.info("Phone confirmation code for user=%s phone=%s code=%s", user_id, phone, code)
    return {"status": "sent", "phone": phone}
