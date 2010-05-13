# -*- coding: utf-8 -*-

import os
import sys
import application
import unittest

# sys.path for importing  modules of Google App Engine and UnitTest Targets.

GAE_HOME = '/foo/bar/google_appengine'
PROJECT_HOME = '/foo/bar/template-gae-with-flask'

sys.path = [
    GAE_HOME,
    PROJECT_HOME,
    os.path.join(GAE_HOME, 'google', 'appengine', 'api'),
    os.path.join(GAE_HOME, 'google', 'appengine', 'ext'),
    os.path.join(GAE_HOME, 'lib', 'yaml', 'lib'),
    os.path.join(PROJECT_HOME, 'utils'),
    ] + sys.path

# to importing stubs and required classes.

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.api import user_service_stub

# environment variables of Google App Engine.

APP_ID = 'test_id'
LOGGED_IN_USER = 'test@example.com'  # AUTH_DOMAIN = 'gmail.com'

# Base Class for UnitTest.


class GAETestBase(unittest.TestCase):

    def setUp(self):

        # to registering API Proxy Stub Map.

        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

        # to registering Datastore File Stub.

        stub = datastore_file_stub.DatastoreFileStub(APP_ID, '/dev/null',
                '/dev/null')
        apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)

        # to setting APPLICATION_ID for Datastore.

        os.environ['APPLICATION_ID'] = APP_ID

        # to registering User Service Stub.

        apiproxy_stub_map.apiproxy.RegisterStub('user',
                user_service_stub.UserServiceStub())

        # to setting AUTH_DOMAIN and USER_EMAIL for UserService.
        # os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN

        os.environ['USER_EMAIL'] = LOGGED_IN_USER
        os.environ['SERVER_NAME'] = 'dev'
        os.environ['SERVER_PORT'] = '80'

        self.app = application.app.test_client()

    def test_first(self):
        res = self.app.get('/')
        self.assertEquals(res.status, '200 OK')


if __name__ == '__main__':
    unittest.main()

