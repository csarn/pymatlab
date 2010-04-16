import unittest
#import mocker

from pymatlab.matlab import MatlabSession
import numpy
from numpy import eye,arange,ones
from numpy.random import randn
from numpy.ma.testutils import assert_equal

class MatlabTestCase(unittest.TestCase):

    def setUp(self):
        self.session = MatlabSession("matlab -nojvm -nodisplay")

    def tearDown(self):
        self.session.close()

    def runOK(self):
        command="A=ones(10);"
        string = self.session.run(command)
        self.assertEqual(string,"")

    def runNOK(self):
        command="A=oxnes(10);"
        string = self.session.run(command)
        self.assertNotEqual(string,"")

    def clear(self):
        command="clear all"
        string = self.session.run(command)
        self.assertEqual(string,"")

    def syntaxerror(self):
        command="""if 1,"""
        self.session.putstring('test',command)
        string = self.session.run('eval(test)')
        self.assertNotEqual(string,"")

    def longscript(self):
        command = """for i=1:10
                        sprintf('aoeu %i',i);
                     end"""
        string = self.session.run(command)
        self.assertEqual(string,"")

    def getvalue(self):
        self.session.run('A=eye(10)')
        b = eye(10)
        a = self.session.getvalue('A')
        self.assertTrue((a==b).all())

    def getvalueX(self):
        self.session.run('A=ones(10,10,10)')
        b = ones((10,10,10))
        a = self.session.getvalue('A')
        self.assertTrue((a==b).all())

    def getput(self):
        a = randn(10,5,30)
        self.session.putvalue('A',a)
        b = self.session.getvalue('A')
        self.assertTrue((a==b).all())

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

def suite():
    tests = [
            'runOK',
            'runNOK',
            'clear',
            'syntaxerror',
            'longscript',
            'getvalue',
            'getvalueX',
            'getput',
            'check_order_mult',
            'check_order_vector',
            ]
    return unittest.TestSuite(map(MatlabTestCase,tests))

