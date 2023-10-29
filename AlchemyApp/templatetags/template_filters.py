from django.template.defaulttags import register
from AlchemyApp.utilities import style_brackets
from django import template

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_items(dictionary, key):
    return dictionary.get(key, [])

@register.filter(name='style_brackets')
def style_brackets_filter(value):
    return style_brackets(value)