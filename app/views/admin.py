import os
import random
import string

from datetime import datetime, date
from app import app
from sqlalchemy import exc

from flask import (
    render_template, request, redirect, url_for, json, Blueprint, session as flask_session
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


def get_random_alphaNumeric_string(stringLength=8):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))



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




@mod.route("/reset_password", methods=["POST"])
@login_required
@requires_roles('admin')
def reset_password():

    user_id = request.form["user_id"]
    name = request.form["name"]
    email = request.form["email"]

    with SessionContext() as session:

        try:
            user = session.query(User)\
                .filter_by(id = user_id)\
                .filter_by(name = name)\
                .filter_by(email = email)\
                .first()
        except Exception:
            user = None

        if not user:
            return render_template("main/admin/password_reset.html", error="Notandi finnst ekki.", cards_left = 0)

        oauth = session.query(OAuth_User)\
            .filter_by(user_id = user.id)\
            .first()

        if oauth:
            return render_template("main/admin/password_reset.html", error="Notandi er skráður inn með facebook eða google.", cards_left = 0)


        password = get_random_alphaNumeric_string(40)
        user.update_password(password)
        session.add(user)
        session.commit()

        return render_template("main/admin/password_reset.html", user_id = user_id, name = name, email = email, password = password, cards_left = 0)




@mod.route("/update_card_count", methods=["POST"])
@login_required
@requires_roles('admin')
def update_card_count():

    user_id = request.form["user_id"]
    count = request.form["count"]

    with SessionContext() as session:

        try:
            user = session.query(User)\
                .filter_by(id = user_id)\
                .first()

            user.max_cards = int(count)
            session.add(user)
            session.commit()
        except Exception as e:
            print(str(e))

    return redirect(flask_session['url_admin_page'])
