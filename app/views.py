from app import app
from app.models import (
    SessionContext,
    IntegrityError,
    User,
    Company,
    Access,
    OAuth_User,
    QueryUnseenMessages,
    QueryUsers,
    QueryAvailibleCards,
    QueryUsedCards,
    UsedCard,
    QueryCardInfo,
    Error,
    QueryError,
    QueryErrorWarning,
    GolfCourse,
    QueryGolfCourses,
    Card,
    QueryGolfCards,
    DeletedUsedCard
)
from app.constants import BadRequestError
from app.logging import Logger
from app.mail import send_mail

# Database exceptions
from sqlalchemy import exc

from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    json,
    jsonify,
    send_from_directory
)
from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required,
    fresh_login_required
)

from app.decorators import (
    validate_json,
    validate_login,
    validate_registration,
    validate_provider,
    my_logger,
    is_logged_in,
    requires_roles
)

from app.oauth import OAuthSignIn

from datetime import datetime, date
import random
import string
import os

logger = Logger()

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


@app.route('/')
@login_required
def index():
    return render_template("index.html")


@app.route('/settings')
@login_required
@fresh_login_required
def settings():
    return render_template("main/settings/settings.html")


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


@app.route('/admin/<name>')
@login_required
@requires_roles('admin')
def admin(name):
    with SessionContext() as session:
        company = session.query(Company).filter_by(name=name).first()
        access = session.query(Access).filter_by(user_id=current_user.id)\
            .filter_by(company_id=company.id).first()

        if not access:
            return redirect(url_for("index"))

        qU = QueryUsers()
        qEW = QueryErrorWarning()
        qE = QueryError()
        qGC = QueryGolfCourses()
        qGCa = QueryGolfCards()

    return render_template("admin.html",
        users=qU.execute(session=session),
        errorswarning=qEW.execute(session=session),
        errors=qE.execute(session=session),
        golfcourses=qGC.execute(session=session, company_id=company.id),
        golfcards=qGCa.execute(session=session, company_id=company.id),
        path=name)


