"""Display elapsed times without ever rounding the seconds field to 60."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math


def _ticks(seconds, precision):
    if isinstance(seconds,bool) or seconds is None:return None
    try:
        value=float(seconds)
        if not math.isfinite(value) or value<0:return None
        return int((Decimal(str(seconds))*(10**precision)).quantize(Decimal(1),rounding=ROUND_HALF_UP))
    except (ValueError,TypeError,InvalidOperation,OverflowError):return None


def elapsed(seconds, precision=1):
    """59.9s below a minute, then 1:00.0; signed differences use their own UI."""
    precision=max(0,min(3,int(precision)))
    ticks=_ticks(seconds,precision)
    if ticks is None:return '—'
    scale=10**precision
    minutes,remainder=divmod(ticks,60*scale)
    whole,fraction=divmod(remainder,scale)
    tail=f'.{fraction:0{precision}d}' if precision else ''
    if minutes:return f'{minutes}:{whole:02d}{tail}'
    return f'{whole}{tail}s'


def lap_time(seconds):
    ticks=_ticks(seconds,3)
    if ticks is None or ticks<=0:return '--:--.---'
    minutes,remainder=divmod(ticks,60000)
    whole,fraction=divmod(remainder,1000)
    return f'{minutes}:{whole:02d}.{fraction:03d}'
