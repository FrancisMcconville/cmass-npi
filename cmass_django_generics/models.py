from django.db.models.base import ModelBase
from django.db.models import CharField


class StatefulModel(ModelBase):
    """
    _states: dict(str(state), str(Verbose state))
    _state_default: str(state)
    _state_verbose: str(Verbose field name)
    """

    def __new__(cls, name, bases, attrs):
        attr_meta = attrs.get('Meta', None)
        if attr_meta:
            states = getattr(attr_meta, '_states', False)

            if states:
                state_default = getattr(attr_meta, '_state_default', '')
                state_verbose = getattr(attr_meta, '_state_verbose', 'State')
                state_prefix = getattr(attr_meta, '_state_prefix', '')
                longest_state = max(states, key=len)
                state_attribute = 'state'

                if state_prefix:
                    state_attribute = "%s_" % state_prefix + state_attribute

                attrs[state_attribute] = CharField(
                    verbose_name=state_verbose,
                    choices=[(state, states[state]) for state in states],
                    default=state_default,
                    max_length=len(longest_state)
                )
                attrs[state_attribute.upper()+'S'] = states
        return super().__new__(cls, name, bases, attrs)