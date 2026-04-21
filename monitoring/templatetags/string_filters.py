from django import template

register = template.Library()

@register.filter
def replace_underscore(value):
    return str(value).replace("_", " ")
