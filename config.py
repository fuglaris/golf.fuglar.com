import os
import random
import string
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
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
           'secret': os.environ.get('FB_SECRET')
       },
       'google': {
           'id': '4219908234-ktvfr0ojp5j3gan8tk09cfbh8c4kvgj1.apps.googleusercontent.com',
           'secret': os.environ.get('G_SECRET')
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


class ProductionConfig(Config):
    DATABASE_URI = os.environ.get('DATABASE_URL', '').replace("postgresql://", "postgresql+psycopg2://")
    

class DevelopmentConfig(Config):
    DATABASE_URI = os.environ.get('DATABASE_URL')
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
