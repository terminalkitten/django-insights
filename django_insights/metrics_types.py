from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import NamedTuple, Optional


@dataclass
class CounterType:
    value: int


@dataclass
class GaugeType:
    value: float


TimeSeriesAnswer = NamedTuple(
    "TimeSeriesAnswer", [('timestamp', datetime.datetime), ('xvalue', float)]
)


@dataclass
class TimeSeriesType:
    values: list[TimeSeriesAnswer]


ScatterPlotAnswer = NamedTuple(
    "ScatterPlotAnswer",
    [
        ('timestamp', Optional[datetime.datetime]),
        ('xvalue', float),
        ('yvalue', float),
        ('category', Optional[str]),
    ],
)


@dataclass
class ScatterPlotType:
    values: list[ScatterPlotAnswer]
