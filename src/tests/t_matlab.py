import unittest
#import mocker

import sys
from pymatlab.matlab import MatlabSession
import numpy
from numpy import eye,arange,ones,array,ndarray
from numpy.random import randn
from numpy.ma.testutils import assert_equal,assert_almost_equal
from StringIO import StringIO
#from scipy.io import savemat,loadmat

class MatlabTestCase(unittest.TestCase):

    def setUp(self):
        self.session = MatlabSession("matlab -nojvm -nodisplay")
        
    def runOK(self):
        command="A=ones(10);"
        self.session.run(command)

    def runNOK(self):
        command="A=oxes(10);"
        self.assertRaises(RuntimeError,self.session.run,command)

    def clear(self):
        command="clear all"
        self.session.run(command)

    def syntaxerror(self):
        command="""if 1,"""
        self.session.putvalue('test',command)
        self.assertRaises(RuntimeError,self.session.run,'eval(test)')

    def longscript(self):
        command = """for i=1:10
                        sprintf('aoeu %i',i);
                     end"""
        self.session.run(command)

    def getvalue(self):
        a = ones((5,3,7,4),dtype='double')
        err = self.session.run("b=ones(5,3,7,4)")
        b = self.session.getvalue('b')
        assert_equal(a,b)

    def putvalue(self):
        a = randn(2,3)
        self.session.putvalue('a',a)
        self.session.run('a')
        buf = self.session.buf.value
        vector = buf.split()
        data = [float(i) for i in vector[-6:]]
        buf=array(data)
        buf.shape=(2,3)
        assert_almost_equal(a,buf,4)

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
    # Want to run them in a certain order...
    tests = [
            'runOK',
            'runNOK',
            'clear',
            'syntaxerror',
            'longscript',
            'getvalue',
            'putvalue',
            'getput',
            'check_order_mult',
            'check_order_vector',
            ]
    return unittest.TestSuite(map(MatlabTestCase,tests))

