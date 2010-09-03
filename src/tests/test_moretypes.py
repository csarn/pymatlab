import unittest
#import mocker

from pymatlab.matlab import MatlabSession
import numpy
from numpy import eye,arange,ones,array
from numpy.random import randn
from numpy.ma.testutils import assert_equal
#from scipy.io import savemat,loadmat
from os import remove

class MatlabMoreTypesTestCase(unittest.TestCase):
    session = MatlabSession("matlab -nojvm -nodisplay")

    # This only works in python 2.7
    #@classmethod
    #def setUpClass(cls):
    #    cls.session = MatlabSession("matlab -nojvm -nodisplay")

    #@classmethod
    #def tearDownClass(cls):
    #    cls.session.close()


    def test_catch_int_array(self):
        s = self.session
        a = array([[1,2,3],[4,5,6]])
        self.assertRaises(TypeError,s.putvalue,'A',a)

    def test_catch_3d_array(self):
        s = self.session
        a = array([[[1]],[[6]]])
        self.assertRaises(TypeError,s.putvalue,'A',a)

    def test_putget_string(self):
        s = self.session
        s1 = 'hello world'
        s.putvalue('a','hello world')
        assert s1==s.getvalue('a')

    def test_get_struct(self):
        s = self.session
        s1 = [{'x': numpy.array([[ 0.]]), 'y': numpy.array([[ 1.,  2.,  3.]])}]
        s.run("s = struct('x',0,'y',[1 2 3])")
        q = s.getvalue('s')
        # check congruency
        for e1,e2 in zip(s1,q):
            for ee1,ee2 in zip(e1,e2):
                assert numpy.all(ee1==ee2)


    def test_get_struct_fieldnames_ascell(self):
        s = self.session
        s1 = [{'x': numpy.array([[ 0.]]), 'y': numpy.array([[ 1.,  2.,  3.]])}]
        s.run("s = struct('x',0,'y',[1 2 3])")
        s.run("fieldnames(s)")
        q = s.getvalue('ans')
        assert q==['x', 'y']

    def test_putget_cell(self):
        s = self.session
        cell = ['x','y']
        s.putvalue('c',cell)
        q = s.getvalue('c')
        assert q==cell



    def test_putget_struct(self):
        s = self.session
        s1 = [{'x': numpy.array([[ 0.]]), 'y': numpy.array([[ 1.,  2.,  3.]])}]
        s.putvalue('s',s1)
        q = s.getvalue('s')
        # check congruency
        for e1,e2 in zip(s1,q):
            for ee1,ee2 in zip(e1,e2):
                assert numpy.all(ee1==ee2)




    def test_putget_empty_struct(self):
        s = self.session
        s.run("s = struct()")
        q = s.getvalue('s')
        # check congruency
        assert q == [{}]

        s.putvalue('s',[{}])
        q = s.getvalue('s')
        # check congruency
        assert q == [{}]

    def test_get_sparse(self):
        import scipy.sparse as sparse
        s = self.session

        s.run("s = sparse([1,5],[2,7],[4.4,3.1],10,11,10)")
        q = s.getvalue("s")

        sp = sparse.csc_matrix(q[:3],shape=q[3])
        
        s.putvalue("pys",sp.toarray())
        s.run("all(all(pys==s))")
        
        ans = s.getvalue("ans")
        assert ans


    def test_getput_sparse(self):
        import scipy.sparse as sparse
        s = self.session

        s.run("s = sparse([1,5],[2,7],[4.4,3.1],10,11,10)")
        q = s.getvalue("s")

        sp = sparse.csc_matrix(q[:3],shape=q[3])
        
        s.putvalue("pys",sp.toarray())
        s.run("all(all(pys==s))")
        
        ans = s.getvalue("ans")
        assert ans

        # ok we've got matching matlab and python
        # now try putting python back to matlab

        tup = q

        s.putvalue("s_from_py",q) 
        s.run("all(all(s_from_py==s))")
        
        ans = s.getvalue("ans")
        assert ans
       
        



    def test_put_scalars(self):

        s = self.session

        s.putvalue('a',2)
        assert s.getvalue('a') == numpy.array([2.])
        s.putvalue('a',1.)
        assert s.getvalue('a') == numpy.array([1.])


    def test_getput_logical(self):

        s = self.session

        s.run("l = true")
        l = s.getvalue("l")
        assert l==True

        s.putvalue("l",l)
        x = s.getvalue("l")
        assert l==x
        
        
        s.run("l = false")
        l = s.getvalue("l")
        assert l==False

        s.putvalue("l",l)
        x = s.getvalue("l")
        assert l==x





def test_suite():

    suite = unittest.makeSuite(MatlabMoreTypesTestCase,'test')
    return suite



if __name__ == "__main__":

    # unittest.main()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite())
