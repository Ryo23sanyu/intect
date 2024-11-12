import re
from django import template

register = template.Library()

@register.filter
def split_comma(value, delimiter=','):
    if not value:
        return []
    return value.split(delimiter)

@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)

@register.filter(name='store')
def store(value, storage):
    if 'value' not in storage:
        storage['value'] = value
        return None
    previous = storage['value']
    storage['value'] = value
    return previous

@register.filter(name='remove_prefix')
def remove_prefix(value, arg):
    """指定されたプレフィックスを削除するフィルター"""
    if value.startswith(arg):
        return value[len(arg):]
    return value

@register.filter
def sort_list(value):
    try:
        return sorted(value)
    except TypeError:
        return value
    
# 2つのforループを合体させて同じ挙動とする(bridge_table.html)
@register.filter
def zip_lists(a, b):
    return zip(a.split(','), b.split(','))

# 異なるモデルのデータをテンプレートに表示
# @register.filter
# def get_bridge_picture(pictures, picture):
#     try:
#         return pictures.get(this_time_picture=picture)
#     except BridgePicture.DoesNotExist:
#         return None
    
# register = template.Library()

@register.filter
def split_urls(value):
    return value.split(', ')