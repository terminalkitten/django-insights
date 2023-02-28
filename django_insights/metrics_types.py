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


class TimeSeriesAnswer(NamedTuple):
    timestamp: datetime.datetime
    xvalue: float


@dataclass
class TimeSeriesType:
    values: list[TimeSeriesAnswer]


class ScatterPlotAnswer(NamedTuple):
    timestamp: Optional[datetime.datetime]
    xvalue: float
    yvalue: float
    category: Optional[str]


@dataclass
class ScatterPlotType:
    values: list[ScatterPlotAnswer]
