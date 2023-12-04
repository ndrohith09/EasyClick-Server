from django import template

register = template.Library()

@register.filter
def divide_string_by_100(value):
    try:
        amount = int(value)
        result = amount / 100
        return int(result)
    except (ValueError, TypeError):
        return value
