from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(email=username)