from django.template.defaulttags import register
from django import template

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_items(dictionary, key):
    return dictionary.get(key, [])