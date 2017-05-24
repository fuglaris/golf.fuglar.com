import os
import random
import string

from datetime import datetime, date

from sqlalchemy import exc

from flask import (
    render_template, request, redirect, url_for, Blueprint
)
from flask_login import (
    login_user, logout_user, current_user, login_required, fresh_login_required
)

from app import app
from app.logging import logger, logg_error
from app.mail import send_mail
from app.oauth import OAuthSignIn
from app.constants import BadRequestError
from app.models import (
    SessionContext, IntegrityError, User, Company, Access, OAuth_User, Error
)
from app.decorators import (
    validate_login, validate_registration, validate_provider,
    is_logged_in, requires_roles
)


@app.route('/favicon.ico')
def favicon():
    """ Serves favicon """

    return url_for('static', filename='img/golf-ball.jpg')


@app.errorhandler(404)
def page_not_found(msg):
    """ 404 error handler, redirects to index """

    return redirect(url_for("index"))


@app.errorhandler(BadRequestError)
def bad_request_handler(error):
    """ Bad request handler, redirects to index """

    return redirect(url_for("index"))


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


@app.before_request
def before_request():

    if current_user and current_user.role == 4:
        return render_template("golfcourse/index.html")

@app.route('/')
@login_required
def index():
    return render_template("index.html")


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    # If request is GET, serve template for profile, otherwise its POST request
    if request.method == 'GET':
        return render_template("profile.html")

    with SessionContext() as session:
        try:
            user = session.query(User).filter_by(id=current_user.id).first()

            if request.form.get('company'):
                user.company = request.form.get('company')

            if request.form.get("displayname"):
                user.displayname = request.form.get("displayname")[:10]

            # Add and commit this user changes to database.
            session.add(user)
            session.commit()

        except Exception as e:
            session.rollback()
            # Logg error to database
            logg_error(location='profile', error=str(e))

    return redirect(url_for('profile'))


@app.route('/statistics')
@login_required
@requires_roles('admin', 'staff')
def statistics():
    return render_template("statistics.html")
