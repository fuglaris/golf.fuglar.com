from app import constants as const
from app import app
from flask import current_app
from datetime import datetime
from flask_login import current_user

import sys
import platform

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import Table, Column, Integer, String, Float, Date, DateTime,\
    Sequence, Boolean, UniqueConstraint, ForeignKey, PrimaryKeyConstraint,\
    BigInteger, Text
from sqlalchemy.exc import SQLAlchemyError as SqlError
from sqlalchemy.exc import IntegrityError as SqlIntegrityError
from sqlalchemy.exc import DataError as SqlDataError
from sqlalchemy import desc as SqlDesc
from sqlalchemy.dialects.postgresql import UUID as psql_UUID

from datetime import date, datetime

#hashing algorithm
from flask_argon2 import Argon2
argon2 = Argon2(app)

# Create the SQLAlchemy ORM Base class
Base = declarative_base()

# Allow client use of IntegrityError exception without importing it from sqlalchemy
IntegrityError = SqlIntegrityError
DatabaseError = SqlError
DataError = SqlDataError
# Same for the desc() function
desc = SqlDesc


class DB_Connection:

    def __init__(self):

        conn_str = current_app.config['DATABASE_URI']
        self._engine = create_engine(conn_str)
        # Create a Session class bound to this engine
        self._Session = sessionmaker(bind=self._engine)

    def create_tables(self):
        """ Create all missing tables in the database """
        Base.metadata.create_all(self._engine)

    def drop_tables(self):
        """ drop all tables in the database """
        Base.metadata.drop_all(self._engine)

    def execute(self, sql, **kwargs):
        """ Execute raw SQL directly on the engine """
        return self._engine.execute(sql, **kwargs)

    @property
    def session(self):
        """ Returns a freshly created Session instance from the sessionmaker """
        return self._Session()


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class SessionContext:

    _db = None

    @classproperty
    def db(cls):
        if cls._db is None:
            cls._db = DB_Connection()
        return cls._db

    def __init__(self, session=None, commit=False):

        if session is None:
            db = self.db
            self._new_session = True
            self._session = db.session
            self._commit = commit
        else:
            self._new_session = False
            self._session = db.session
            self._commit = False

    def __enter__(self):
        return self._session

    def __exit__(self, exc_type, ext_value, traceback):
        if self._new_session:
            if self._commit:
                if exc_type is None:
                    self._session.commit()
                else:
                    self._session.rollback()
            self._session.close()
        return False


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    displayname = Column(String)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    company = Column(String)
    role = Column(Integer)
    registered_on = Column(DateTime)
    max_cards = Column(Integer)

    def __init__(self, name, password, company, email, role=const.USER):
        self.name = name
        if name:
            self.displayname = name.split(" ")[0][:10]
        else:
            self.displayname = "---"
        self.password = argon2.generate_password_hash(password)
        self.email = email
        self.company = company
        self.role = role
        self.registered_on = datetime.utcnow()
        self.max_cards = 30

    def check_password(self, password):
        try:
            return argon2.check_password_hash(self.password, password)
        except Exception as e:
            print(e)
            return False

    def update_password(self, password):
        self.password = argon2.generate_password_hash(password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_role(self):
        return const.ROLE[self.role]

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return 'User(name={name})'.format(name=self.name)


class OAuth_User(Base):
    __tablename__ = 'oauth_users'
    id = Column(Integer, primary_key=True)
    provider_id = Column(BigInteger)
    user_id = Column(Integer, ForeignKey('users.id'))
    provider = Column(String)
    email = Column(String, index=True)

    def __init__(self, provider_id, user_id, provider, email):
        self.provider_id = provider_id
        self.user_id = user_id
        self.provider = provider
        self.email = email


class Error(Base):
    __tablename__ = 'errors'
    id = Column(Integer, primary_key=True)
    location = Column(Text)
    error_message = Column(Text)
    current_user_id = Column(Integer)
    warning = Column(Boolean)
    date = Column(DateTime)

    def __init__(self, location, error_message, current_user_id, warning=False):
        self.location = location
        self.error_message = error_message
        self.current_user_id = current_user_id
        self.warning = warning
        self.date = datetime.utcnow()


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    message = Column(Text)
    date = Column(DateTime)

    def __init__(self, message, title):
        self.message = message
        self.title = title
        self.date = datetime.utcnow()


class Message_Seen(Base):
    __tablename__ = 'messages_seen'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message_id = Column(Integer, ForeignKey('messages.id'))

    __table_args__ = (
        UniqueConstraint('user_id', 'message_id'),
    )

    def __init__(self, user_id, message_id):
        self.user_id = user_id
        self.message_id = message_id


class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __init__(self, name):
        self.name = name


class Access(Base):
    __tablename__ = 'access'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'company_id'),
    )

    def __init__(self, user_id, company_id):
        self.user_id = user_id
        self.company_id = company_id


