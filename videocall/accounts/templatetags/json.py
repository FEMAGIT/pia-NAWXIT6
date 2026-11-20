from django import template
from django.utils.safestring import mark_safe

register = template.Library()



@register.filter()
def print_nested(val, nesting = -5,html_text = '' ):
    if type(val) == dict:
        html_text += '<ul class="list-group" >'
        html_text +='\n'
        nesting += 5
        for k in val:
            html_text+=nesting * ' '
            html_text += '<li class="list-group-item"> '
            html_text += k +'  :  '
            html_text = print_nested(val=val[k], nesting=nesting, html_text=html_text)
            html_text += '</li> '
        html_text += '</ul>'
    elif type(val) == list:
        html_text += '<ul class="list-group" >'
        html_text += '\n'
        nesting += 5
        for elm in val:
            html_text += nesting * ' '
            html_text += '<li class="list-group-item"> '
            html_text = print_nested(elm, nesting=nesting, html_text=html_text)
            html_text += '</li> '

        html_text += '</ul>'
    else:
        html_text += str(val)
    return  mark_safe(html_text)


