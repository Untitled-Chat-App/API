__all__ = ("generate_id", "parse_id")

from typing import Literal

from snowflake import Snowflake, SnowflakeGenerator

EPOCH = 0x63B01630
CODES = {
    "USER_ID": 0x1BF,
    "ROOM_ID": 0x1BD,
    "DEVICE_ID": 0x270,
    "MESSAGE_ID": 0x2E5,
}

generators = {
    key: SnowflakeGenerator(value, epoch=EPOCH) for (key, value) in CODES.items()
}


class SnowflakeID(Snowflake):
    """
    Subclass of Snowflake that include type
    """

    @property
    def idtype(self):
        for key, value in CODES.items():
            if value == self.instance:
                return key
        raise Exception("Invalid ID")


def generate_id(
    id_type: Literal["USER_ID", "ROOM_ID", "DEVICE_ID", "MESSAGE_ID"]
) -> int:
    """
    Generates a snowflake ID

    Parameters:
        id_type (Literal[
            "USER_ID", "ROOM_ID", "DEVICE_ID", "MESSAGE_ID"
        ]): The type of ID to generate
    """
    if (generator := generators.get(id_type)) is None:
        raise ValueError(f"ID type provided: {id_type} is not a valid option!")
    if (_id := next(generator)) is None:
        raise Exception("Failed to generate ID")
    return _id


def parse_id(id_to_parse: int):
    """
    Parse an ID and return the useful stuff
    """
    return SnowflakeID.parse(id_to_parse, EPOCH)