class CompanyAccess(Base):
    __tablename__ = 'companiesaccess'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'company_id'),
    )

    def __init__(self, user_id, company_id):
        self.user_id = user_id
        self.company_id = company_id


class GolfCourseAccess(Base):
    __tablename__ = 'golfcoursesaccess'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    golfcourse_id = Column(Integer, ForeignKey('golfcourses.id'), index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'golfcourse_id'),
    )

    def __init__(self, user_id, golfcourse_id):
        self.user_id = user_id
        self.golfcourse_id = golfcourse_id


class GolfCourse(Base):
    __tablename__ = 'golfcourses'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    shortname = Column(String, index=True)
    color = Column(String, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)

    __table_args__ = (
        UniqueConstraint('name', 'shortname', 'company_id'),
    )

    def __init__(self, name, shortname, color, company_id):
        self.name = name
        self.shortname = shortname
        self.color = color
        self.company_id = company_id


class GolfCourseCompany(Base):
    # This table shows with companies the golfcourse has access to

    __tablename__ = 'golfcoursescompanies'

    id = Column(Integer, primary_key=True)
    golfcourse_id = Column(Integer, ForeignKey('golfcourses.id'), index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)

    __table_args__ = (
        UniqueConstraint('golfcourse_id', 'company_id'),
    )

    def __init__(self, golfcourse_id, company_id):
        self.golfcourse_id = golfcourse_id
        self.company_id = company_id


class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), index=True)
    golfcourse_id = Column(Integer, ForeignKey('golfcourses.id'), index=True)
    number = Column(Integer, index=True)

    __table_args__ = (
        UniqueConstraint('company_id', 'golfcourse_id', 'number'),
    )

    def __init__(self, company_id, golfcourse_id, number):
        self.company_id = company_id
        self.golfcourse_id = golfcourse_id
        self.number = number


class UsedCard(Base):
    __tablename__ = 'usedcards'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    card_id = Column(Integer, ForeignKey('cards.id'))
    date = Column(Date)
    date_registered = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('card_id', 'date'),
    )

    def __init__(self, user_id, card_id, date):
        self.user_id = user_id
        self.card_id = card_id
        self.date = date.date()
        self.date_registered = datetime.now()


class DeletedUsedCard(Base):
    __tablename__ = 'deletedusedcards'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    card_id = Column(Integer, ForeignKey('cards.id'))
    date = Column(Date)
    date_registered = Column(DateTime)
    date_deleted = Column(DateTime)

    def __init__(self, user_id, card_id, date_on, date_registed):
        self.user_id = user_id
        self.card_id = card_id
        self.date = date_on
        self.date_registered = date_registed
        self.date_deleted = datetime.now()


class _BaseQuery:

    def __init__(self):
        pass

    def execute(self, session, **kwargs):
        """ Execute the query and return the result from fetchall() """
        results = session.execute(text(self._Q), kwargs)
        columns = results.keys()
        for result in results.fetchall():
            yield dict(zip(columns, result))
        #return results.fetchall()

    def scalar(self, session, **kwargs):
        """ Execute the query and return the result from scalar() """
        return session.scalar(text(self._Q), kwargs)


class QueryUnseenMessages(_BaseQuery):

    _Q = """
        SELECT m.title, m.message
        FROM message m
        WHERE m.id NOT IN (SELECT ms.message_id
                           FROM message_seen ms
                           WHERE ms.user_id = :userId)
    """


class QueryUsers(_BaseQuery):

    _Q = """
        SELECT u.id, u.name, u.email, c.name as company, u.role, count_cards_left(u.id, extract(year from now())::integer) as cards_left, max_cards
        FROM users u
        LEFT OUTER JOIN access a
        ON a.user_id = u.id
        LEFT OUTER JOIN companies c
        ON a.company_id = c.id
    """

class QueryErrorWarning(_BaseQuery):

    _Q = """
        SELECT id, location, date, error_message
        FROM errors
        WHERE warning = true
    """

class QueryError(_BaseQuery):

    _Q = """
        SELECT id, location, date, error_message
        FROM errors
        WHERE warning = false
    """


class QueryGolfCourses(_BaseQuery):

    _Q = """
        SELECT id, name, shortname, color
        FROM golfcourses
        WHERE company_id = :company_id
    """


class QueryGolfCards(_BaseQuery):

    _Q = """
        SELECT c.id, gc.shortname, c.number, gc.color
        FROM cards c
        JOIN golfcourses gc
        ON c.golfcourse_id = gc.id
        WHERE c.company_id = :company_id
    """

