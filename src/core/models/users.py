""" (module) users
Contains models for users
"""

__all__ = ["NewUserForm", "User"]

import re
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    BOOLEAN,
    VARCHAR,
    TEXT,
    TIMESTAMP,
    BIGINT,
)
from pydantic import BaseModel, EmailStr, EmailError, validator

from core.db import Base
from core import InvalidUsernameError, InvalidEmailError, argon2_hash


class User(Base):
    __tablename__ = "users"

    """
    Base model for a user from the database

    Attributes:
        user_id (str): unique id to identify user, no other users can have that id.
        username (str): the users Username. used to signup for the app and shown everywhere (unless display name)
        password (str): the users hashed password
        email (str): the users email
        firstname (str): the users firstname
        lastname (Optional[str]): the users lastname. This is optional
        created_at (int): timestamp of when the user created their account
        verified (bool): indicator of if the user has verified their email
            and completed the signup process (default=false)
        avatar (Optional[str]): link to the users profile picture
            (or foreign key (uuid) to the user avatar table where the pfp is stored in bytes)
        rooms (Optional[list[str]]): A list of rooms the user is the owner/admin of.
            This list is a list of room ids aka foreign keys to the rooms table
        display_name (Optional[str]): The users chosen display name.
            By default this is none but if a user sets it they are displayed with that name
    """

    id = Column(BIGINT, primary_key=True, autoincrement=False)
    username = Column(VARCHAR(32), unique=True, nullable=False)
    password = Column(TEXT, nullable=False)
    email = Column(VARCHAR(256), unique=True, nullable=False)
    firstname = Column(VARCHAR(64), nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False)
    verified = Column(BOOLEAN, default=False)
    lastname = Column(VARCHAR(64))
    avatar = Column(TEXT)
    rooms = Column(ARRAY(BIGINT))
    display_name = Column(TEXT)


class NewUserForm(BaseModel):
    """
    Base model to represent the details of a new user
    These are provided by the user when signing up
    """

    username: str = ""
    firstname: str = ""
    lastname: Optional[str] = ""
    email: str = ""
    password: str = ""

    @validator("username")
    @classmethod
    def validate_user_name(cls, username: str):
        """
        Takes in an username and checks if it is valid

        Parameters:
            username (str): The username of the person signing up

        Returns:
            str: If username is valid it returns the user

        Raises:
            InvalidUsernameError: If the username is invalid it raises an exception
        """

        # if length of username is 0 get better at usernames
        if not username:
            raise InvalidUsernameError(username)

        # check if username starts with a number
        if username[0].isnumeric():
            raise InvalidUsernameError(username)

        # check if username matches criteria
        if not re.match(
            "^(?=.{3,32}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$", username
        ):
            raise InvalidUsernameError(username)

        return username

    @validator("email")
    @classmethod
    def validate_user_email(cls, email: str):
        """
        Takes in an email and checks if it is valid

        Parameters:
            email (str): The email of the person signing up

        Returns:
            str: If email is valid it returns the user

        Raises:
            InvalidEmailError: If the email is invalid it raises an exception
        """

        try:
            EmailStr.validate(email)
        except EmailError:
            raise InvalidEmailError(email)

        return email

    async def hashpass(self):
        self.password = await argon2_hash(self.password)
