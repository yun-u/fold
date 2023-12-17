from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, Tuple, Union

ESCAPE = "\x1b"
CSI = f"{ESCAPE}["


class Color:
    class Light:
        RED = "#FF3B30"
        ORANGE = "#FF9500"
        YELLOW = "#FFCC00"
        GREEN = "#34C759"
        MINT = "#00C7BE"
        TEAL = "#5AC8FA"
        CYAN = "#32ADE6"
        BLUE = "#007AFF"
        INDIGO = "#5856D6"
        PURPLE = "#AF52DE"
        PINK = "#FF2D55"
        BROWN = "#A2845E"
        GRAY = "#8E8E93"

    class Dark:
        RED = "#FF453A"
        ORANGE = "#FF9F0A"
        YELLOW = "#FFD60A"
        GREEN = "#30D158"
        MINT = "#66D4CF"
        TEAL = "#40C8E0"
        CYAN = "#64D2FF"
        BLUE = "#0A84FF"
        INDIGO = "#5E5CE6"
        PURPLE = "#BF5AF2"
        PINK = "#FF375F"
        BROWN = "#AC8E68"
        GRAY = "#8E8E93"

    GRAY1 = "#1C1C1E"
    GRAY2 = "#2C2C2E"
    GRAY3 = "#3A3A3C"
    GRAY4 = "#48484A"
    GRAY5 = "#636366"
    GRAY6 = "#8E8E93"
    GRAY7 = "#48484A"
    GRAY8 = "#636366"
    GRAY9 = "#8E8E93"
    GRAY10 = "#AEAEB2"
    GRAY11 = "#C7C7CC"
    GRAY12 = "#F2F2F7"


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    return tuple([int(hex_code[i : i + 2], 16) for i in range(1, 7, 2)])


def format_ansi_escape_sequence(*args: Any) -> str:
    """
    Applies Select Graphic Rendition (SGR) codes to format the characters.

    Args:
        *args (`str`): Variable number of SGR codes as arguments.

    Returns:
        `str`: The formatted string with the applied SGR codes.
    """
    return f"{CSI}{';'.join([str(arg) for arg in args])}m"


class TextStyle(IntEnum):
    """
    Enum class representing text styles SGR parameters.
    """

    NORMAL = 0  # Reset or normal
    BOLD = auto()
    LIGHT = auto()
    ITALIC = auto()
    UNDERLINE = auto()
    SLOW_BLINK = auto()
    RAPID_BLINK = auto()
    REVERSE = auto()

    @property
    def code(self) -> str:
        """
        Returns the SGR code corresponding to the enum value.

        Returns:
            `str`: The SGR code.
        """
        return format_ansi_escape_sequence(self.value)


class TextColor(IntEnum):
    """
    Enum class representing text colors for SGR system color codes.
    """

    BLACK = 30
    RED = auto()
    GREEN = auto()
    YELLOW = auto()
    BLUE = auto()
    MAGENTA = auto()
    CYAN = auto()
    WHITE = auto()

    BRIGHT_BLACK = 90
    BRIGHT_RED = auto()
    BRIGHT_GREEN = auto()
    BRIGHT_YELLOW = auto()
    BRIGHT_BLUE = auto()
    BRIGHT_MAGENTA = auto()
    BRIGHT_CYAN = auto()
    BRIGHT_WHITE = auto()

    @property
    def fg(self) -> str:
        """
        Returns the SGR foreground code corresponding to the enum value.

        Returns:
            `str`: The SGR foreground code.
        """
        return format_ansi_escape_sequence(self.value)

    @property
    def bg(self) -> str:
        """
        Returns the SGR background code corresponding to the enum value.

        Returns:
            `str`: The SGR background code.
        """
        return format_ansi_escape_sequence(self.value + 10)


class SGRRGBCode:
    """
    Class representing an RGB color for SGR.
    """

    def __init__(self, *rgb: int) -> None:
        """Initializes the RGB color with the provided values.

        Args:
            *rgb (`int`): Variable number of RGB color channel values.
        """
        assert len(rgb) == 3
        self.rgb = rgb

    @property
    def fg(self) -> str:
        """
        Returns the SGR foreground code corresponding to the RGB values.

        Returns:
            `str`: The SGR foreground code.
        """
        return format_ansi_escape_sequence(38, 2, *self.rgb)

    @property
    def bg(self) -> str:
        """
        Returns the SGR background code corresponding to the RGB values.

        Returns:
            `str`: The SGR background code.
        """
        return format_ansi_escape_sequence(48, 2, *self.rgb)


def colored_text(
    text: str,
    color: Union[TextColor, Tuple[int, int, int], None] = None,
    background_color: Union[TextColor, Tuple[int, int, int], None] = None,
    bold: bool = False,
    light: bool = False,
    italic: bool = False,
    underline: bool = False,
    reverse: bool = False,
) -> str:
    """
    Applies style attributes to the given text using SGR codes.

    Args:
        text (`str`): The text to be formatted.
        color (`Union[TextColor, Tuple[int, int, int]]`, optional): The color of the text. Defaults to None.
        background_color (`Union[TextColor, Tuple[int, int, int]]`, optional): The background color of the text. Defaults to None.
        bold (`bool`, optional): Whether to apply bold style. Defaults to False.
        light (`bool`, optional): Whether to apply light style. Defaults to False.
        italic (`bool`, optional): Whether to apply italic style. Defaults to False.
        underline (`bool`, optional): Whether to apply underline style. Defaults to False.

    Raises:
        AssertionError: Raised if both bold and light are set to True.

    Returns:
        `str`: The colored text.
    """
    assert not (bold and light), "Bold and light cannot be True simultaneously"

    codes = []

    if color:
        codes.append(
            color.fg if isinstance(color, TextColor) else SGRRGBCode(*color).fg
        )

    if background_color:
        codes.append(
            background_color.bg
            if isinstance(background_color, TextColor)
            else SGRRGBCode(*background_color).bg
        )

    if bold:
        codes.append(TextStyle.BOLD.code)

    if light:
        codes.append(TextStyle.LIGHT.code)

    if italic:
        codes.append(TextStyle.ITALIC.code)

    if underline:
        codes.append(TextStyle.UNDERLINE.code)

    if reverse:
        codes.append(TextStyle.REVERSE.code)

    style_code = "".join(codes)
    reset_code = TextStyle.NORMAL.code if codes else ""

    return f"{style_code}{text}{reset_code}"


@dataclass
class Style:
    color: Union[TextColor, Tuple[int, int, int], None] = None
    background_color: Union[TextColor, Tuple[int, int, int], None] = None
    bold: bool = False
    light: bool = False
    italic: bool = False
    underline: bool = False
    reverse: bool = False

    def apply(self, text: str) -> str:
        """
        Applies the defined style attributes to the given text.

        Args:
            text (`str`): The input text to be styled.

        Returns:
            `str`: The styled text.
        """
        return colored_text(
            text,
            color=self.color,
            background_color=self.background_color,
            bold=self.bold,
            light=self.light,
            italic=self.italic,
            underline=self.underline,
            reverse=self.reverse,
        )
