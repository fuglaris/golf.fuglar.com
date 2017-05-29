import os
import random
import string

from datetime import datetime, date
from app import app
from sqlalchemy import exc

from flask import (
    render_template, request, redirect, url_for, json, Blueprint, jsonify
)
from flask_login import (
    current_user, login_required
)

from app.mail import send_mail
from app.decorators import requires_roles
from app.models import (
    SessionContext, IntegrityError, User, Company, Access, OAuth_User, GolfCourseCompany,
    GolfCourse, GolfCourseAccess, QueryGolfCourseUsedCards, QueryCompanyGolfCards
)


mod = Blueprint('golfcourse', __name__, url_prefix='/golfcourse')


@mod.before_request
def before_request():
    if current_user.role != 3:
        return redirect(url_for('main.index'))


@mod.context_processor
def utility_processor():
    with SessionContext() as session:

        gcaccess = session.query(GolfCourseAccess)\
            .filter_by(user_id=current_user.id).first()

        access = session.query(GolfCourseCompany.company_id)\
            .filter_by(golfcourse_id=gcaccess.golfcourse_id).all()

        if access:
            companies = session.query(Company).filter(Company.id.in_([company_id for company_id in access])).all()
        else:
            companies = None

        return dict(companies=companies)


@mod.route('', methods=["GET"])
@login_required
def golfcourse():

    with SessionContext() as session:
        company_name = request.args.get('company')

        gcaccess = session.query(GolfCourseAccess)\
            .filter_by(user_id=current_user.id).first()

        if not gcaccess:
            return redirect(url_for("golfcourse.noaccess"))

        golfcourse = session.query(GolfCourse)\
            .filter_by(id=gcaccess.golfcourse_id).first()

        if not golfcourse:
            return redirect(url_for("golfcourse.noaccess"))

        if company_name:
            qCGC = QueryCompanyGolfCards()

            company = session.query(Company).filter_by(name=company_name).first()

            if not company:
                return redirect(url_for("golfcourse.golfcourse"))

            return render_template("golfcourse/company.html",
                golfcourse_name=golfcourse.shortname.upper(),
                current_company=company_name,
                golfcards=qCGC.execute(session=session, company_id=company.id, golfcourse_id=golfcourse.id))

        if request.method == 'GET':
            return render_template("golfcourse/index.html", golfcourse_name=golfcourse.shortname.upper())


@mod.route('/usedcards', methods=["GET"])
@login_required
def usedcards(name=None):

    with SessionContext() as session:
        qUC = QueryGolfCourseUsedCards()
        return_obj = list()
        query = qUC.execute(session=session, user_id=current_user.id)
        for q in query:
            return_obj.append(dict(q))

        return jsonify(return_obj)

@mod.route('/NoAccess')
@login_required
def noaccess():
    return "User does not have access"
