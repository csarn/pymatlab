import unittest
#import mocker

from pymatlab.matlab import MatlabSession
import numpy
from numpy import eye,arange,ones,array
from numpy.random import randn
from numpy.ma.testutils import assert_equal
#from scipy.io import savemat,loadmat
from os import remove

class MatlabTestCase(unittest.TestCase):

    def setUp(self):
        self.session = MatlabSession("matlab -nojvm -nodisplay")

    def tearDown(self):
        self.session.close()

    def runOK(self):
        command="A=ones(10);"
        self.session.run(command)

    def runNOK(self):
        command="A=oxnes(10);"
        self.assertRaises(RuntimeError,self.session.run,command)

    def clear(self):
        command="clear all"
        self.session.run(command)

    def syntaxerror(self):
        command="""if 1,"""
        self.session.putstring('test',command)
        self.assertRaises(RuntimeError,self.session.run,'eval(test)')

    def longscript(self):
        command = """for i=1:10
                        sprintf('aoeu %i',i);
                     end"""
        self.session.run(command)

    def getvalue(self):
        a = ones((3,5,7,2))
        err = self.session.run("b=ones(3,5,7,2)")
        b = self.session.getvalue('b')
        assert_equal(a,b)

    def getput(self):
        for type in [
                # Disbled tests
                #"<i2",
                #"<i4",
                #"i",
                #"f",
                "d",
                ]:
            a = array([[1,2,3],[4,5,6]],dtype=type)
            self.session.putvalue('A',a)
            b = self.session.getvalue('A')
            self.assertEqual(a.dtype,b.dtype)
            assert_equal(a,b)

    def check_order_mult(self):
        a = 1.0 * numpy.array([[1, 4], [2, 5], [3, 6]])
        b = 1.0 * numpy.array([[7, 9, 11, 13], [8, 10, 12, 14]])
        s = self.session
        s.putvalue('A', a)
        s.putvalue('B', b)
        s.run("C = A*B;")
        c = s.getvalue('C')
        assert_equal(c.astype(int), numpy.dot(a, b).astype(int))

    def check_order_vector(self):
        a = 1.0 * numpy.array([[1, 4, 7], [2, 5, 8], [3, 6, 9]])
        s = self.session
        s.putvalue('A', a)
        s.run("B = A(1:9);")
        b = s.getvalue('B')
        assert_equal(b.astype(int), numpy.array([range(1, 10)]).astype(int))

def test_suite():
    tests = [
            'runOK',
            'runNOK',
            'clear',
            'syntaxerror',
            'longscript',
            'getvalue',
            'getput',
            'check_order_mult',
            'check_order_vector',
            ]
    return unittest.TestSuite(map(MatlabTestCase,tests))

