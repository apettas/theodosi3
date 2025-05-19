# proypiresies_app/templatetags/proypiresies_extras.py
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)