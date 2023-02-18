import os
from typing import Optional
from datetime import datetime, timedelta

from jose import jwt, ExpiredSignatureError, JWTError

from core import ExpiredTokenError, InvalidTokenError, User, parse_id


JWT_SIGNING_KEY = os.environ["JWT_SIGNING_KEY"]


async def create_access_token(
    data: dict, token_id: int, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a jwt access token. Token will be encoded with data. Since it uses JWT it can be decoded
    But it is signed so if you try modifiying it without knowing the sign

    Parameters:
        data (dict): The data to be encoded and put in the JWT token
        token_id (int): The id of the token. This is used to verify the token and figure out the token type
        expires_delta (Optional[timedelta]): How long the token should last. If not provided it will expire in 15min

    Returns:
        str: The JWT token with expiry and username encoded in
    """

    if expires_delta is None:
        expires_delta = timedelta(minutes=15)

    expire_time = datetime.utcnow() + expires_delta
    encoded_data = {"exp": expire_time, "tok_id": token_id, **data.copy()}

    return jwt.encode(encoded_data, JWT_SIGNING_KEY, algorithm="HS256")


async def check_valid_token(token: str):
    """
    Checks the token to see if its legit

    Parameters:
        token (str): The oauth2 JWT access token you got from the /token endpoint
    """

    try:
        payload = jwt.decode(token, JWT_SIGNING_KEY, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise ExpiredTokenError
    except JWTError:
        raise InvalidTokenError

    try:
        token_id = parse_id(payload["tok_id"])
    except (KeyError, ValueError, AttributeError):
        raise InvalidTokenError

    if token_id.idtype == "AUTH_TOK_ID":
        pass
    elif token_id.idtype == "VERIF_TOK_ID":
        await User.filter(id=payload.get("user_id")).update(verified=True)
    else:
        raise InvalidTokenError
