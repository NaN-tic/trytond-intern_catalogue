# This file is part intern_catalogue module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
import doctest
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import suite as test_suite
from trytond.tests.test_tryton import doctest_teardown
from trytond.tests.test_tryton import doctest_checker


class InternCatalogueTestCase(ModuleTestCase):
    'Test Intern Catalogue module'
    module = 'intern_catalogue'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            InternCatalogueTestCase))
    suite.addTests(doctest.DocFileSuite(
            'scenario_intern_catalogue.rst',
            tearDown=doctest_teardown, encoding='utf-8',
            checker=doctest_checker,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
