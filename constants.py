"""Константы проекта."""
from datetime import datetime as dt


TIMER_DELAY = 1
RETRY_TIME = 60
TIME_PATTERN = r'^(0[1-9]|[1-2][0-9]|3[0-1])\.(0[1-9]|1[0-2]) ([0-1][0-9]|2[0-3])\:([0-5][0-9])$' # noqa
date_format = "%d.%m %H:%M"
year_now = dt.today().year
