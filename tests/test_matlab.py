import unittest
#import mocker

from pymatlab.matlab import MatlabSession
from numpy import eye,arange,ones
from numpy.random import randn

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
            ]
    return unittest.TestSuite(map(MatlabTestCase,tests))
            
