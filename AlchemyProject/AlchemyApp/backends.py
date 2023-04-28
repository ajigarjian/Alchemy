from django.contrib.auth.backends import BaseBackend
from .models import CustomUser

# Custom authentication backend to override built in Django authentication for default users
class CustomUserAuthenticationBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None