""" (module) users
Contains models for users
"""

import os
import re
from typing import Optional
from collections import OrderedDict

from jose import jwt, ExpiredSignatureError, JWTError

from tortoise import fields
from tortoise.models import Model
from fastapi import Form, Depends
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.contrib.pydantic import pydantic_model_creator  # type: ignore
from pydantic import BaseModel, SecretStr, EmailStr, EmailError, validator
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core import (
    InvalidUsernameError,
    InvalidEmailError,
    ExpiredTokenError,
    InvalidTokenError,
    argon2_hash,
    parse_id,
)
from core.models.chatapp import create_redis_connection


redis_conn = create_redis_connection()


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


class BlacklistedIP(Model):
    id = fields.BigIntField(pk=True, null=False, generated=True)
    ip = fields.CharField(max_length=40, unique=True, null=False)

    class Meta:
        table = "blacklisted_ips"


class Token(Model):
    token_id = fields.BigIntField(pk=True, null=False)
    owner = fields.ForeignKeyField("models.User", "token_users")
    token_type = fields.CharField(16, null=False)
    created_at = fields.DatetimeField(auto_now_add=True, null=False)

    class Meta:
        table = "tokens"


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


class PasswordRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        username: str = Form(...),
        password: SecretStr = Form(...),
        scope: str = Form(""),
    ):
        super().__init__(
            username=username,
            password=password,  # type: ignore
            scope=scope,
        )


class AuthToken(BaseModel):
    access_token: str
    token_type: str
    expiry_min: int

    refresh_token: str


class Permissions(BaseModel):
    user_read = False


user_cache = UserCache(50)
user_pyd = pydantic_model_creator(User, name="User")

permissions = {"user:read": "something cool no cap"}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", scopes=permissions)


async def check_auth_token(
    token: str = Depends(oauth2_scheme),
) -> tuple[User, Permissions]:
    try:
        payload = jwt.decode(token, os.environ["JWT_SIGNING_KEY"], algorithms=["HS256"])
    except ExpiredSignatureError:
        raise ExpiredTokenError
    except JWTError:
        raise InvalidTokenError

    try:
        token_id = parse_id(payload["tok_id"])
    except (KeyError, ValueError, AttributeError):
        raise InvalidTokenError

    user_id = payload["user_id"]

    user = user_cache.get(user_id)  # try getting user from cache
    if user is None:  # if user is not in cache
        # try get user from db:
        user = await User.filter(id=user_id).first()
        if user is None:  # if user is not even in db
            raise InvalidTokenError  # time for an error
        user_cache.set(user_id, user)  # update cache

    if token_id.idtype == "AUTH_TOK_ID":
        token = await redis_conn.get(str(payload["tok_id"]))
        if token is None:
            raise InvalidTokenError

        scopes: list[str] = payload["scopes"].split()
        perms_dict = {}

        for perm in permissions:
            if perm in scopes:
                perms_dict[perm.replace(":", "_")] = True

        perms = Permissions(**perms_dict)
        return (user, perms)

    raise InvalidTokenError
