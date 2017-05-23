import os, sys
from config import basedir

from flask import Flask, render_template, request, redirect, url_for
from flask_assets import Environment, Bundle

from app.constants import BadRequestError


app = Flask(__name__)

from flask_login import LoginManager, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong"

login_manager.refresh_view = "app.reauthenticate"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"


from app.models import SessionContext, User, Access, Company

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


@app.route('/favicon.ico')
def favicon():
    """ Serves favicon """

    return url_for('static', filename='img/golf-ball.jpg')


@app.errorhandler(404)
def page_not_found(msg):
    """ 404 error handler, redirects to index """

    return redirect(url_for("general.index"))


@app.errorhandler(BadRequestError)
def bad_request_handler(error):
    """ Bad request handler, redirects to index """

    return redirect(url_for("general.index"))


@app.before_request
def before_request():
    """ Redirects user to secure https if page is requested as http """

    if not 'localhost' in request.url:
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)



@app.context_processor
def utility_processor():
    """ Serves all templates with base dict, containing language, user, etc. """

    with SessionContext() as session:
        try:
            access = session.query(Access.id).filter_by(user_id=current_user.id).all()
            companies = session.query(Company).filter(Company.id.in_([company_id for company_id in access])).all()
        except AttributeError:
            # AttributeError is catched if current_user is not defined.
            companies = None

        return dict(language="is", user=current_user, companies=companies)

#bundels imported.
from app.util.assets import bundles
assets = Environment(app)
assets.register(bundles)

from app.views import general
from app.views import api
from app.views import admin
app.register_blueprint(general.mod)
app.register_blueprint(api.mod)
app.register_blueprint(admin.mod)

#from app import views
