from django.forms import *
from django.views.generic.base import ImproperlyConfigured
from django.db import transaction


class FormInlineModelFormset(Form):
    FORMSET_FORM = None
    FORMSET_FORMSET = None
    FORMSET_MODEL = None
    FORMSET_FACTORY_KWARGS = {}
    FORMSET_INSTANCE_KWARGS = {}

    def __init__(self, *args, **kwargs):
        if not self.FORMSET_MODEL:
            raise ImproperlyConfigured("FormInlineModelFormset missing FORMSET_MODEL attribute")
        super().__init__(*args, **kwargs)
        self.formset = self.get_formset(**kwargs)

    @classmethod
    def get_formset_form(cls):
        return cls.FORMSET_FORM

    @classmethod
    def get_formset_formset(cls):
        return cls.FORMSET_FORMSET

    @classmethod
    def get_formset_factory_kwargs(cls):
        formset_kwargs = cls.FORMSET_FACTORY_KWARGS
        formset_kwargs['model'] = cls.FORMSET_MODEL
        if cls.get_formset_form():
            formset_kwargs['form'] = cls.get_formset_form()
        if cls.get_formset_formset():
            formset_kwargs['formset'] = cls.get_formset_formset()
        return formset_kwargs

    @classmethod
    def _get_formset_factory(cls):
        return modelformset_factory(**cls.get_formset_factory_kwargs())

    def get_formset(self, **kwargs):
        return self._get_formset_factory()(**self.get_formset_instance_kwargs(**kwargs))

    def get_formset_instance_kwargs(self, **kwargs):
        kwargs.update(self.FORMSET_INSTANCE_KWARGS)
        kwargs.update({'queryset': self.get_formset_queryset()})
        return kwargs

    def get_formset_queryset(self):
        return None

    def is_valid(self):
        valid = super().is_valid()
        valid = self.formset_is_valid() and valid
        return valid

    def formset_is_valid(self):
        return self.formset.is_valid()

    def formset_save(self):
        return self.formset.save()

    def save(self):
        self.formset_save()


class ModelFormInlineModelFormset(FormInlineModelFormset, ModelForm):

    def __init__(self, *args, **kwargs):
        if not self.FORMSET_MODEL:
            raise ImproperlyConfigured("ModelFormInlineModelFormset missing FORMSET_MODEL attribute")
        super(ModelForm, self).__init__(*args, **kwargs)
        kwargs.pop('instance', None)
        self.formset = self.get_formset(**kwargs)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            result = super().save(*args, **kwargs)
            self.formset_save()
            return result











