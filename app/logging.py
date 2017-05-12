import logging


logger = logging.getLogger('activity_logger')
hdlr = logging.FileHandler('activity.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)



class Logger(object):
    """ Class used to log messages """

    def __init__(self):
        pass

    @staticmethod
    def register_failed(email):
        logger.warning('Register - email:\'{email}\' was reused, register failed'\
                       .format(email=email))

    @staticmethod
    def register_successful(email):
        logger.info('Register - email:\'{email}\' register successfully'\
                    .format(email=email))

    @staticmethod
    def login_failed_user(email):
        logger.warning('Login - email:\'{email}\' tried to login, does not exist'\
                       .format(email=email))

    @staticmethod
    def login_failed_password(email):
        logger.warning('Login - email:\'{email}\' tried to login with incorrect password'\
                       .format(email=email))

    @staticmethod
    def login_successful(email):
        logger.info('Login - email:\'{email}\' login successfully'\
                    .format(email=email))

    @staticmethod
    def oauth_register_failed(email):
        logger.warning('Register oauth - email:\'{email}\' register failed'\
                       .format(email=email))

    @staticmethod
    def oauth_register_successful(email):
        logger.info('Register oauth - email:\'{email}\' register successfully'\
                       .format(email=email))

    @staticmethod
    def oauth_login_successful(email):
        logger.info('Login oauth - email:\'{email}\' login successfully'\
                    .format(email=email))
