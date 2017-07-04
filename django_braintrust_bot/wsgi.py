"""
WSGI config for django_braintrust_bot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_braintrust_bot.settings")

application = get_wsgi_application()

if 'ON_HEROKU' in os.environ or 'PRODUCTION' in os.environ:
    application = DjangoWhiteNoise(application)
