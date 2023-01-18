""" (module) exception
This module contains exceptions to make development easier
"""

from rich.text import Text
from rich.panel import Panel
from rich.console import Console


class BaseException(Exception):
    """Base class for other exceptions to inherit form"""

    pass


class RichBaseException(BaseException):
    """
    Base rich class for other exceptions to inherit form
    This one prints the error to console with rich
    """

    def __init__(self, title: str, message: str) -> None:
        error_message = Panel(
            Text.from_markup(f"[yellow]{message}"),
            title=title,
            border_style="red",
        )
        Console().print(error_message, justify="left")
        super().__init__()
