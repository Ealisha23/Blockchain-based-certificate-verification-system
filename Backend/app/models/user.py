#!/usr/bin/python3
"""
User object class
"""
from app import models
from app.models.base_model import BaseModel, Base
from os import getenv
import sqlalchemy
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
import bcrypt


class User(BaseModel, Base):
    """
    User Object representation
    """
    __tablename__ = 'users'
    email = Column(String(128), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    profile_url = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    about_profile = Column(String(255), nullable=True)
    role = Column(String(20), nullable=True, default="user")
    certificates = relationship(
        "Certificate",
        backref='user',
        lazy='dynamic',
        cascade="all, delete, delete-orphan")
    schools = relationship(
        "School",
        backref="user",
        lazy='dynamic',
        cascade="all, delete, delete-orphan")
    certificates_verify_status = relationship(
        "VerifyCertificate",
        backref="user",
        lazy='dynamic',
        cascade="all, delete, delete-orphan")

    def __init__(self, *args, **kwargs):
        """
        initializes user
        """
        super().__init__(*args, **kwargs)

    def __setattr__(self, name, value):
        """
        hashes the password with bcrypt before storing it
        """
        if name == "password":
            value = bcrypt.hashpw(
                value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        super().__setattr__(name, value)

    def check_password(self, password):
        """
        CheckPassword Encryption
        """
        if not isinstance(password, str) or not self.password:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'),
                                  self.password.encode('utf-8'))
        except ValueError:
            return False
