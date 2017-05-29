import os
import random
import string

from datetime import datetime, date
from app import app
from sqlalchemy import exc

from flask import (
    render_template, request, redirect, url_for, Blueprint
)
from flask_login import (
    login_user, logout_user, current_user, login_required, fresh_login_required
)

from app.logging import logger, logg_error
from app.mail import send_mail
from app.oauth import OAuthSignIn
from app.models import (
    SessionContext, IntegrityError, User, Company, Access, OAuth_User, Error
)
from app.decorators import (
    validate_login, validate_registration, validate_provider,
    is_logged_in, requires_roles
)

mod = Blueprint('auth', __name__)


@mod.route('/login', methods=['GET', 'POST'])
@is_logged_in
@validate_login
def login():
    """ Loggs user in, if user exists this redirects to index
        otherwise it redirects back to login """

    if request.method == 'GET':
        return render_template("auth/login.html")

    with SessionContext(commit=True) as session:
        try:
            registerd_user = session.query(User)\
                                    .filter_by(email=request.form['email'])\
                                    .first()

            # If user does not exist, redirect to login with status message.
            if not registerd_user:
                logger.login_failed_user(request.form.get('email'))
                logg_error(location="login", error="Logged in with email that does not exist in database, {email}".format(email=request.form.get('email')), warning=True)
                return render_template("auth/login.html", status='user_does_not_exist')

            # If user password is incorrect, redirect to login with status message
            if not registerd_user.check_password(password=request.form.get('password')):
                logger.login_failed_password(request.form.get('email'))
                logg_error(location="login", error="Logged in with incorrect password {email}".format(email=request.form.get('email')), warning=True)
                return render_template("auth/login.html", status='wrong_password')

            remember_me = request.form.get('remember_me') is not None
            login_user(registerd_user, remember=remember_me)
            logger.login_successful(request.form.get('email'))
        except Exception as e:
            session.rollback()
            logg_error(location='login', error=str(e))
            return redirect(url_for('main.index'))

        return redirect(url_for('main.index'))


@mod.route('/register', methods=['GET', 'POST'])
@is_logged_in
@validate_registration
def register():
    """ Registers a user.
        Redirects to login """

    if request.method == 'GET':
        return render_template("auth/register.html")

    with SessionContext() as session:
        try:
            user = User(name=request.form['name'],
                        password=request.form['password'],
                        company=request.form['company'],
                        email=request.form['email'])

            session.add(user)
            session.commit()
        except exc.IntegrityError as e:
            session.rollback()
            logger.register_failed(request.form.get('email'))
            logg_error(location='register', error="Tried to register with email that already exists in database {email}".format(email=request.form.get('email')), warning=True)
            return render_template("auth/register.html",
                                   status='user_already_exists')
        except Exception as e:
            sesison.rollback()
            logg_error(location='register', error=str(e))
            return render_template("auth/register.html",
                                   status='error in registry')

        company = session.query(Company).filter_by(name='Fuglar').first()
        access = Access(user_id=user.id, company_id=company.id)
        session.add(access)
        session.commit()

        logger.register_successful(request.form.get('email'))
        send_mail(request.form['email'])
        login_user(user, remember=False)
        return redirect(url_for('auth.login'))


@mod.route('/authorize/<provider>')
@validate_provider
def oauth_authorize(provider):
    """ Used to call login provider """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@mod.route('/callback/<provider>')
@validate_provider
def oauth_callback(provider):
    """ Loggs in a user if he exists, else it tries to register the user.
        Allways redirects to index """

    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    oauth = OAuthSignIn.get_provider(provider)
    id, email, name = oauth.callback()
    if email is None:
        logg_error(location='oauth_callback-{provider}'.format(provider=provider), error="No email supplied from provider, id: {id}, name: {name}".format(id=id, name=name))
        return redirect(url_for('main.index'))

    with SessionContext() as session:

        if provider == 'facebook':
            oauth_user = session.query(OAuth_User)\
                                .filter_by(provider_id=id, provider=provider)\
                                .first()
        else:
            oauth_user = session.query(OAuth_User)\
                                .filter_by(email=email, provider=provider)\
                                .first()


        print(oauth_user)

        if not oauth_user:
            try:
                objs = list()
                user = User(name=name,
                            password=''.join(random.choice(string.ascii_uppercase + string.digits + " ") for _ in range(100)),
                            company='',
                            email=email)
                session.add(user)
                session.commit()
                objs.append(user)
                oUser = OAuth_User(provider_id=id,
                                   user_id=user.get_id(),
                                   provider=provider,
                                   email=email)
                session.add(oUser)
                session.commit()
                objs.append(oUser)
                send_mail(id)
                logger.oauth_register_successful(email)

                company = session.query(Company).filter_by(name='Fuglar').first()
                access = Access(user_id=user.id, company_id=company.id)
                session.add(access)
                session.commit()
                objs.append(access)


            except Exception as e:
                logger.oauth_register_failed(email)
                session.rollback()
                logg_error(location='oauth_callback-{provider}'.format(provider=provider), error=str(e))
                try:
                    for ob in objs[::-1]:
                        session.delete(ob)
                        session.commit()
                except UnboundLocalError:
                    pass
                return redirect(url_for('main.index'))
        else:
            user = session.query(User).filter_by(id=oauth_user.user_id).first()
            logger.oauth_login_successful(email)


        login_user(user, remember=True)
        return redirect(url_for('main.index'))

'''
@app.route("/reauthenticate", methods=["GET", "POST"])
@login_required
def reauth():
    # if the session is `fresh` just redirect to the page the user has requested
    if not login_fresh():
        form = LoginForm()
        if form.validate_on_submit():
            # do password check here
            confirm_login()
            return redirect(url_for("index"))
        return render_template("reauth.html", form=form)
    return redirect(request.args.get("next") or url_for("index"))
'''


@mod.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


""" REMEMBER
have
@login_manager.needs_refresh_handler
decorator in actions that are sensitive, like changing password
"""
