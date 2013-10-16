from ctypes import *
from numpy import array,ndarray,dtype
from os.path import join
import platform
import sys,numpy

class mxArray(Structure):
    pass

def numpy_to_ctype(np_variable):
    dtype = str(np_variable.dtype)
    ctype = c_double
    if "int" in dtype:
        if '8' in dtype:
            ctype = c_short
        elif '16' in dtype:
            ctype = c_short
        elif '32' in dtype:
            ctype = c_int
        elif '64' in dtype:
            ctype = c_long
    elif "float" in dtype:
        if '32' in dtype:
            ctype = c_float
        elif '64' in dtype:
            ctype = c_double
        else:
            ctype = c_double
    return ctype

def mat_to_ctype(classname):
    dtype = classname
    ctype = c_double
    if "int" in dtype:
        if '8' in dtype:
            ctype = c_short
        elif '16' in dtype:
            ctype = c_short
        elif '32' in dtype:
            ctype = c_int
        elif '64' in dtype:
            ctype = c_long
    elif "single" in dtype:
        ctype = c_float
    elif "double" in dtype:
        ctype = c_double
    return ctype


def np_to_mat(np_variable):
    
    #Typedef enum
    #{
    #0        mxUNKNOWN_CLASS = 0,
    #1        mxCELL_CLASS,
    #2        mxSTRUCT_CLASS,
    #3        mxLOGICAL_CLASS,
    if np_variable.dtype.type ==numpy.bool:
        matlab_type = c_int(3)
    #4        mxCHAR_CLASS,
    elif np_variable.dtype.type ==numpy.str :
        matlab_type = c_int(4)
    #5        mxVOID_CLASS,
    elif np_variable.dtype.type ==numpy.void:
        matlab_type = c_int(5)
    #6        mxDOUBLE_CLASS,
    elif np_variable.dtype.type ==numpy.float64: 
        matlab_type = c_int(6)
    #7        mxSINGLE_CLASS,
    elif np_variable.dtype.type ==numpy.float32: 
        matlab_type = c_int(7)
    #8        mxINT8_CLASS,
    elif np_variable.dtype.type ==numpy.int8: 
        matlab_type = c_int(8)
    #9        mxUINT8_CLASS,
    elif np_variable.dtype.type ==numpy.uint8: 
        matlab_type = c_int(9)
    #10       mxINT16_CLASS,
    elif np_variable.dtype.type ==numpy.int16: 
        matlab_type = c_int(10)
    #11       mxUINT16_CLASS,
    elif np_variable.dtype.type ==numpy.uint16: 
        matlab_type = c_int(11)
    #12       mxINT32_CLASS,
    elif np_variable.dtype.type ==numpy.int32: 
        matlab_type = c_int(12)
    #13       mxUINT32_CLASS,
    elif np_variable.dtype.type ==numpy.uint32: 
        matlab_type = c_int(13)
    #14       mxINT64_CLASS,
    elif np_variable.dtype.type ==numpy.int64: 
        matlab_type = c_int(14)
    #15       mxUINT64_CLASS,
    elif np_variable.dtype.type ==numpy.uint64: 
        matlab_type = c_int(15)
    #16       mxFUNCTION_CLASS,
    #17       mxOPAQUE_CLASS,
    #18       mxOBJECT_CLASS, /* keep the last real item in the list */
    #        #if defined(_LP64) || defined(_WIN64)
    #        mxINDEX_CLASS = mxUINT64_CLASS,
    #        #else
    #        mxINDEX_CLASS = mxUINT32_CLASS,
    #        #endif
    #        /* TEMPORARY AND NASTY HACK UNTIL mxSPARSE_CLASS IS COMPLETELY ELIMINATED */
    #        mxSPARSE_CLASS = mxVOID_CLASS /* OBSOLETE! DO NOT USE */
    #        }
    else:
        matlab_type = c_int(5) #VOID_CLASS
    #MxClassID;
    return matlab_type


