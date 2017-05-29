import os.path
import datetime

from app import app

from app.models import (
    DB_Connection,
    SessionContext,
    User,
    OAuth_User
)

with app.app_context():
    app.config.from_object('config.ProductionConfig')


    tmp = DB_Connection()
    tmp.create_tables()

    """ Import base user to database """
    """
    with SessionContext() as session:
        try:
            user = User(
                name='Pálmar Gíslason',
                password='stuff',
                company='Fuglar',
                email='palmar08@nff.is',
                role=0
            )
            session.add(user)
            session.commit()

            oauthuser = OAuth_User(
                provider_id=10209723454195190,
                user_id=user.id,
                provider='facebook',
                email='palmar08@nff.is',
            )
            session.add(oauthuser)
            session.commit()
        except Exception as e:
            print("Already exists")
    """
