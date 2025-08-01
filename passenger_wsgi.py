import sys
import os

sys.path.insert(0, os.path.expanduser('~/django-blog'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
