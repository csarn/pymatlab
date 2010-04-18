import unittest,doctest
from tests import test_matlab

def test_suite():
    return unittest.TestSuite([
        test_matlab.test_suite(),
        doctest.DocFileSuite('../../README.txt'),
        ])
            
