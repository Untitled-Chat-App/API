""" (module)
functions for hashing text and passwords
"""

__all__ = ["argon2_hash", "bcrypt_hash", "bcrypt_verify", "argon2_verify"]

from argon2 import PasswordHasher
from bcrypt import gensalt, hashpw, checkpw
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash


async def argon2_hash(text: str) -> str:
    """
    Hashes text using the argon2 algorithm

    Parameters:
        text (str): The text to hash

    Returns:
        str: The hashed output of the function
    """

    password_hasher = PasswordHasher()
    hashed_output = password_hasher.hash(text)

    return hashed_output


async def bcrypt_hash(text: str) -> str:
    """
    Hashes text using the bcrypt algorithm

    Parameters:
        text (str): The text to hash

    Returns:
        str: The hashed output of the function
    """

    salt = gensalt(13)
    hashed = hashpw(text.encode(), salt).decode()

    return hashed


async def bcrypt_verify(password: str, hashed: str) -> bool:
    """
    Verifies an unverified password against the hashed version using bcrypt

    Parameters:
        password (str): The password in plain text
        hashed (str): The hashed password (from database)

    Returns:
        bool: If the hash is verified it returns true
    """

    return checkpw(password.encode(), hashed.encode())


async def argon2_verify(password: str, hashed: str) -> bool:
    """
    Verifies an unverified password against the hashed version using bcrypt

    Parameters:
        password (str): The password in plain text
        hashed (str): The hashed password (from database)

    Returns:
        bool: If the hash is verified it returns true
    """

    password_hasher = PasswordHasher()
    try:
        password_hasher.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False

    return True
