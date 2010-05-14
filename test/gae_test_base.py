#!/usr/bin/env python2.5
# -*- coding:utf-8 -*-

import os, sys
import functools
import unittest

APP_ID = u'tagomoris-test'
LOCAL_GAE_HOME = '/home/tagomoris/google_appengine'
LOCAL_PROJECT_HOME = '/home/tagomoris/tagomoris-test/trunk'
REMOTE_API_ENTRY_POINT = '/remote_api'

def is_in_production():
    try:
        from google3.apphosting.runtime import _apphosting_runtime___python__apiproxy
        _apphosting_runtime___python__apiproxy = None
        return True
    except ImportError:
        return False

if not is_in_production():
    import getpass

    EXTRA_PATHS = [
        LOCAL_GAE_HOME,
        LOCAL_PROJECT_HOME,
        os.path.join(LOCAL_GAE_HOME, 'google', 'appengine', 'api'),
        os.path.join(LOCAL_GAE_HOME, 'google', 'appengine', 'ext'),
        os.path.join(LOCAL_GAE_HOME, 'lib', 'yaml', 'lib'),
        os.path.join(LOCAL_GAE_HOME, 'lib', 'webob'),
        ]
    sys.path = EXTRA_PATHS + sys.path

    from google.appengine.tools import appengine_rpc
    from google.appengine.ext.remote_api import remote_api_stub
    from google.appengine.api import datastore_file_stub
    from google.appengine.api import mail_stub
    from google.appengine.api import urlfetch_stub
    from google.appengine.api import user_service_stub

    AUTH_DOMAIN = 'gmail.com'
    LOGGED_IN_USER = 'test@gmail.com'


from google.appengine.api import apiproxy_stub_map
from google.appengine.ext import db

def set_environments(testcase):
    if not is_in_production() and not is_in_gaeunit() and not testcase.use_remote_api():
        testcase.original_env = os.environ.copy()
        os.environ['APPLICATION_ID'] = APP_ID
        os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
        os.environ['USER_EMAIL'] = LOGGED_IN_USER

def restore_environments(testcase):
    if hasattr(testcase, 'original_env'):
        os.environ = testcase.original_env

def auth_func():
    return (raw_input('Email: '), getpass.getpass('Password: '))

def get_gaeunit_frame():
    frame = sys._getframe()
    frame = frame.f_back.f_back
    while frame:
        if (frame.f_code.co_filename.find('gaeunit') > -1 and
            frame.f_code.co_name == '_run_test_suite'):
            return frame
        frame = frame.f_back
    return None

def is_in_gaeunit():
    return get_gaeunit_frame() is not None

def get_original_apiproxy_behind_gaeunit():
    f = get_gaeunit_frame()
    return f.f_locals['original_apiproxy']

def get_dev_apiproxy():
    _apiproxy = apiproxy_stub_map.APIProxyStubMap()

    _apiproxy.RegisterStub('datastore_v3', datastore_file_stub.DatastoreFileStub(APP_ID, None, None))
    _apiproxy.RegisterStub('user', user_service_stub.UserServiceStub())
    _apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub())
    _apiproxy.RegisterStub('mail', mail_stub.MailServiceStub()) 
    return _apiproxy

