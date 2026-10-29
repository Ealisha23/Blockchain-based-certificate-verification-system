#!/usr/bin/python3
"""
Admin object class
"""
from app import models
from app.models.base_model import BaseModel, Base
from os import getenv
import sqlalchemy
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
import bcrypt


class Admin(BaseModel, Base):
    """
    Admin Object representation
    """
    __tablename__ = 'admins'
    username = Column(String(128), nullable=False)
    password = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    is_superadmin = Column(Boolean, default=False)
    role = Column(String(20), nullable=True, default="admin")


    def __init__(self, *args, **kwargs):
        """Initialize the Admin instance"""
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
