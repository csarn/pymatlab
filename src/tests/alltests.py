import unittest
from tests import test_matlab

def suite():
    return unittest.TestSuite([
        test_matlab.suite(),
        ])
            
