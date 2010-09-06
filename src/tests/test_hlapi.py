import unittest
#import mocker

from pymatlab import Session, Container
import pymatlab
import numpy
import scipy.sparse
from numpy import eye,arange,ones,array
from numpy.random import randn
from numpy.ma.testutils import assert_equal
#from scipy.io import savemat,loadmat
from os import remove

class MatlabHLAPITestCase(unittest.TestCase):
    session = Session("matlab -nojvm -nodisplay")

    # This only works in python 2.7
    #@classmethod
    #def setUpClass(cls):
    #    cls.session = MatlabSession("matlab -nojvm -nodisplay")

    #@classmethod
    #def tearDownClass(cls):
    #    cls.session.close()


    def test_eval(self):
        s = self.session
        s.run("s = struct()")
        s.eval("size(s)")
        s.run("s=reshape(s,[2 3])")
        assert numpy.alltrue(s.eval("size(s)")==numpy.array([[2.0, 3.0]]))


    def test_shape(self):

        s = self.session

        # a cell array
        c = Container(['x','y','z','w'],size=numpy.array([[2., 2.]]))

        s.put('c',c)
        size = s.eval("size(c)")
        assert numpy.alltrue(size==c.size)


    def test_funcwrap(self):
        
        s = self.session
        rand = s.func_wrap('rand')
        x = rand(numpy.array([[10, 1.]]))
        assert x.shape == (10,1)

    def test_funcwrap_null(self):
        """ tests if functions returning null in MATLAB
        also do so in Python """

        s = self.session
        a = s.clear('ans')
        assert a==None

    def test_funcwrap_figure_retval(self):
        """ tests if figure functions return values are ok"""

        s = self.session
        a = s.figure()
        assert a==s.gcf()
        # this is the matlab function "close", not the session._close()!
        s.close()


    def test_append_path(self):
        s = self.session
        path = s.path()
        s.path(append=['/home','/var'])
        path = s.path()
        assert path[-2:]==['/home','/var']

    def test_scipy_sparse_matrix(self):
        a = scipy.sparse.lil_matrix((10,11))
        a[4,5] = 1.1
        a[9,10] = 2.0
        a_csc = a.tocsc()
        s = self.session
        s.put('a_sp',a_csc)
        m_a_csc = s.get('a_sp')
        assert numpy.all(a.toarray() == a_csc.toarray())

        self.assertRaises(TypeError,s.putvalue,'a_sp',a)

    def test_funcwrap_converter(self):
        
        s = self.session
        sparse = s.func_wrap('sparse',converters=[pymatlab.csc_matrix_converter])
        e = numpy.array([])
        sp = sparse(e,e,e,10,10,10)
        assert isinstance(sp,scipy.sparse.csc_matrix)
        assert sp.shape == (10,10)

        rand = s.func_wrap('rand',converters=lambda x: x.flatten().tolist())
        x = rand(1,10)
        assert isinstance(x,list)
        assert len(x) == 10

    def test_funcwrap_multiple_converters(self):
        
        s = self.session

        def tolist(x):
            try:
                return x.flatten().tolist()
            except:
                raise TypeError
        
        converters = [pymatlab.csc_matrix_converter, tolist]
        sparse = s.func_wrap('sparse',converters=converters)
        e = numpy.array([])
        sp = sparse(e,e,e,10,10,10)
        assert isinstance(sp,scipy.sparse.csc_matrix)
        assert sp.shape == (10,10)

        rand = s.func_wrap('rand',converters=converters)
        x = rand(1,10)
        assert isinstance(x,list)
        assert len(x) == 10


    def test_help(self):
        s = self.session
        h = s.help('help')
        assert isinstance(h,str)
        assert 'HELP Display help text in Command Window' in h

    def test_isa(self):

        s = self.session
        s.run("f = @(x) x.^2")
        assert s.isa('f','function_handle')
        #s.putvalue('f',True)
        s.run("f = [true]")
        assert s.isa('f', 'logical')
        s.putvalue('f',True)
        assert s.isa('f', 'logical')
        s.putvalue('f',False)
        assert s.isa('f', 'logical')

    def test_isfunc(self):
        s = self.session
        s.run("f = @(x) x.^2")
        assert s.isfunc('f')
        s.put('f',True)
        assert s.isfunc('f')==False
        assert s.isfunc('rand')

    def test_isvar(self):
        s = self.session
        s.run("f = @(x) x.^2")
        assert s.isvar('f')
        s.put('f',True)
        assert s.isvar('f')

        s.run("clear('f')")
        assert s.isvar('f')==False
        s.run("clear('rand')")
        assert s.isvar('rand')==False
        


    def test_attr_lookup(self):

        s = self.session
        s.run("f = @(x) x.^2")
        assert s.f(2.0)==4.0

        x = s.rand(10,11)
        assert x.shape == (10,11)

        e = s.exp(1)
        s.run("my_pi=pi()")
        pi = s.my_pi
        assert numpy.allclose(e**pi,s.exp(s.my_pi))

    def test_setattr(self):

        s = self.session
        s.x = s.rand(10,11)
        assert s.x.shape == (10,11)

        e = s.exp(1)
        s.my_pi = s.pi()
        pi = s.my_pi
        assert numpy.allclose(e**pi,s.exp(s.my_pi))

    def test_default_converters(self):
        
        def get_cont_data(cont):
            if isinstance(cont,pymatlab.Container):
                return cont.data
            else:
                raise TypeError
        
        s = self.session
        s.converters = [get_cont_data]
        # this lookup creates a FuncWrap object
        # which will use s.converters
        s.run("f = @(x) x.rnames")
        f = s.f

        # test data
        struct = [{'rnames':['axon','dend']}]
        ans = f(struct)
        s.converters = []
        assert ans==['axon','dend']


def test_suite():

    suite = unittest.makeSuite(MatlabHLAPITestCase,'test')
    return suite



if __name__ == "__main__":

    # unittest.main()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite())
