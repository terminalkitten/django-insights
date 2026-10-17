from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, NamedTuple


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
    category: Any | None


@dataclass
class ScatterPlotType:
    values: list[ScatterPlotAnswer]


class BarChartAnswer(NamedTuple):
    xvalue: float
    yvalue: float
    category: Any | None


@dataclass
class BarChartType:
    values: list[BarChartAnswer]
