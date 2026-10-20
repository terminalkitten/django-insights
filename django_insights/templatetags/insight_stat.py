from django import template
from django.utils.html import format_html
from django.utils.safestring import SafeString

register = template.Library()

WIDTH = 100
HEIGHT = 28


@register.filter
def sparkline(values: list[float]) -> SafeString | str:
    """A small line of the trend values, nothing without at least two"""
    if len(values) < 2:
        return ''

    low, high = min(values), max(values)
    spread = (high - low) or 1
    step = WIDTH / (len(values) - 1)
    points = ' '.join(
        f'{number * step:.1f},{HEIGHT - 2 - (value - low) / spread * (HEIGHT - 4):.1f}'
        for number, value in enumerate(values)
    )
    return format_html(
        '<svg viewBox="0 0 {} {}" preserveAspectRatio="none" aria-hidden="true"'
        ' class="h-7 w-full overflow-visible" fill="none" stroke="currentColor"'
        ' stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline vector-effect="non-scaling-stroke" points="{}" /></svg>',
        WIDTH,
        HEIGHT,
        points,
    )


@register.filter
def trend(values: list[float]) -> float | None:
    """Percentage change of the last value against the one before it"""
    if len(values) < 2 or not values[-2]:
        return None
    return (values[-1] - values[-2]) / abs(values[-2]) * 100
