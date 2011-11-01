from ctypes import *
from numpy import array,ndarray
import sys

class mxArray(Structure):
    pass
#Typedef enum
#{
#        mxUNKNOWN_CLASS = 0,
#        mxCELL_CLASS,
#        mxSTRUCT_CLASS,
#        mxLOGICAL_CLASS,
#        mxCHAR_CLASS,
#        mxVOID_CLASS,
#        mxDOUBLE_CLASS,
#        mxSINGLE_CLASS,
#        mxINT8_CLASS,
#        mxUINT8_CLASS,
#        mxINT16_CLASS,
#        mxUINT16_CLASS,
#        mxINT32_CLASS,
#        mxUINT32_CLASS,
#        mxINT64_CLASS,
#        mxUINT64_CLASS,
#        mxFUNCTION_CLASS,
#        mxOPAQUE_CLASS,
#        mxOBJECT_CLASS, /* keep the last real item in the list */
#        #if defined(_LP64) || defined(_WIN64)
#        mxINDEX_CLASS = mxUINT64_CLASS,
#        #else
#        mxINDEX_CLASS = mxUINT32_CLASS,
#        #endif
#        /* TEMPORARY AND NASTY HACK UNTIL mxSPARSE_CLASS IS COMPLETELY ELIMINATED */
#        mxSPARSE_CLASS = mxVOID_CLASS /* OBSOLETE! DO NOT USE */
#        }
#MxClassID;
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
    def __init__(self,start_command):
        self.engine = CDLL('/opt/matlab/bin/glnxa64/libeng.so')
        self.mx     = CDLL('/opt/matlab/bin/glnxa64/libmx.so')
        self.ep = self.engine.engOpen(c_char_p(start_command))
        buff_length = 8*1024
        self.buf = create_string_buffer(buff_length)
        self.engine.engOutputBuffer(self.ep,self.buf,buff_length-1)

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
        numelems = 1
        for i in range(ndims):
            numelems = numelems*dims[i]
        #self.mx.mxGetClassName.restype=c_char_p
        returntype = c_double
        self.mx.mxGetData.restype=POINTER(returntype)
        data =self.mx.mxGetData(mx)
        data_array=array( data[:numelems])
        #pyarray = ndarray(dims[:ndims],'float64',data,order='F')
        #return array(range(10,20))
        return ndarray(buffer=data_array,shape=dims[:ndims],order='F')

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
                    c_int(6),
                    c_int(0))
            data_old = self.mx.mxGetData(mx)
            if pyvariable.flags.f_contiguous:
                tmp = pyvariable
            else:
                tmp = array(pyvariable,order='F')
            self.mx.mxSetData(mx,tmp.ctypes.data)
            self.mx.mxFree(data_old)
    
        self.engine.engPutVariable(self.ep,c_char_p(name),mx)
