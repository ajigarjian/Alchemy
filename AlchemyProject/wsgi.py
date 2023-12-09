"""
WSGI config for AlchemyProject project.

It exposes the WSGI callable as a module-level variable named ``app``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AlchemyProject.settings')

# vercel_app/wsgi.py
application = get_wsgi_application()