class QueryCompanyGolfCards(_BaseQuery):

    _Q = """
        SELECT c.id, gc.shortname, c.number, gc.color
        FROM cards c
        JOIN golfcourses gc
        ON c.golfcourse_id = gc.id
        WHERE c.company_id = :company_id
          AND c.golfcourse_id = :golfcourse_id
    """


class QueryUsedCards(_BaseQuery):

    _Q = """
        SELECT u.displayname, gc.shortname, gc.color, uc.date, uc.id, c.number
        FROM usedcards uc
        JOIN cards c
        ON uc.card_id = c.id
        JOIN golfcourses gc
        ON c.golfcourse_id = gc.id
        JOIN users u
        ON uc.user_id = u.id
        WHERE c.company_id in (
            SELECT company_id
            FROM access
            WHERE user_id = :user_id)
    """


class QueryGolfCourseUsedCards(_BaseQuery):

    _Q = """
        SELECT u.displayname, gc.shortname, gc.color, uc.date, uc.id, c.number
        FROM usedcards uc
        JOIN cards c
        ON uc.card_id = c.id
        JOIN golfcourses gc
        ON c.golfcourse_id = gc.id
        JOIN users u
        ON uc.user_id = u.id
        WHERE c.golfcourse_id in (
            SELECT golfcourse_id
            FROM golfcoursesaccess
            WHERE user_id = :user_id
        )
    """


class QueryAvailibleCards(_BaseQuery):

    _Q = """
        SELECT c.id, gc.shortname, c.number
        FROM cards c
        JOIN golfcourses gc
        ON c.golfcourse_id = gc.id
        WHERE c.company_id in (
            SELECT company_id
            FROM access
            WHERE user_id = :user_id)
          AND c.id not in (
            SELECT card_id
            FROM usedcards
            WHERE date = :date)
          AND check_card_availability(:user_id, :date)
          AND check_golfcourse_availability(:user_id, gc.id, :date)
    """


class QueryCardInfo(_BaseQuery):

    _Q = """
        SELECT u.name as username, gc.name as coursename, uc.date, c.number, uc.id
        FROM usedcards uc
        JOIN cards c
        ON uc.card_id = c.id
        JOIN golfcourses gc
        ON c.golfcourse_id = gc.id
        JOIN users u
        ON uc.user_id = u.id
        WHERE uc.id = :card_id
          AND c.company_id in (
              SELECT company_id
              FROM access
              WHERE user_id = :user_id)
    """


class QueryNumberOfGolfcourses_By_CardIds(_BaseQuery):

    _Q = """
        SELECT count(1)
        FROM (
            SELECT golfcourse_id
            FROM cards
            WHERE id  = ANY(:ids)
            GROUP BY golfcourse_id) a
    """

class QueryNumberOfCardsLeft(_BaseQuery):

    _Q = """
        SELECT count_cards_left(:user_id, :year) cnt
    """



class QueryStatisticsCardsUsed(_BaseQuery):

    _Q = """
        select g.shortname, g.color, array_agg(to_char(d.date, 'Mon') ORDER BY d.date) months, array_agg(coalesce(total, 0) ORDER BY d.date) totals
        from golfcourses g
        cross join generate_series(date_trunc('year', :date) + interval '4 month', date_trunc('year', :date) + interval '9 months', '1 month') as d(date)
        left join (
            select date_trunc('month', date) as date, g.id as golfcourse_id, count(1) as total
            from usedcards uc
            join cards c on uc.card_id = c.id
            join golfcourses g on c.golfcourse_id = g.id
            where date_trunc('year', uc.date) = date_trunc('year', :date)
            group by 1, 2
        ) data
        on g.id = data.golfcourse_id
        and d.date = data.date
        GROUP BY 1,2
    """

class QueryStatisticsCardsUsedByUser(_BaseQuery):

    _Q = """
        WITH all_cards as (
            SELECT u.id as user_id,
                u.name as user_name,
                gc.name as golfcourse_name,
                gc.color,
                coalesce(ucc.total, 0) as total,
                sum(coalesce(ucc.total, 0)) over (partition by u.id) as user_total
            FROM golfcourses gc
            CROSS JOIN users u
            LEFT JOIN (
                SELECT uc.user_id, c.golfcourse_id, count(1) as total
                FROM usedcards uc
                        JOIN cards c on uc.card_id = c.id
                WHERE date_trunc('year', uc.date) = date_trunc('year', :date)
                GROUP BY 1, 2
            ) ucc
            ON gc.id = ucc.golfcourse_id
            AND u.id = ucc.user_id
        )
        SELECT golfcourse_name, color,
            array_agg(total ORDER BY user_total, user_name) AS totals,
            array_agg(user_name ORDER BY user_total, user_name) as names
        FROM (select * from all_cards order by user_total) a
        WHERE user_total > 0
        GROUP BY 1,2
    """