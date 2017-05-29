import os
import random
import string

from datetime import datetime, date
from app import app
from sqlalchemy import exc

from flask import (
    render_template, request, redirect, url_for, json, Blueprint
)
from flask_login import (
    current_user, login_required
)

from app.mail import send_mail
from app.decorators import requires_roles
from app.models import (
    SessionContext, IntegrityError, User, Company, Access, OAuth_User, QueryUnseenMessages,
    QueryUsers, Error,
    QueryError, QueryErrorWarning, GolfCourse, QueryGolfCourses, Card, QueryGolfCards
)


mod = Blueprint('admin', __name__, url_prefix='/admin')


@mod.route('/golfcourse_add/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def golfcourse_add(name):
    with SessionContext() as session:
        company = session.query(Company).filter_by(name=name).first()
        if not company:
            return redirect(url_for("main.index"))

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

    return redirect(url_for("admin.admin", name=name))


@mod.route('/golfcourse_delete/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def golfcourse_delete(name):
    with SessionContext() as session:
        try:
            company = session.query(Company).filter_by(name=name).first()
            if not company:
                return redirect(url_for("main.index"))

            golfcourse = session.query(GolfCourse)\
                .filter_by(shortname=request.form.get("shortname"))\
                .filter_by(company_id=company.id).first()

            if golfcourse:

                session.delete(golfcourse)
                session.commit()
        except exc.IntegrityError as e:
            pass

    return redirect(url_for("admin.admin", name=name))


@mod.route('/golfcard_add/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def golfcard_add(name):
    with SessionContext() as session:
        try:
            company = session.query(Company).filter_by(name=name).first()
            if not company:
                return redirect(url_for("main.index"))

            golfcourse = session.query(GolfCourse)\
                .filter_by(shortname=request.form.get("shortname"))\
                .filter_by(company_id=company.id).first()

            if not golfcourse:
                return redirect(url_for("main.index"))

            golfcard = Card(company_id=company.id, golfcourse_id=golfcourse.id, number=request.form.get("number"))

            session.add(golfcard)
            session.commit()


        except Exception as e:
            pass

    return redirect(url_for("admin.admin", name=name))


@mod.route('/golfcard_delete/<name>', methods=["POST"])
@login_required
@requires_roles('admin')
def golfcard_delete(name):
    with SessionContext() as session:
        try:
            company = session.query(Company).filter_by(name=name).first()
            if not company:
                return redirect(url_for("main.index"))

            golfcourse = session.query(GolfCourse)\
                .filter_by(shortname=request.form.get("shortname"))\
                .filter_by(company_id=company.id).first()

            if not golfcourse:
                return redirect(url_for("main.index"))

            golfcard = session.query(Card).filter_by(company_id=company.id)\
                .filter_by(golfcourse_id=golfcourse.id)\
                .filter_by(number=request.form.get("number")).first()

            session.delete(golfcard)
            session.commit()


        except Exception as e:
            pass

    return redirect(url_for("admin.admin", name=name))
