from django import template

register = template.Library()


@register.filter
def remove_substr(string, char):
    return string.replace(char, '')
