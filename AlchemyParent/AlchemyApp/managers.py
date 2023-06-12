from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(email=username)

    def create_superuser(self, email, client_id, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        client = Client.objects.get(id=client_id)
        return self._create_user(email, password, client=client, **extra_fields)

    def _create_user(self, email, password=None, client=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, client=client, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def prompt_for_fields(self, interactive=True, **kwargs):
        field_names = set(self.model.REQUIRED_FIELDS) | {'email', 'password'}
        field_names.remove('client_id')
        field_names.add('client')

        field_values = super().prompt_for_fields(interactive, **kwargs)

        if interactive and 'client_id' not in kwargs:
            client_id = input("Client (Client.id): ")
            field_values['client_id'] = client_id
        elif 'client_id' in kwargs:
            field_values['client_id'] = kwargs['client_id']

        return field_values