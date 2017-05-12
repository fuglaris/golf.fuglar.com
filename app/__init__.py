import os, sys
from config import basedir

from flask import Flask
from flask_assets import Environment, Bundle

#hashing algorithm
from flask_argon2 import Argon2

app = Flask(__name__)
argon2 = Argon2(app)
app.config.from_object('config')

from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong"

login_manager.refresh_view = "app.reauthenticate"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"

from app.models import SessionContext, User


@login_manager.user_loader
def load_user(id):
    with SessionContext() as session:
        return session.query(User).get(int(id))




def install_secret_key(app, filename='secret_key'):
    """Configure the SECRET_KEY from a file
    in the instance directory.

    If the file does not exist, print instructions
    to create it from a shell with a random key,
    then exit.
    """
    filename = os.path.join(app.instance_path, filename)

    try:
        app.config['SECRET_KEY'] = open(filename, 'rb').read()
    except IOError:
        print('Error: No secret key. Create it with:')
        full_path = os.path.dirname(filename)
        if not os.path.isdir(full_path):
            print('mkdir -p {filename}'.format(filename=full_path))
        print('head -c 24 /dev/urandom > {filename}'.format(filename=filename))
        sys.exit(1)

install_secret_key(app)


#bundels imported.
from app.util.assets import bundles
assets = Environment(app)
assets.register(bundles)


from app import views
