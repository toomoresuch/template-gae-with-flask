# -*- coding: utf-8 -*-

import unittest
import application


class ExampleTest(unittest.TestCase):

    def setUp(self):
        self.application = application.app.test_client()

    def test_default_page(self):
        app = self.application
        response = app.get('/')
        self.assertEqual('200 OK', response.status)



