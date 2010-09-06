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

    def test_runOK(self):
        command="A=ones(10);"
        self.session.run(command)

    def test_runNOK(self):
        command="A=oxnes(10);"
        self.assertRaises(RuntimeError,self.session.run,command)

    def test_clear(self):
        command="clear all"
        self.session.run(command)

    def test_longscript(self):
        command = """for i=1:10
                        sprintf('aoeu %i',i);
                     end"""
        self.session.run(command)

    def test_getvalue(self):
        a = ones((3,5,7,2))
        err = self.session.run("b=ones(3,5,7,2)")
        b = self.session.getvalue('b')
        assert_equal(a,b)

    def test_getput(self):
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

    def test_check_order_mult(self):
        a = 1.0 * numpy.array([[1, 4], [2, 5], [3, 6]])
        b = 1.0 * numpy.array([[7, 9, 11, 13], [8, 10, 12, 14]])
        s = self.session
        s.putvalue('A', a)
        s.putvalue('B', b)
        s.run("C = A*B;")
        c = s.getvalue('C')
        assert_equal(c.astype(int), numpy.dot(a, b).astype(int))

    def test_check_order_vector(self):
        a = 1.0 * numpy.array([[1, 4, 7], [2, 5, 8], [3, 6, 9]])
        s = self.session
        s.putvalue('A', a)
        s.run("B = A(1:9);")
        b = s.getvalue('B')
        assert_equal(b.astype(int), numpy.array([range(1, 10)]).astype(int))

    def test_closing(self):

        s = MatlabSession("matlab -nojvm -nodisplay")
        assert s.closed()==False
        # check that we can call s.close more that once
        # and it is gracefull
        s.close()
        s.close()
        s.close()
        assert s.closed()
        self.assertRaises(RuntimeError,s.run,'x=1')
        self.assertRaises(RuntimeError,s.putvalue,'x',1)
        self.assertRaises(RuntimeError,s.getvalue,'x')



def test_suite():

    suite = unittest.makeSuite(MatlabTestCase,'test')
    return suite



if __name__ == "__main__":

    # unittest.main()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite())
