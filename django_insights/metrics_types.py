from __future__ import annotations

import datetime
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, NamedTuple

__all__ = ['BarChartResult', 'ScatterPlotResult', 'TimeSeriesResult']

TimeSeriesResult = Iterable[tuple[datetime.datetime, float]]
ScatterPlotResult = Iterable[tuple[float, float, Any]]
BarChartResult = Iterable[tuple[float, float, Any]]


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
