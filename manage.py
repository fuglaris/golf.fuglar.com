import sys
import gc
import getopt
import time
import os
from config import basedir

from app.models import *

class Usage(Exception):

    def __init__(self, msg):
        self.msg = msg

__doc__ = """usage: Perform database migrations

positional arguments:
upgrade             Upgrade to a later version
migrate             Alias for 'revision --autogenerate'
current             Display the current revision for each database.

init                Generates a new migration
downgrade           Revert to a previous version
history             List changeset scripts in chronological order.\

optional arguments:
-h, --help            show this help message and exit
"""



db = SessionContext.db

class Migrate_Version(Base):
    __tablename__ = 'migrate_version'
    id = Column(Integer, primary_key=True)
    version = Column(Integer, unique=True)
    script = Column(String)
    date = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('version', 'script'),
    )

    def __init__(self, version, script):
        self.version = version
        self.script = script
        self.date = datetime.utcnow()

    def __repr__(self):
        return "{script} <{version}>".format(script=self.script, version=self.version)


class _BaseQuery:

    def __init__(self):
        pass

    def execute(self, session, **kwargs):
        """ Execute the query and return the result from fetchall() """
        return session.execute(self._Q, kwargs).fetchall()

    def scalar(self, session, **kwargs):
        """ Execute the query and return the result from scalar() """
        return session.scalar(self._Q, kwargs)


class QueryMigrateVersion(_BaseQuery):

    _Q = """
        SELECT MAX(version)
        FROM migrate_version
    """

class QueryMigrateVersionHistory(_BaseQuery):

    _Q = """
        SELECT version, script, date
        FROM migrate_version
        ORDER BY date
    """


def read_script(version):
    script_name = "{:03d}script.sql".format(version)
    f = open(os.path.join(basedir, "migrations/{script}".format(script=script_name)))
    return f.read(), script_name


def main(argv=None):
    """ Guido van Rossum's pattern for a Python main function """

    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hiudvmct",
                         ["help", "init", "upgrade", "downgrade", "version", "migrate", "current", "drop_all", "test"])
        except getopt.error as msg:
            raise Usage(msg)
        init = False
        urls = None

        # Process options
        for o, a in opts:
            if o in ("-h", "--help"):
                print(__doc__)
                sys.exit(0)

            elif o in ('--drop_all'):
                try:
                    db.drop_tables()
                except Exception as e:
                    print(e)
            elif o in ("-i", "--init"):
                db.create_tables()

                with SessionContext() as session:

                    mdl_user = User(name="Pálmar Gíslason", password="1qazXSW2", company="Fuglar ehf.", email="palmargisla@gmail.com", role=0)
                    session.add(mdl_user)
                    session.commit()

                    mdl_oauth = OAuth_User(provider_id=1, user_id=mdl_user.id, provider="google", email=mdl_user.email)
                    session.add(mdl_oauth)
                    session.commit()


                    mdl_company = Company(name="Fuglar")
                    session.add(mdl_company)
                    session.commit()

                    mdl_access = Access(user_id=mdl_user.id, company_id=mdl_company.id)
                    session.add(mdl_access)
                    session.commit()

                    mdl_golfcourse_1 = GolfCourse(name="Golfklúbbur Reykjavíkur", shortname="GR", color="#d72f40", company_id=mdl_company.id)
                    mdl_golfcourse_2 = GolfCourse(name="golfklúbbur Kópavogs og Garðabæjar", shortname="GKG", color="#6B9500", company_id=mdl_company.id)
                    session.add(mdl_golfcourse_1)
                    session.add(mdl_golfcourse_2)
                    session.commit()


                with SessionContext() as session:
                    try:
                        migr = Migrate_Version(0, "Migration initialized")
                        print("Migrated database to first version: {migr}".format(migr=migr))
                        session.add(migr)
                        session.commit()
                    except Exception as e:
                        print(e)
                        session.rollback()

            elif o in ("-t", "--test"):
                with SessionContext() as session:
                    pass

            elif o in ("-v", "--version"):
                with SessionContext() as session:
                    qMV = QueryMigrateVersion()
                    ver = qMV.scalar(session=session)

                    print("current version is {ver:03d}".format(ver=ver))


                    qMVH = QueryMigrateVersionHistory()
                    histories = qMVH.execute(session=session)
                    print("---------------")
                    for ver, scr, date in histories:
                        print("{scr} - v{ver:03d} ran on {date}"\
                            .format(scr=scr, ver=ver, date=date))

            elif o in ("-u", "--upgrade"):
                try:
                    with SessionContext() as session:
                        qMV = QueryMigrateVersion()
                        version = qMV.scalar(session=session) + 1

                        scripts, script_name = read_script(version)

                        for script in scripts.split(";"):
                            session.execute(script)

                        migr = Migrate_version(version, script_name)

                        session.add(migr)
                        session.commit()

                except FileNotFoundError:
                    print("file was not found, create a new one with 'migrate'")

                except Exception as e:
                    print(e)
                #with SessionContext() as session:
                #
                #    version = qMV.scalar()
                #    script = read_script(version)
                #    print(script)
                pass

        # Process arguments
        for arg in args:
            pass

    except Usage as err:
        print(err.msg, file = sys.stderr)
        print("For help use --help", file = sys.stderr)
        return 2

    finally:
        print("")

    # Completed with no error
    return 0


if __name__ == "__main__":
    sys.exit(main())
