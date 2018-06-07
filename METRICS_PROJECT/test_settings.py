from METRICS_PROJECT.settings import *
import os

OPENERP_URL = '127.0.0.1'
OPENERP_DATABASE = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'erp': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cmasscrm',
        'USER': '',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}
IS_TESTING = True
