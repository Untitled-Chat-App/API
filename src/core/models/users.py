""" (module) users
Contains models for users
"""

__all__ = ("NewUserForm", "User", "user_pyd", "UserCache")

import re
from typing import Optional
from collections import OrderedDict

from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.contrib.pydantic import pydantic_model_creator  # type: ignore
from pydantic import BaseModel, EmailStr, EmailError, validator

from core import InvalidUsernameError, InvalidEmailError, argon2_hash, parse_id


class User(Model):
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

    id = fields.BigIntField(pk=True, null=False)
    username = fields.CharField(32, unique=True, null=False)
    password = fields.TextField(null=False)
    email = fields.CharField(256, unique=True, null=False)
    firstname = fields.CharField(64, null=False)
    created_at = fields.DatetimeField(auto_now_add=True, null=False)
    verified = fields.BooleanField(default=False, null=False)
    lastname = fields.CharField(64, null=True)
    avatar = fields.TextField(null=True)
    rooms = ArrayField("BIGINT", null=True)
    display_name = fields.TextField(null=True)

    registration_id = fields.IntField(null=True)
    identity_key = fields.TextField(null=True)
    signed_prekey = fields.TextField(null=True)

    class Meta:
        table = "users"


user_pyd = pydantic_model_creator(User, name="User")


class BlacklistedIP(Model):
    id = fields.BigIntField(pk=True, null=False, generated=True)
    ip = fields.CharField(max_length=40, unique=True, null=False)

    class Meta:
        table = "blacklisted_ips"


class BlacklistedEmail(Model):
    id = fields.BigIntField(pk=True, null=False, generated=True)
    email = fields.CharField(256, unique=True, null=False)

    class Meta:
        table = "blacklisted_emails"


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


class UserCache:
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.users: OrderedDict[int, User] = OrderedDict()

    def get(self, user_id: int) -> Optional[User]:
        value = self.users.get(user_id)
        if value is not None:
            self.users.move_to_end(user_id)
        return value

    def set(self, user_id: int, value: User) -> None:
        if parse_id(user_id).idtype != "USER_ID":
            return

        self.get(user_id)
        self.users[user_id] = value

        if len(self.users) > self.capacity:
            self.users.popitem(last=False)
