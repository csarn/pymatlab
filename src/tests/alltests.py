import unittest
from tests import test_matlab, doctests

def suite():
    return unittest.TestSuite([
        test_matlab.test_suite(),
        doctests.test_suite(),
        ])
            
