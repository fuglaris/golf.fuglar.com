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
    SessionContext, IntegrityError, User, Company, Access, OAuth_User,
    GolfCourse, GolfCourseAccess
)


mod = Blueprint('golfcourse', __name__, url_prefix='/golfcourse')


@mod.before_request
def before_request():
    if current_user.role != 3:
        return redirect(url_for('index'))


@mod.route('/')
@mod.route('/<name>', methods=["GET"])
@login_required
def golfcourse(name=None):

    with SessionContext() as session:

        golfcourse = session.query(GolfCourse)\
            .filter_by(shortname=name.upper()).first()
        if not golfcourse:
            return redirect(url_for("index"))

        gcaccess = session.query(GolfCourseAccess)\
            .filter_by(user_id=current_user.id)\
            .filter_by(golfcourse_id=golfcourse.id).first()
        if not gcaccess:
            return redirect(url_for("index"))

        if request.method == 'GET':
            return render_template("golfcourse/index.html", golfcourse_name=name)


@mod.route('/<name>/usedcards', methods=["POST"])
@login_required
def usedcards(name=None):
    pass
