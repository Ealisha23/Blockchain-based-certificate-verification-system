#!/usr/bin/python3
"""
Db Storage module
"""

from app import models
from app.models.base_model import BaseModel, Base
from app.models.user import User
from app.models.school import School
from app.models.certificate import Certificate
from app.models.certificate_request_verification import VerifyCertificate
from app.models.admin import Admin
from os import getenv
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime

classes = {"User": User, "School": School, "Certificate": Certificate, "VerifyCertificate":VerifyCertificate, "Admin":Admin}


class DBstorage:
    """
    Connection class to mysql db
    """
    __engine = None
    __session = None

    def __init__(self):
        """
        Storage instance
        """
        BCV_ENV = getenv('BCV_ENV')
        database_url = getenv('BCV_DATABASE_URL')
        if not database_url:
            database_url = URL.create(
                'mysql+mysqldb',
                username=getenv('BCV_MYSQL_USER'),
                password=getenv('BCV_MYSQL_PWD'),
                host=getenv('BCV_MYSQL_HOST') or 'localhost',
                port=int(getenv('BCV_MYSQL_PORT') or 3306),
                database=getenv('BCV_MYSQL_DB'))
        self.__engine = create_engine(
            database_url, pool_pre_ping=True, pool_recycle=1800)

        if BCV_ENV == "test":
            db_name = self.__engine.url.database or ""
            if "test" not in db_name.lower():
                raise RuntimeError(
                    "Refusing to drop all tables: BCV_ENV=test but database "
                    "{!r} does not look like a test database.".format(db_name))
            Base.metadata.drop_all(self.__engine)

    def all(self, cls=None):
        """
        Get all the db sessions
        """
        new_dict = {}
        for clss in classes:
            if cls is None or cls is classes[clss] or cls is clss:
                objs = self.__session.query(classes[clss]).all()
                for obj in objs:
                    key = obj.__class__.__name__ + '.' + obj.id
                    new_dict[key] = obj
        return (new_dict)

    def new(self, obj):
        """
        Add the object to the current database session
        """
        self.__session.add(obj)

    def add(self, obj):
        """
        Add object to current database
        """
        self.__session.add(obj)

    def save(self):
        """
        Save object to db
        """
        self.__session.commit()

    def delete(self, obj=None):
        """
        Delete Object from db
        """
        if obj is not None:
            self.__session.delete(obj)

    def reload(self):
        """
        Reload data from the database
        """
        Base.metadata.create_all(self.__engine)
        sess_factory = sessionmaker(
            bind=self.__engine, expire_on_commit=False)
        Session = scoped_session(sess_factory)
        self.__session = Session

    def rollback(self):
        self.__session.rollback()

    def close(self):
        """
        Removes session
        """
        self.__session.remove()

    def get(self, cls, id):
        """
        Return an object based on class and id
        """
        if cls not in classes.values() or not id:
            return None
        return self.__session.get(cls, id)

    def get_email(self, cls, email):
        """
        Return an object based on class and email
        """
        if cls not in classes.values() or not email:
            return None
        return self.__session.query(cls).filter(cls.email == email).first()

    def get_certificate_by_hash(self, certificate_hash):
        return self.__session.query(Certificate).filter(
            Certificate.certificate_hash == certificate_hash).first()

    def email_in_use(self, email):
        """
        True if the email is registered as a user, school or admin
        """
        return any(self.get_email(c, email) for c in (User, School, Admin))

    def get_user_certificates(self, cls, user_id):
        """
        Return the certificates owned by a user or issued by a school
        """
        if cls is not Certificate:
            return None
        return self.__session.query(Certificate).filter(
            (Certificate.user_id == user_id) |
            (Certificate.school_id == user_id)).all()

    def get_certificates_status(self, cls, certificate_id):
        """
        Return the verification status row of a certificate
        """
        if cls is not VerifyCertificate:
            return None
        return self.__session.query(VerifyCertificate).filter(
            VerifyCertificate.certificate_id == certificate_id).order_by(
            VerifyCertificate.created_at.desc()).first()

    def get_user_schools(self, cls, user_id):
        """
        Return an object based on classname and certificate id
        """
        if cls is not School:
            return None
        return self.__session.query(School).filter(
            School.user_id == user_id).all()

    def count(self, cls=None):
        """
        Count objects
        """
        targets = [cls] if cls else list(classes.values())
        return sum(self.__session.query(c).count() for c in targets)

    def increase(self, cls=None):
        """
        Count objects created within the last 7 days
        """
        week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        targets = [cls] if cls else [User, School, Certificate]
        return sum(
            self.__session.query(c).filter(c.created_at >= week_ago).count()
            for c in targets)

    def verified_certificate_count(self):
        return self.__session.query(Certificate).filter(
            Certificate.verified_certificate.is_(True)).count()
