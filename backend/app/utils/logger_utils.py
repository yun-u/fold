import logging
from dataclasses import asdict
from typing import Union

from app.utils.style_utils import Color, Style, TextColor, colored_text, hex_to_rgb

LOG_FORMAT = (
    f"{colored_text('[%(asctime)s]', color=TextColor.GREEN)} "
    f"%(levelname)s "
    f"{colored_text('[%(filename)26s:%(lineno)-4d]', color=hex_to_rgb(Color.GRAY5), light=True)} "
    f"{colored_text('[%(process)d]', color=TextColor.YELLOW)} "
    f"%(message)s"
)


LOG_LEVEL_FORMATS = {
    logging.DEBUG: Style(color=TextColor.WHITE, bold=True),
    logging.INFO: Style(color=TextColor.BLUE, bold=True),
    logging.WARNING: Style(color=TextColor.YELLOW, bold=True),
    logging.ERROR: Style(color=TextColor.RED, bold=True),
    logging.CRITICAL: Style(
        color=TextColor.WHITE,
        bold=True,
        background_color=TextColor.RED,
    ),
}


def setup_logger(level: Union[str, int] = logging.INFO):
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt="%x %X",
    )

    for level, style in LOG_LEVEL_FORMATS.items():
        logging.addLevelName(
            level, colored_text(f"{logging.getLevelName(level):>8}", **asdict(style))
        )
