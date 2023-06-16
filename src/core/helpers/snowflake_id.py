__all__ = ("generate_id", "parse_id")

from typing import Literal

from snowflake import Snowflake, SnowflakeGenerator

from .exceptions import UCHTTPExceptions

EPOCH = 0x63B01630  # January 1, 2023 12:00:00 AM NZST
CODES = {  # lambda x: hex(sum(ord(i) for i in x.lower()))
    "USER_ID": 0x1BF,
    "ROOM_ID": 0x1BD,
    "DEVICE_ID": 0x270,
    "MESSAGE_ID": 0x2E5,
    "AUTH_TOK_ID": 0x35F,
    "VERIF_TOK_ID": 0x3C9,
    "REFRESH_TOK_ID": 0x360,
}

generators = {
    key: SnowflakeGenerator(value, epoch=EPOCH) for (key, value) in CODES.items()
}


class SnowflakeID(Snowflake):
    """
    Subclass of Snowflake that include type
    """

    @classmethod
    def parse(cls, snowflake: int, epoch: int = 0) -> "SnowflakeID":
        return cls(
            epoch=epoch,
            timestamp=snowflake >> 22,
            instance=snowflake >> 12 & 0b1111111111,
            seq=snowflake & 0b111111111111,
        )

    @property
    def idtype(self):
        for key, value in CODES.items():
            if value == self.instance:
                return key
        raise UCHTTPExceptions.INVALID_SNOWFLAKE_ID


def generate_id(
    id_type: Literal[
        "USER_ID",
        "ROOM_ID",
        "DEVICE_ID",
        "MESSAGE_ID",
        "AUTH_TOK_ID",
        "VERIF_TOK_ID",
        "REFRESH_TOK_ID",
    ]
) -> int:
    """
    Generates a snowflake ID

    Parameters:
        id_type (Literal[
            "USER_ID", "ROOM_ID", "DEVICE_ID", "MESSAGE_ID",
            "AUTH_TOK_ID", "VERIF_TOK_ID", REFRESH_TOK_ID
        ]): The type of ID to generate
    """
    if (generator := generators.get(id_type)) is None:
        raise UCHTTPExceptions.INVALID_SNOWFLAKE_TYPE(id_type)
    if (_id := next(generator)) is None:
        raise UCHTTPExceptions.SNOWFLAKE_GENERATION_FAILED
    return _id


def parse_id(id_to_parse: int):
    """
    Parse an ID and return the useful stuff
    """
    return SnowflakeID.parse(id_to_parse, EPOCH)
