from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Custom filter to access dictionary items using a variable key"""
    return dictionary.get(key)
