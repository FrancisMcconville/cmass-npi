from django.conf import settings


class OpenerpRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'metrics':
            return 'erp'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'metrics' and settings.IS_TESTING:
            return 'erp'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'metrics' and obj2._meta.app_label == 'metrics' and settings.IS_TESTING:
            return 'erp'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'erp' and settings.IS_TESTING:
            return True
        return None