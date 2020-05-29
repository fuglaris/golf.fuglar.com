import os
import random
import string
import json

from datetime import datetime, date

from sqlalchemy import exc

from flask import (
    render_template, request, redirect, url_for, Blueprint, session as flask_session
)
from flask_login import (
    login_user, logout_user, current_user, login_required, fresh_login_required
)

from app import app
from app.logging import logger, logg_error
from app.mail import send_mail
from app.oauth import OAuthSignIn
from app.models import (
    SessionContext, IntegrityError, User, Company, Access, OAuth_User, Error,
    QueryUsers, QueryErrorWarning, QueryError, QueryGolfCourses, QueryGolfCards,
    GolfCourseAccess, GolfCourse, QueryNumberOfCardsLeft, 
    QueryStatisticsCardsUsed, QueryStatisticsCardsUsedByUser
)
from app.decorators import (
    validate_login, validate_registration, validate_provider,
    is_logged_in, requires_roles
)


mod = Blueprint('main', __name__)


@mod.context_processor
def utility_processor():
    qCL = QueryNumberOfCardsLeft()

    with SessionContext() as session:
        try:
            cards_left = qCL.scalar(session=session, user_id=current_user.id, year='2018')
            if cards_left < 0:
                cards_left = 0
            access = session.query(Access.company_id).filter_by(user_id=current_user.id).all()
            if access:
                companies = session.query(Company).filter(Company.id.in_([company_id for company_id in access])).all()
            else:
                companies = None
        except AttributeError as e:
            # AttributeError is catched if current_user is not defined.
            print(str(e))
            companies = None
            cards_left = None

        return dict(companies=companies, cards_left=cards_left)


@mod.route('/')
@login_required
def index():
    return render_template("main/index.html")


@mod.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    # If request is GET, serve template for profile, otherwise its POST request
    if request.method == 'GET':
        return render_template("main/profile.html")

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

    return redirect(url_for('main.profile'))


@mod.route('/statistics')
@login_required
@requires_roles('admin', 'staff')
def statistics():

    with SessionContext() as session:

        year = request.args.get('year', date.today().year)

        today = date(int(year), 1, 1)

        qSCU = QueryStatisticsCardsUsed()
        qSCUbU = QueryStatisticsCardsUsedByUser()

        cardsused = [{ 'shortname': _[0], 'color': _[1], 'months': _[2], 'totals': _[3]} for _ in qSCU.execute(session=session, date=today)]
        cardsused_byuser = [{ 'golfcourse_name': _[0], 'color': _[1], 'totals': _[2], 'names': _[3]} for _ in qSCUbU.execute(session=session, date=today)]


        return render_template("main/statistics.html", cardsused = json.dumps(cardsused), cardsused_byuser = json.dumps(cardsused_byuser), year = year)


@mod.route('/c/<name>')
@login_required
@requires_roles('admin')
def company(name):
    with SessionContext() as session:

        flask_session['url_admin_page'] = url_for(request.endpoint, name=name)

        company = session.query(Company).filter_by(name=name).first()
        access = session.query(Access).filter_by(user_id=current_user.id)\
            .filter_by(company_id=company.id).first()

        if not access:
            return redirect(url_for("main.index"))

        qU = QueryUsers()
        qEW = QueryErrorWarning()
        qE = QueryError()
        qGC = QueryGolfCourses()
        qGCa = QueryGolfCards()

        return render_template("main/company.html",
            users=qU.execute(session=session),
            errorswarning=qEW.execute(session=session),
            errors=qE.execute(session=session),
            golfcourses=qGC.execute(session=session, company_id=company.id),
            golfcards=qGCa.execute(session=session, company_id=company.id),
            path=name)
