import unittest,doctest
from tests import t_matlab
from tests import t_pymatlab

def test_suite():
    return unittest.TestSuite([
        t_matlab.test_suite(),
#        doctest.DocFileSuite('../../README.txt'),
        ])
            
