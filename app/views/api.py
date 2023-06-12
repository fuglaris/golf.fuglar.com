import os
import random
import string

from datetime import datetime, date
from app import app
from sqlalchemy import exc

from flask import (
    request, jsonify, Blueprint
)
from flask_login import (
    current_user, login_required
)

from app.constants import BadRequestError
from app.logging import logger, logg_error
from app.mail import send_mail
from app.oauth import OAuthSignIn
from app.models import (
    SessionContext, User, QueryAvailibleCards, QueryUsedCards, UsedCard, QueryCardInfo,
    Error, Card, DeletedUsedCard, QueryGolfCourseUsedCards, QueryNumberOfGolfcourses_By_CardIds
)
from app.decorators import (
    validate_json, validate_login, validate_registration, validate_provider, my_logger,
    is_logged_in, requires_roles
)


mod = Blueprint('api', __name__, url_prefix='/api')

@mod.route('/availiblecards')
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

        print(query)
        for q in query:
            print(q, q.keys())
            return_obj.append(dict(q))

        return jsonify(return_obj)


@mod.route('/usedcards')
@login_required
def api_used_cards():

    with SessionContext() as session:
        qUC = QueryUsedCards()
        return_obj = list()
        query = qUC.execute(session=session, user_id=current_user.id)
        for q in query:
            return_obj.append(dict(q))

        return jsonify(return_obj)


@mod.route('/usecards')
@login_required
def api_use_cards():

    if not request.args.get("dateid"):
        return jsonify(dict(error="1", title="Ekki tókst að skrá kort", message="Ekkert kort valið."))

    qNGC = QueryNumberOfGolfcourses_By_CardIds()

    with SessionContext() as session:
        try:
            dags = datetime.strptime(request.args.get("dateid"),"%Y%m%d")

            data = qNGC.scalar(session=session, ids=[int(i) for i in request.args.getlist('id')])
            
            if data > 1:
                return jsonify(dict(error="1", title="Ekki tókst að skrá kort", message="Ekki má velja kort frá fleirri en einum golfvelli í einu."))

            for i in request.args.getlist('id'):
                mdl_card = UsedCard(user_id=current_user.id, card_id=i, date=dags)

                session.add(mdl_card)

            session.commit()

        except Exception as e:
            print(e)
            session.rollback()
            logg_error(location="api/usecards", error=str(e))
            return jsonify(dict(error="1", title="Ekki tókst að skrá kort", message="Villa kom upp við að skrá kort, vinsamlegst hafið samband við palmar@fuglar.com"))

    return jsonify(dict(error="0", title="Kort skráð",message="{count} kort var skráð á þig dags: {date}"\
        .format(count=len(request.args.getlist('id')), date=dags.date())))


@mod.route('/cardinfo')
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


@mod.route('/deletecard')
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


@mod.route('/golfcourse/usedcards')
@login_required
def api_golfcourse_used_cards():

    with SessionContext() as session:
        qUC = QueryUsedCards()
        return_obj = list()
        query = qUC.execute(session=session, user_id=current_user.id)
        for q in query:
            return_obj.append(dict(q))

        return jsonify(return_obj)
