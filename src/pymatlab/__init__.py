
import scipy.sparse
import numpy
from pymatlab.matlab import MatlabSession as _MatlabSession



def valid_matlab_symbol(name):
    """ some basic tests (no complete) to check if symbol name
    is valid in MATLAB"""

    invalid_chars = """()""'[] """
    invalid_prefixes = '_()[]'
    
    if name[0] in invalid_prefixes:
        return False

    for c in invalid_chars:
        if c in name:
            return False

    return True
    


class SymbProxy(object):
    def __init__(self,symbol):
        self.symbol = symbol


class Sparse(object):
    """

    An object for Matlab Sparse Matrices
    which knows how to convert itself to a scipy.sparse.csc_matrix.


    Given:
      scipy.sparse.csc_matrix((data,indices,indptr))
      data,indices,indptr are analagous to MATLAB sparse matrix (pr,ir,jc)

    """
    

    def __init__(self,data):
        pass
        


class Container(object):
    """ Container

    This class is used when a cell or struct array is returned,
    so that it can store extra meta information, such as size.

    Also, it should allow analagous indexing and attribute lookup
    as the matlab equivalent.


    """

    def __init__(self,data,size):
        self.data = data
        self.size = size


class FuncWrap(object):
    """ 
    s = MatlabSession(...)
    rand = FuncWrap(s,'rand')
    rand([10])
    

    """

    # These are matlab functions that
    # return a value but only if
    # one explicitly calls them as
    # ans = func(args)
    explicit_ans = ['figure','close']

    def __init__(self,session,func_name,converters=None):
        """constructs a proxy to a matlab function.
        
        converters is a callable or list of callables which 
        accept the return value of the matlab function "ans" 
        and return a value, or raise TypeError on failure
        to pass to the next converter in the list.

        If arguments passed to the wrapped function define
        the "to_matlab" member, it will be called and its return
        value passed to MATLAB.
        
        Example:

        sample_tree = s.func_wrap('sample_tree',
                                  converter=lambda x: return Tree(x))

        """


        self.session = session
        self.func_name = func_name
        self.converters = converters

    def __call__(self,*args):
        arg_list = []
        arg_count = 0
        for x in args:
            if isinstance(x,SymbProxy):
                arg_list.append(x.symbol)
            else:
                symbol = "pymatlab_arg_%i" % arg_count
                self.session.put(symbol,x)
                arg_list.append(symbol)
                arg_count+=1
        # set ans to 'NoneNULLvoid'
        self.session.putvalue("ans","NoneNULLvoid")        
        # Some functions do not implicitly set return
        # value in ans, so let's explicitly do it.
        if self.func_name in self.explicit_ans:
            self.session.run("ans = "+self.func_name+"(%s)" % ", ".join(arg_list))
        else:
            self.session.run(self.func_name+"(%s)" % ", ".join(arg_list))
            

        # did ans get cleared? Yes, then return None
        if self.session.isvar("ans"):
            r = self.session.get("ans",converters = self.converters)
        else:
            return None

        # Did ans get written to?  No, then return None
        if  r == 'NoneNULLvoid':
            return None
        else:
            return r

def csc_matrix_converter(sp_matrix):
    """ Takes the (pr,ir,jc,shape) repr of a sparse matrix 
    returned from MATLAB and creates a scipy.sparse.csc_matrix
    from it 
    
    example:

    sparse = s.func_wrap('sparse',converters=[csc_matrix_converter])
    e = numpy.array([])
    s = sparse(e,e,e,10,10,10)
    isinstance(s,scipy.sparse.csc_matrix) -> True

    """

    sp = sp_matrix
    if isinstance(sp, scipy.sparse.csc_matrix):
        # was already converted somehow, don't care how
        return sp
    elif isinstance(sp,tuple) and len(sp)==4:
        # raw from matlab
        return scipy.sparse.csc_matrix(sp[:3],shape=sp[3])
    elif isinstance(sp,scipy.sparse.spmatrix):
        return sp.tocsc()
    else:
        raise TypeError, "csc_matrix_converter: don't know how to convert supplied type %s" % str(type(sp))

        


