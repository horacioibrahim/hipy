#coding: utf-8

from mongoengine.python_support import PY3
from mongoengine import connect

try:
    from django.test import TestCase
    from django.conf import settings
except Exception as err:
    if PY3:
        from unittest import TestCase
        # Dummy value so no error
        class settings:
            MONGO_DATABASE_NAME = 'dummy'
    else:
        raise err


class MongoTestCase(TestCase):
    """
        TestCase class that clear the collection between the tests
    """
    
    def _pre_setup(self):
        from mongoengine.connection import connect, disconnect
        for db_name, db_alias in settings.MONGO_DATABASES.items():
            disconnect(db_alias)
            test_db_name = "test_{}".format(db_name)
            test_db_alias = "test_{}".format(db_alias)
            connect(db=test_db_name, alias=test_db_alias,
                    port=settings.MONGO_PORT)

    def _post_teardown(self):
        from mongoengine.connection import get_connection, disconnect
        for db_name, db_alias in settings.MONGO_DATABASES.items():
            test_db_name = "test_{}".format(db_name)
            connection = get_connection("test_{}".format(db_alias))
            connection.drop_database(test_db_name)
            disconnect(db_alias)



    # em pre_setup criar com alias