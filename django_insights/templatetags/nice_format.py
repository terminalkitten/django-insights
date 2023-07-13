from django import template

register = template.Library()


@register.filter
def clean_str(string, char):
    return string.replace(char, '')


@register.filter
def nice_float(string):
    if isinstance(string, float):
        return f'{round(string):,}'.replace(',', '.')
    return string
