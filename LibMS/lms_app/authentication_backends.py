from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import CustomUser

class EmailOrPhoneBackend(BaseBackend):
    """
    Authenticate using either email or phone number.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Try to fetch the user by email or phone
        try:
            user = CustomUser.objects.get(email=username) if "@" in username else CustomUser.objects.get(phone=username)
        except CustomUser.DoesNotExist:
            return None

        # Check if the password matches
        if user and check_password(password, user.password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
