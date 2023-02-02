""" (module) users
Contains models for users
"""

__all__ = ["NewUserForm"]

import re
from typing import Optional

from pydantic import BaseModel, EmailStr, EmailError, validator

from core import InvalidUsernameError, InvalidEmailError, argon2_hash


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
