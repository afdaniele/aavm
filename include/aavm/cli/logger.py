import logging
from logging import getLogger

from termcolor import colored

from aavm.constants import DEBUG

# create logger
aavmlogger = getLogger('aavm')

colors = {
    'critical': 'red',
    'debug': 'magenta',
    'error': 'red',
    'info': 'green',
    'notice': 'magenta',
    'spam': 'green',
    'success': 'green',
    'verbose': 'blue',
    'warning': 'yellow'
}

# color parts of the left bar
levelname = colored("%(levelname)8s", "grey")
filename_lineno = colored("%(filename)15s:%(lineno)-4s", "blue")

# compile format
format = f"%(name)4s|{filename_lineno} - %(funcName)-15s : %(message)s" \
    if DEBUG else f"%(name)4s|{levelname} : %(message)s"
indent = " " * (44 if DEBUG else 14)


class CustomFilter(logging.Filter):
    def filter(self, record):
        lines = str(record.msg).split("\n")
        color = colors[record.levelname.lower()]
        lines = map(lambda l: colored(l, color) if color else l, lines)
        record.msg = f"\n{indent}: ".join(lines)
        return super(CustomFilter, self).filter(record)


# handle multi-line messages
aavmlogger.addFilter(CustomFilter())

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter(format)
ch.setFormatter(formatter)
# add the handlers to logger
aavmlogger.addHandler(ch)


def update_logger(level: int):
    # set level
    aavmlogger.setLevel(level)
    ch.setLevel(level)


# set INFO as default level
update_logger(logging.INFO)


__all__ = [
    "aavmlogger",
    "update_logger"
]
