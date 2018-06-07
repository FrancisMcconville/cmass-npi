from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    if user.is_superuser:
        return True
    try:
        group = Group.objects.get(name=group_name)
    except:
        # Group does not exist
        return False
    return True if group in user.groups.all() else False


@register.filter(name='bool_as_icon')
def bool_as_icon(value):
    if value:
        return '✔'
    else:
        return '✘'
    
@register.filter(name='keyvalue')
def keyvalue(dict, key):
    return dict.get(key, {})
