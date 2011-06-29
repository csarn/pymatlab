from ctypes import *
from numpy import array
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

class Matlab(object):
    def __init__(self,start_command):
        self.engine = CDLL('/opt/matlab/bin/glnxa64/libeng.so')
        self.mx     = CDLL('/opt/matlab/bin/glnxa64/libmx.so')
        self.ep = self.engine.engOpen(c_char_p(start_command))
        self.buf = c_char_p(" "*127)
        self.engine.engOutputBuffer(self.ep,self.buf,126)

    def __del__(self):
        self.engine.engClose(self.ep)

    def run(self,matlab_statement):
        self.engine.engEvalString(self.ep,c_char_p(matlab_statement))

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
        self.mx.mxGetClassName.restype=c_char_p
        self.mx.mxGetData.restype=POINTER(c_double)
        data =self.mx.mxGetData(mx)
        pyarray = array(data[0:numelems])
        pyarray.shape = dims[0:ndims]
        return pyarray

    def putvalue(self,name,pyvariable):
        self.mx.mxCreateNumericArray.restype=POINTER(mxArray)
        dim = pyvariable.ctypes.shape_as(c_size_t)
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
        