class GAETestBase(unittest.TestCase):
    DEFAULT_USE_PRODUCTION_STUBS = False
    DEFAULT_USE_REMOTE_STUBS = False
    DEFAULT_CLEANUP_USED_KIND = False
    DEFAULT_KIND_PREFIX_IN_TEST = 't'
    DEFAULT_KIND_NAME_UNSWAPPED = False

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

        if hasattr(self, 'setUp'):
            self.test_setup = self.setUp
            def setup_env_and_test():
                self._env_setUp()
                self.test_setup()
            self.setUp = setup_env_and_test
        else:
            self.setUp = self._env_setUp

        if hasattr(self, 'tearDown'):
            self.test_teardown = self.tearDown
            def teardown_test_and_env():
                try:
                    self.test_teardown()
                finally:
                    self._env_tearDown()
            self.tearDown = teardown_test_and_env
        else:
            self.tearDown = self._env_tearDown

    def use_production_environment(self):
        return getattr(self.__class__, 'USE_PRODUCTION_STUBS', GAETestBase.DEFAULT_USE_REMOTE_STUBS)

    def use_remote_api(self):
        return getattr(self.__class__, 'USE_REMOTE_STUBS', GAETestBase.DEFAULT_USE_PRODUCTION_STUBS)
    
    def may_cleanup_used_kind(self):
        return getattr(self.__class__, 'CLEANUP_USED_KIND', GAETestBase.DEFAULT_CLEANUP_USED_KIND)

    def kind_prefix(self):
        return getattr(self.__class__, 'KIND_PREFIX_IN_TEST', GAETestBase.DEFAULT_KIND_PREFIX_IN_TEST) + '_'

    def use_swapped_kind_name(self):
        return not getattr(self.__class__, 'KIND_NAME_UNSWAPPED', GAETestBase.DEFAULT_KIND_NAME_UNSWAPPED)

    def swap_model_kind(self):
        self.kind_method_swapped = True
        self.original_class_for_kind_method = db.class_for_kind
        kprefix = self.kind_prefix()

        def kind_for_test_with_store_kinds(cls):
            k = kprefix + cls.__name__
            global kind_names_for_test
            if not kind_names_for_test:
                kind_names_for_test = {}
            kind_names_for_test[k] = cls
            return k

        def kind_for_test(cls):
            return kprefix + cls.__name__
            

        def class_for_kind_for_test(kind):
            if kind.find(kprefix) == 0 and db._kind_map.has_key(kind[len(kprefix):]):
                return db._kind_map[kind[len(kprefix):]]
            else:
                try:
                    return db._kind_map[kind]
                except KeyError:
                    raise KindError('No implementation for kind \'%s\'' % kind)

        if self.may_cleanup_used_kind():
            db.Model.kind = classmethod(kind_for_test_with_store_kinds)
        else:
            db.Model.kind = classmethod(kind_for_test)
        db.class_for_kind = class_for_kind_for_test

    def reswap_model_kind(self):
        def original_kind(cls):
            return cls.__name__
        db.Model.kind = classmethod(original_kind)
        db.class_for_kind = self.original_class_for_kind_method

    def _env_setUp(self):
        self.kind_method_swapped = False
        self.original_kind_method = None

        if self.may_cleanup_used_kind():
            global kind_names_for_test
            kind_names_for_test = {}

        set_environments(self)

        if self.use_swapped_kind_name():
            self.swap_model_kind()

        if is_in_production() and self.use_production_environment():
            apiproxy_stub_map.apiproxy = get_original_apiproxy_behind_gaeunit()
        elif is_in_production():
            pass # use apiproxy prepared by GAEUnit (datastore_stub is datastore_file_stub)
        elif not is_in_gaeunit() and self.use_remote_api():
            remote_api_stub.ConfigureRemoteApi(APP_ID, REMOTE_API_ENTRY_POINT,
                                               auth_func,
                                               secure=True, save_cookies=True)
            remote_api_stub.MaybeInvokeAuthentication()
        else:
            apiproxy_stub_map.apiproxy = get_dev_apiproxy()

    def delete_all_entities_of_used_kind(self):
        global kind_names_for_test
        for k in kind_names_for_test.keys():
            cls = kind_names_for_test[k]
            q = cls.all(keys_only=True)
            while True:
                l = q.fetch(100)
                if len(l) < 1:
                    break
                db.delete(l)

    def _env_tearDown(self):
        if self.may_cleanup_used_kind():
            self.delete_all_entities_of_used_kind()
            global kind_names_for_test
            del kind_names_for_test
        if self.kind_method_swapped:
            self.reswap_model_kind()
        restore_environments(self)