class Session(object):

    # converters are the user overridable default converters 
    # for self.func_wrap
    non_parameter_attributes = ['converters','_session']
    converters = []

    def __init__(self,matlab_cmd=None,*args,**kwargs):
        if matlab_cmd==None:
            matlab_cmd = "matlab -nosplash -nodesktop"
        self._session = _MatlabSession(matlab_cmd,*args,**kwargs)

    def __del__(self):
        if not self._closed():
            print "Closing MATLAB session."
            self._close()


    def run(self,expr):
        self._session.run(expr)

    def getvalue(self,expr):
        return self._session.getvalue(expr)

    def putvalue(self,expr,val):
        self._session.putvalue(expr,val)

    def _close(self):
        """ Close the MATLAB session. """
        self._session.close()

    def _closed(self):
        """ Check if the MATLAB session is closed."""
        return self._session.closed()

    def eval(self,expr):

        self.run(expr)
        return self.get('ans')

    def get(self,var,converters = None):
        """ provided converters OVERRIDE instance converters """
        
        if converters==None:
            converters = self.converters
        else:
            if not hasattr(converters,'__iter__'):
                converters = [converters]

        v = self.getvalue(var)
        # some hard coded converters
        if isinstance(v,list):
            size = self.eval('size(%s)' % var)
            v = Container(v,size)
        elif isinstance(v,tuple) and len(v)==4:
            v = scipy.sparse.csc_matrix(v[:3],shape=v[3])
        
        # user defined converters are now applied in order
        # first to succeed breaks
        for conv in converters:
            try:
                new_v = conv(v)
                # convert if succesful and break
                v = new_v
                break
            except TypeError:
                pass
        # there is no need for any converters to succeed!
        return v

    def put(self,var,val):
        # hard coded "to_matlab" conversions
        if isinstance(val,Container):
            self.putvalue(var,val.data)
            self.putvalue('py_pymatlab_temp_size',val.size)
            self.run('%s=reshape(%s,py_pymatlab_temp_size)' % (var,var))
        elif isinstance(val,scipy.sparse.spmatrix):
            # spase matrix
            if not isinstance(val,scipy.sparse.csc_matrix):
                # only support csc_matrix to be consistent
                # with return value of get
                raise TypeError, "Please convert sparse matrix type '%s' to scipy.sparse.csc_matrix." % val.__class__
            t = (val.data,val.indices,val.indptr,numpy.array(val.shape,dtype=numpy.int32))
            self.putvalue(var,t)

        elif isinstance(val,scipy.sparse.lil_matrix):
            raise TypeError, "scipy.sparse.lil_matrix unsupported.  Please use scipy.sparse.csc_matrix." 
        
        # user defined "to_matlab" conversions
        elif hasattr(val,'to_matlab'):
            self.putvalue(var,val.to_matlab())

        #fallback
        else:
            self.putvalue(var,val)
            

    def func_wrap(self,func_name,converters=None):
        """ returns a FuncWrap object for the function func_name in this session.

        Provided arg 'converters' are passed to FuncWrap constructor
"""

        return FuncWrap(self,func_name,converters)

        
    def path(self,append=None):
        """ returns the matlab path

        if append is not None, it should be a list of
        paths (as strings) to append to the path """
        if append:
            for path in append:
                self.run("path(path,'%s')"%path)
        
        self.run("ans=path")
        p = self.getvalue("ans")
        return p.split(':')

    def help(self,name):

        return self.eval("ans = help('%s')" % name)

    def isa(self,var,type_str):
        """ 
calls MATLAB isa function on var:

MATLAB docs:
        
 ISA    True if object is a given class.
    ISA(OBJ,'classname') returns true if OBJ is an instance of 'classname'.
    It also returns true if OBJ is an instance of a class that is derived 
    from 'classname'.
 
    Some possibilities for 'classname' are:
      double          -- Double precision floating point numeric array
                         (this is the traditional MATLAB matrix or array)
      logical         -- Logical array
      char            -- Character array
      single          -- Single precision floating-point numeric array
      float           -- Double or single precision floating-point numeric array
      int8            -- 8-bit signed integer array
      uint8           -- 8-bit unsigned integer array
      int16           -- 16-bit signed integer array
      uint16          -- 16-bit unsigned integer array
      int32           -- 32-bit signed integer array
      uint32          -- 32-bit unsigned integer array
      int64           -- 64-bit signed integer array
      uint64          -- 64-bit unsigned integer array
      integer         -- An array of any of the 8 integer classes above
      numeric         -- Integer or floating-point array
      cell            -- Cell array
      struct          -- Structure array
      function_handle -- Function Handle
      <classname>     -- Any MATLAB or Java class
 
    See also ISNUMERIC, ISLOGICAL, ISCHAR, ISCELL, ISSTRUCT, ISFLOAT,
             ISINTEGER, ISOBJECT, ISJAVA, ISSPARSE, ISREAL, CLASS.

    Overloaded methods:
       scribehandle/isa
       serial/isa
       fxptds.isa
       instrument/isa
       icinterface/isa
       icgroup/isa
       icdevice/isa
       rptcp/isa
       rptsp/isa

    doc isa
"""
        return self.eval("isa(%s,'%s')" % (var,type_str))
    



    def isfunc(self,name):
        """ returns true if name is a defined function or
        function handle in MATLAB world."""

        self.run("py_ans=which('%s')" % name)
        path = self.get("py_ans")
        if path=='variable':
            return self.isa(name, 'function_handle')
        else:
            return bool(path)

    def isvar(self,name):
        """ returns true if name is a defined variable the in MATLAB world."""

        self.run("py_ans=which('%s')" % name)
        path = self.get("py_ans")
        if path=='variable':
            return True
        else:
            return False

    def __getattr__(self,name):
        # do class lookup first
        # if fail, do MATLAB lookup

      
        # NB: __getattr__() will not be called unless __getattribute__()
        # either calls it explicitly or raises an AttributeError.

        # but somehow s.help('help') is doing a matlab symbol lookup
        # so explicitly try a class lookup here
        try:
            return self.__getattribute__(name)
        except AttributeError as e:
            pass

        if not valid_matlab_symbol(name):
            raise AttributeError, "Symbol '%s' is not a valid MATLAB symbol." % name
        
        if self.isfunc(name):
            f = self.func_wrap(name)
            f.__doc__ = self.help(name)
            return f
        elif self.isvar(name):
            return self.get(name)
        else:
            raise AttributeError, "Symbol '%s' is not defined in MATLAB session." % name

    def __setattr__(self,name,value):

        if name in self.non_parameter_attributes:
            object.__setattr__(self, name, value)
        else:
            self.put(name,value)
