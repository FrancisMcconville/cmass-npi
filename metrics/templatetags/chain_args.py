"""Pass multiple parametrs into Django filter.
Inspired by http://stackoverflow.com/a/24402622/2629036.
By this filters you can chain as many variables into parametrs as you like.
You can even make different lengths for one filter.
WARNING: You have to apply n_chain_end filter at the end of the n_chains.
Thanks to this the intial var can also be tupple.
Usage of n_chain:
  {{ var|n_chain_more:1|n_chain_more:2|n_chain_more:3|n_chain_end|your_filter }}
  The output from this will look like:
  (var, 1, 2, 3)
  NOTE: if var was tupple (elements_of_my_tupple, None, 5, 10) the resoult would look like:

  ((elements_of_my_tupple, None, 5, 10), 1, 2, 3)

Usage of n_more:
  {{ var|n_more:1|n_more:2|n_more:3|your_filter }}

  The output from this will look like:

  (var, 1, 2, 3)

  NOTE: if var was tupple (elements_of_my_tupple, None, 5, 10) the resoult would look like:

  (elements_of_my_tupple, None, 5, 10, 1, 2, 3)
"""
from django import template

register = template.Library()


class Chain(object):
    pass


@register.filter(name='n_chain_more')
def n_chain_more(_n, _2):
    """Chain element."""
    if type(_n) == tuple and _n[-1] == Chain:
        return _n[:-1] + (_2, Chain)
    return _n, _2, Chain


@register.filter(name='n_chain_end')
def n_chain_end(_n):
    """Chain terminator."""
    if type(_n) == tuple and _n[-1] == Chain:
        return _n[:-1]
    return _n


@register.filter(name='n_more')
def n_more(_n, _2):
    """Append element to tupple."""
    if type(_n) == tuple:
        return _n + (_2,)
    return _n, _2
