import os
import random
import string
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'user.db')

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')


ADMINS = frozenset(['palmargisla@gmail.com'])
SECRET_KEY = 'hestur hleypur um geltandi eins og hundur'

SQLALCHEMY_COMMIT_ON_TEARDOWN = True
DATABASE_CONNECT_OPTIONS = {}

THREADS_PER_PAGE = 8

WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = "Eitthvadrosalegaerfittadgiskaautaf1337"

RECAPTCHA_USE_SSL = False
RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
RECAPTCHA_OPTIONS = {'theme': 'white'}

OAUTH_CREDENTIALS = {
   'facebook': {
       'id': '642104792615678',
       'secret': '6567bb17586249896670965cc7e40053'
   },
   'google': {
       'id': '553790731870-1f3giabgt6q93eqi3hf3ssmh8ckrf62e.apps.googleusercontent.com',
       'secret': 'OitS-AwC8Bg9LjSfcdDtbRsG'
   },
   'microsoft': {
       'id': '',
       'secret': ''
   }
}

SESSION_COOKIE_NAME = 'AO45E'
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_NAME = 'RS3F2'
REMEMBER_COOKIE_HTTPONLY = True