from django.test.runner import DiscoverRunner
from django.test.simple import DjangoTestSuiteRunner
from django.conf import settings

# Check if database will use already defined test_database in settings_test.py
# or if is need change name in runtime

SETUP_DATABASE_NAME = settings.MONGO_DATABASE_NAME

class TestRunner(DiscoverRunner):

    def setup_databases(self, **kwargs):
        from mongoengine.connection import connect, disconnect
        disconnect(settings.MONGO_DATABASE_NAME)
        db_name = 'test_%s' % SETUP_DATABASE_NAME
        conn = connect(db_name)
        database = conn[db_name]
        print 'Creating test-database: ' + db_name[0]
        return db_name

    def teardown_databases(self, old_config, **kwargs):
        from pymongo import MongoClient
        conn = MongoClient()
        conn.drop_database(old_config)
        print 'Dropping test-database: ' + old_config
