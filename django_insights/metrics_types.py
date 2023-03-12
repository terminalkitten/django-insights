from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, NamedTuple, Optional


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
    xvalue: float
    yvalue: float
    category: Optional[Any]


@dataclass
class ScatterPlotType:
    values: list[ScatterPlotAnswer]


class BarChartAnswer(NamedTuple):
    xvalue: float
    yvalue: float
    category: Optional[Any]


@dataclass
class BarChartType:
    values: list[BarChartAnswer]
