import xmlrpc.client as xmlrpclib
from copy import deepcopy
from django.conf import settings


def dictfetchall(cursor):
    """
    Source: http://stackoverflow.com/questions/10888844/using-dict-cursor-in-django
    Returns all rows from a cursor as a dict
    """
    desc = cursor.description
    return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
    ]


class OpenerpXmlrpc(object):

    _CONNECTION_ARGS = settings.OPENERP_XMLRPC_SETTINGS
    _SERVER = None
    _UID = None

    def connect(self):
        server = xmlrpclib.ServerProxy('http://%(host)s:%(port)s/xmlrpc/common' % self._CONNECTION_ARGS)
        self._UID = server.login(
            self._CONNECTION_ARGS['database'],
            self._CONNECTION_ARGS['username'],
            self._CONNECTION_ARGS['password']
        )
        if not self._UID:
            raise Exception(
                "Login to XMLRPC Failed, Incorrect Username or Password. Username: %(user)s" % {
                    'user': self._CONNECTION_ARGS['username'],
                }
            )
        self._SERVER = xmlrpclib.ServerProxy(
            "http://%(host)s:%(port)s/xmlrpc/object" % self._CONNECTION_ARGS)

    def openerp_execute(self, model, command, *args):
        return self._SERVER.execute(
            self._CONNECTION_ARGS['database'], self._UID, self._CONNECTION_ARGS['password'], model, command, *args
        )


bad_characters = [',', ';', '\t']


def _(string):
    """sanitize strings for csv"""
    for character in bad_characters:
        string = string.replace(character, ' ')
    return string


def copy_record(record):
    record = deepcopy(record)
    record.id = None
    record.save()
    return record