@app.route('/admin_golfcourse_add/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def admin_golfcourse_add(name):
    with SessionContext() as session:
        company = session.query(Company).filter_by(name=name).first()
        if not company:
            return redirect(url_for("index"))

        golfcourse = session.query(GolfCourse)\
            .filter_by(shortname=request.form.get("shortname"))\
            .filter_by(company_id=company.id).first()

        if not golfcourse:
            golfcourse = GolfCourse(name=request.form.get("name"),
                shortname=request.form.get("shortname"),
                color=request.form.get("color"),
                company_id=company.id)
        else:
            if request.form.get("name"):
                golfcourse.name = request.form.get("name")
            if request.form.get("color"):
                golfcourse.color = request.form.get("color")

        session.add(golfcourse)
        session.commit()

    return redirect(url_for("admin", name=name))


@app.route('/admin_golfcourse_delete/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def admin_golfcourse_delete(name):
    with SessionContext() as session:
        try:
            company = session.query(Company).filter_by(name=name).first()
            if not company:
                return redirect(url_for("index"))

            golfcourse = session.query(GolfCourse)\
                .filter_by(shortname=request.form.get("shortname"))\
                .filter_by(company_id=company.id).first()

            if golfcourse:

                session.delete(golfcourse)
                session.commit()
        except exc.IntegrityError as e:
            pass

    return redirect(url_for("admin", name=name))


@app.route('/admin_golfcard_add/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def admin_golfcard_add(name):
    with SessionContext() as session:
        try:
            company = session.query(Company).filter_by(name=name).first()
            if not company:
                return redirect(url_for("index"))

            golfcourse = session.query(GolfCourse)\
                .filter_by(shortname=request.form.get("shortname"))\
                .filter_by(company_id=company.id).first()

            if not golfcourse:
                return redirect(url_for("index"))

            golfcard = Card(company_id=company.id, golfcourse_id=golfcourse.id, number=request.form.get("number"))

            session.add(golfcard)
            session.commit()


        except Exception as e:
            pass

    return redirect(url_for("admin", name=name))


@app.route('/admin_golfcard_delete/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def admin_golfcard_delete(name):
    with SessionContext() as session:
        try:
            company = session.query(Company).filter_by(name=name).first()
            if not company:
                return redirect(url_for("index"))

            golfcourse = session.query(GolfCourse)\
                .filter_by(shortname=request.form.get("shortname"))\
                .filter_by(company_id=company.id).first()

            if not golfcourse:
                return redirect(url_for("index"))

            golfcard = session.query(Card).filter_by(company_id=company.id)\
                .filter_by(golfcourse_id=golfcourse.id)\
                .filter_by(number=request.form.get("number")).first()

            session.delete(golfcard)
            session.commit()


        except Exception as e:
            pass

    return redirect(url_for("admin", name=name))

@app.route('/statistics')
@login_required
@requires_roles('admin', 'staff')
def statistics():
    return render_template("statistics.html")


@app.route('/login', methods=['GET', 'POST'])
@is_logged_in
@validate_login
def login():
    """ Loggs user in, if user exists this redirects to index
        otherwise it redirects back to login """

    if request.method == 'GET':
        return render_template("login/login.html")

    with SessionContext(commit=True) as session:
        try:
            registerd_user = session.query(User)\
                                    .filter_by(email=request.form['email'])\
                                    .first()

            # If user does not exist, redirect to login with status message.
            if not registerd_user:
                logger.login_failed_user(request.form.get('email'))
                logg_error(location="login", error="Logged in with email that does not exist in database, {email}".format(email=request.form.get('email')), warning=True)
                return render_template("login/login.html", status='user_does_not_exist')

            # If user password is incorrect, redirect to login with status message
            if not registerd_user.check_password(password=request.form.get('password')):
                logger.login_failed_password(request.form.get('email'))
                logg_error(location="login", error="Logged in with incorrect password {email}".format(email=request.form.get('email')), warning=True)
                return render_template("login/login.html", status='wrong_password')

            remember_me = request.form.get('remember_me') is not None
            login_user(registerd_user, remember=remember_me)
            logger.login_successful(request.form.get('email'))
        except Exception as e:
            session.rollback()
            logg_error(location='login', error=str(e))
            return redirect(url_for('index'))

        return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
@is_logged_in
@validate_registration
def register():
    """ Registers a user.
        Redirects to login """

    if request.method == 'GET':
        return render_template("login/register.html")

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
            return render_template("login/register.html",
                                   status='user_already_exists')
        except Exception as e:
            sesison.rollback()
            logg_error(location='register', error=str(e))
            return render_template("login/register.html",
                                   status='error in registry')

        company = session.query(Company).filter_by(name='Fuglar').first()
        access = Access(user_id=user.id, company_id=company.id)
        session.add(access)
        session.commit()

        logger.register_successful(request.form.get('email'))
        send_mail(request.form['email'])
        login_user(user, remember=False)
        return redirect(url_for('login'))


@app.route('/authorize/<provider>')
@validate_provider
def oauth_authorize(provider):
    """ Used to call login provider """
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
@validate_provider
def oauth_callback(provider):
    """ Loggs in a user if he exists, else it tries to register the user.
        Allways redirects to index """

    if not current_user.is_anonymous:
        return redirect(url_for('index'))

    oauth = OAuthSignIn.get_provider(provider)
    id, email, name = oauth.callback()
    if email is None:
        logg_error(location='oauth_callback-{provider}'.format(provider=provider), error="No email supplied from provider, id: {id}, name: {name}".format(id=id, name=name))
        return redirect(url_for('index'))

    with SessionContext() as session:
        oauth_user = session.query(OAuth_User)\
                            .filter_by(email=email, provider=provider)\
                            .first()

        if not oauth_user:
            try:
                user = User(name=name,
                            password=''.join(random.choice(string.ascii_uppercase + string.digits + " ") for _ in range(100)),
                            company='',
                            email=email)
                session.add(user)
                session.commit()
                oUser = OAuth_User(provider_id=id,
                                   user_id=user.get_id(),
                                   provider=provider,
                                   email=email)
                session.add(oUser)
                session.commit()
                send_mail(id)
                logger.oauth_register_successful(email)

                company = session.query(Company).filter_by(name='Fuglar').first()
                access = Access(user_id=user.id, company_id=company.id)
                session.add(access)
                session.commit()


            except Exception as e:
                logger.oauth_register_failed(email)
                session.rollback()
                logg_error(location='oauth_callback-{provider}'.format(provider=provider), error=str(e))
                try:
                    session.delete(user)
                    session.commit()
                except UnboundLocalError:
                    pass
                return redirect(url_for('index'))
        else:
            user = session.query(User).filter_by(id=oauth_user.user_id).first()
            logger.oauth_login_successful(email)


        login_user(user, remember=True)
        return redirect(url_for('index'))

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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


""" REMEMBER
have
@login_manager.needs_refresh_handler
decorator in actions that are sensitive, like changing password
"""


@app.route('/api/availiblecards')
@login_required
def api_availible_cards():
    if not request.args.get('dateid'):
        logg_error(location="api/availiblecards", error="no dateid supplied")
        return jsonify(dict(error="1"))

    if len(request.args.get('dateid')) != 8:
        logg_error(location="api/availiblecards", error="dateid length is not 8")
        return jsonify(dict(error="1"))

    try:
        int(request.args.get('dateid'))
    except ValueError:
        logg_error(location="api/availiblecards", error="dateid contains string values: {val}".format(val=request.args.get('dateid')))
        return jsonify(dict(error="1"))

    with SessionContext() as session:
        qAC = QueryAvailibleCards()
        return_obj = list()
        query = qAC.execute(session=session,
            user_id=current_user.id,
            date=datetime.strptime(request.args.get('dateid'), "%Y%m%d").date())
        for q in query:
            return_obj.append(dict(q))

        return jsonify(return_obj)


@app.route('/api/usedcards')
@login_required
def api_used_cards():

    with SessionContext() as session:
        qUC = QueryUsedCards()
        return_obj = list()
        query = qUC.execute(session=session, user_id=current_user.id)
        for q in query:
            return_obj.append(dict(q))

        return jsonify(return_obj)


@app.route('/api/usecards')
@login_required
def api_use_cards():

    if not request.args.get("dateid"):
        return jsonify(dict(error="1", title="Ekki tókst að skrá kort", message="Ekkert kort valið."))


    with SessionContext() as session:
        try:
            dags = datetime.strptime(request.args.get("dateid"),"%Y%m%d")
            for i in request.args.getlist('id'):
                mdl_card = UsedCard(user_id=current_user.id, card_id=i, date=dags)

                session.add(mdl_card)

            session.commit()

        except Exception as e:
            session.rollback()
            logg_error(location="api/usecards", error=str(e))
            return jsonify(dict(error="1", title="Ekki tókst að skrá kort", message="Villa kom upp við að skrá kort, vinsamlegst hafið samband við palmar@fuglar.com"))

    return jsonify(dict(error="0", title="Kort skráð",message="{count} kort var skráð á þig dags: {date}"\
        .format(count=len(request.args.getlist('id')), date=dags.date())))


@app.route('/api/cardinfo')
@login_required
def api_cardinfo():
    with SessionContext() as session:
        qCI = QueryCardInfo()
        return_obj = list()
        query = qCI.execute(session=session,
            card_id=request.args.get("id"),
            user_id=current_user.id)
        for q in query:
            return_obj.append(dict(q))

        return jsonify(return_obj)


@app.route('/api/deletecard')
@login_required
def api_deletecard():
    with SessionContext() as session:
        try:
            card = session.query(UsedCard)\
                .filter_by(id=request.args.get("id"))\
                .filter_by(user_id=current_user.id)\
                .first()

            if not card:
                return jsonify(dict(error="1", title="Ekki tókst að eyða korti", message="Kortið er ekki skráð á þig."))

            if card.date < date.today():
                return jsonify(dict(error="1", title="Ekki tókst að eyða korti", message="Ekki er hægt að eyða korti á dagsetningu sem er þegar liðin."))

            deletedcard = DeletedUsedCard(user_id=card.user_id, card_id=card.card_id, date_on=card.date, date_registed=card.date_registered)
            session.add(deletedcard)
            session.commit()

            session.delete(card)
            session.commit()

            return jsonify(dict(error="0", title="Korti eytt", message=""))
        except Exception as e:
            session.rollback()
            logg_error(location="api/deletecard", error=str(e))
            return jsonify(dict(error="1", title="Ekki tókst að eyða korti", message="Villa kom upp við að eyða korti, vinsamlegst hafið samband við palmar@fuglar.com"))
