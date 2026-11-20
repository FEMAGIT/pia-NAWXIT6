from django import template
register = template.Library()



def get_item(dictionary, args):
    if args is None:
        return False
    arg_list = [arg.strip() for arg in args.split(',')]
    return var in arg_list

    return key[dictionary]

register.filter(get_item)

@register.simple_tag
def enabled(dict, pk1, pk2):
    cost = dict.get(str(str(pk1)+"_"+ str(pk2)))
    return cost