wrap_script = '''
pymatlaberrstring ='';
try
    {0}
catch err
    pymatlaberrstring = sprintf('Error: %s with message: %s\\n',err.identifier,err.message);
    for i = 1:length(err.stack)
        pymatlaberrstring = sprintf('%%sError: in fuction %%s in file %%s line %%i\\n',pymatlaberrstring,err.stack(i,1).name,err.stack(i,1).file,err.stack(i,1).line);
    end
end
if exist('pymatlaberrstring','var')==0
    pymatlaberrstring='';
end
'''
class MatlabSession(object):
    def __init__(self,matlab_root='',command='',bufsize=128):
        system = platform.system()
        if system=='Linux' or system=='Darwin':
            self.engine = CDLL(join(matlab_root,'bin','glnxa64','libeng.so'))
            self.mx = CDLL(join(matlab_root,'bin','glnxa64','libmx.so'))
            self.ep = self.engine.engOpen(c_char_p(command))
        elif system=='Windows':
            self.engine = CDLL(join(matlab_root,'bin','glnxa64','libeng.dll'))
            self.mx = CDLL(join(matlab_root,'bin','glnxa64','libmx.dll'))
            self.ep = self.engine.engOpen(None)
        else:
            raise NotSupportedException(
                    'system {} not yet supported'.format(system))
        if self.ep is None:
            raise RuntimeError(
                  'Could not start matlab using command "{}"'.format(command))
        self.buff_length = bufsize
        if self.buff_length!=0:
	    self.buf = create_string_buffer(self.buff_length)
            self.engine.engOutputBuffer(self.ep,self.buf,self.buff_length-1)

    def __del__(self):
        self.engine.engClose(self.ep)

    def run(self,matlab_statement):
        #wrap statement to be able to catch errors
        real_statement = wrap_script.format(matlab_statement)
        self.engine.engEvalString(self.ep,c_char_p(real_statement))
        self.engine.engGetVariable.restype=POINTER(mxArray)
        mxresult = self.engine.engGetVariable(
                self.ep,c_char_p('pymatlaberrstring'))
        self.mx.mxArrayToString.restype=c_char_p
        error_string = self.mx.mxArrayToString(mxresult)
        if error_string <> "":
            raise(RuntimeError('Error from Matlab: {0}'.format(
                error_string)))

    def getvalue(self,variable):
        self.engine.engGetVariable.restype=POINTER(mxArray)
        mx = self.engine.engGetVariable(self.ep,c_char_p(variable))
        self.mx.mxGetNumberOfDimensions.restype=c_size_t
        ndims = self.mx.mxGetNumberOfDimensions(mx)
        self.mx.mxGetDimensions.restype=POINTER(c_size_t)
        dims = self.mx.mxGetDimensions(mx)
        self.mx.mxGetNumberOfElements.restype=c_size_t
        numelems = self.mx.mxGetNumberOfElements(mx)
        self.mx.mxGetElementSize.restype=c_size_t
        elem_size = self.mx.mxGetElementSize(mx)
        self.mx.mxGetClassName.restype=c_char_p
        class_name = self.mx.mxGetClassName(mx)
        if class_name=='char':
            length = numelems+2
            return_str = create_string_buffer(length)
            self.mx.mxGetString(mx, return_str, length-1);
            return return_str.value
        else:
            returntype = mat_to_ctype(class_name)
            returnsize = numelems*elem_size
            self.mx.mxGetData.restype=POINTER(returntype)
            data =self.mx.mxGetData(mx)
            buf =create_string_buffer(returnsize)
            memmove(buf,data,returnsize)
            pyarray = ndarray(buffer=buf,shape=dims[:ndims], 
                    dtype=dtype(returntype),order='F')
            return pyarray.squeeze()

    def putvalue(self,name,pyvariable):
        if type(pyvariable)==str:
            self.mx.mxCreateString.restype=POINTER(mxArray)
            mx = self.mx.mxCreateString(c_char_p(pyvariable))
        else:
            if not type(pyvariable)==ndarray:
                pyvariable = array(pyvariable)
            dim = pyvariable.ctypes.shape_as(c_size_t)
            self.mx.mxCreateNumericArray.restype=POINTER(mxArray)
            mx = self.mx.mxCreateNumericArray(c_size_t(pyvariable.ndim),
                    dim,
                    np_to_mat(pyvariable),
                    c_int(0))
            #self.mx.mxGetData.restype=POINTER(numpy_to_ctype(pyvariable))
            self.mx.mxGetData.restype=POINTER(c_void_p)
            data_old = self.mx.mxGetData(mx)
            datastring = pyvariable.tostring('F')
            n_datastring = len(datastring)
            memmove(data_old,datastring,n_datastring)
            
    
        self.engine.engPutVariable(self.ep,c_char_p(name),mx)
