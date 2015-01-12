#coding: utf-8
from django.test.simple import DjangoTestSuiteRunner

from mongoengine.python_support import PY3

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

class MongoTestRunner(DjangoTestSuiteRunner):
    """
        A test runner that can be used to create, connect to, disconnect from, 
        and destroy a mongo test database for standard django testing. The
        target is from start and end of the tests. One database is creates for
        each executing tests (full suite) and not each test case.

        NOTE:
            The MONGO_PORT and MONGO_DATABASES settings must exist, create them
            if necessary.

            e.g:
            MONGO_DATABASES = {
                'YourDB' : 'default' # default is alias name
            }
            MONGO_PORT = 27017
            MONGO_HOST = 'localhost'
        
        Adapted from:
            http://nubits.org/post/django-mongodb-mongoengine-testing-with-custom-test-runner/
    """

    @property
    def mongodb_name(self):
        for db_name, db_alias in settings.MONGO_DATABASES.items():
            return db_name
    @property
    def mongodb_test_name(self):
        for db_name, db_alias in settings.MONGO_DATABASES.items():
            return 'test_%s' % (db_name,)

    def setup_databases(self, **kwargs):
        from mongoengine.connection import connect, disconnect
        disconnect()
        connect(self.mongodb_test_name, port=settings.MONGO_PORT)
        print 'Creating mongo test database ' + self.mongodb_test_name
        return super(MongoTestRunner, self).setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        from mongoengine.connection import get_connection, disconnect
        connection = get_connection()
        connection.drop_database(self.mongodb_test_name)
        print 'Dropping mongo test database: ' + self.mongodb_test_name
        disconnect()
        super(MongoTestRunner, self).teardown_databases(old_config, **kwargs)
