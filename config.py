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


class ProductionConfig(Config):
    DATABASE_URI = os.environ.get('DATABASE_URL', '').replace("postgresql://", "postgresql+psycopg2://")
    

class DevelopmentConfig(Config):
    #DATABASE_URI = 'postgresql+psycopg2://sucufvwoyqhjou:494ef44cf2cfe52f5c58ed2460049c67be8c73779cb1a92f460e27f45f7c9543@ec2-54-247-79-178.eu-west-1.compute.amazonaws.com:5432/d49cjvdpjfeiu7'
    DATABASE_URI = 'postgresql+psycopg2://beabmullgttgfd:1685f6482f774544141a14475bad3ab0e039c5e5063ee3bac651d42a250c9368@ec2-54-73-22-169.eu-west-1.compute.amazonaws.com:5432/db0co4ifmg6e9b'
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
