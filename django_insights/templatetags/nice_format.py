from typing import TypeVar

from django import template

register = template.Library()

T = TypeVar('T')


@register.filter
def clean_str(string: str, char: str) -> str:
    return string.replace(char, '')


@register.filter
def nice_float(string: T) -> T | str:
    if isinstance(string, float):
        return f'{round(string):,}'.replace(',', '.')
    return string
