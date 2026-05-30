from django.contrib.auth.hashers import (
    make_password,
    check_password
)

from django.core.mail import send_mail
from django.conf import settings


import random


def generate_otp(length=6):

    digits = "0123456789"

    return "".join(
        random.choice(digits)
        for _ in range(length)
    )

def hash_password(password):
    return make_password(password)


def verify_password(plain_password,hashed_password):
    return check_password(
        plain_password,
        hashed_password
    )


def send_otp_email(email,otp,subject="OTP Verification"):
    send_mail(
        subject,
        f"Welcome to BSGUPLMS Your Register OTP is {otp}",
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False
    )