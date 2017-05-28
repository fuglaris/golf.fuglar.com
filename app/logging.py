import logging
from app.models import SessionContext, Error
from flask_login import current_user


class Logger(object):
    """ Class used to log messages """

    def __init__(self):
        self.logger = logging.getLogger('activity_logger')
        hdlr = logging.FileHandler('activity.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

    def register_failed(self, email):
        self.logger.warning('Register - email:\'{email}\' was reused, register failed'\
                       .format(email=email))

    def register_successful(self, email):
        self.logger.info('Register - email:\'{email}\' register successfully'\
                    .format(email=email))

    def login_failed_user(self, email):
        self.logger.warning('Login - email:\'{email}\' tried to login, does not exist'\
                       .format(email=email))

    def login_failed_password(self, email):
        self.logger.warning('Login - email:\'{email}\' tried to login with incorrect password'\
                       .format(email=email))

    def login_successful(self, email):
        self.logger.info('Login - email:\'{email}\' login successfully'\
                    .format(email=email))

    def oauth_register_failed(self, email):
        self.logger.warning('Register oauth - email:\'{email}\' register failed'\
                       .format(email=email))

    def oauth_register_successful(self, email):
        self.logger.info('Register oauth - email:\'{email}\' register successfully'\
                       .format(email=email))

    def oauth_login_successful(self, email):
        self.logger.info('Login oauth - email:\'{email}\' login successfully'\
                    .format(email=email))


def logg_error(location, error, warning=False):
    """ Loggs error to database """

    with SessionContext() as session:
        i = None

        if current_user:
            i = current_user.id

        err = Error(
            location=location,
            error_message=error,
            current_user_id=i,
            warning=warning
        )

        session.add(err)
        session.commit()

    return True


logger = Logger()
