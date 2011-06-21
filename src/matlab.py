from ctypes import *
from numpy import array
import sys

class mxArray(Structure):
    pass

class Matlab(object):
    def __init__(self,start_command):
        self.engine = CDLL('/opt/matlab/bin/glnxa64/libeng.so')
        self.mx     = CDLL('/opt/matlab/bin/glnxa64/libmx.so')
        self.ep = self.engine.engOpen(c_char_p(start_command))
        self.buf = c_char_p(" "*12)
        self.engine.engOutputBuffer(self.ep,self.buf,11)

    def __del__(self):
        self.engine.engClose(self.ep)

    def run(self,matlab_statement):
        self.engine.engEvalString(self.ep,c_char_p(matlab_statement))

    def getvalue(self,variable):
        self.engine.engGetVariable.restype=POINTER(mxArray)
        mx = self.engine.engGetVariable(self.ep,c_char_p(variable))
        self.mx.mxGetNumberOfDimensions.restype=c_int
        ndims = self.mx.mxGetNumberOfDimensions(mx)
        self.mx.mxGetDimensions.restype=POINTER(c_long)
        dims = self.mx.mxGetDimensions(mx)
        numelems = 1
        for i in range(ndims):
            numelems = numelems*dims[i]
        self.mx.mxGetClassName.restype=c_char_p
        self.mx.mxGetData.restype=POINTER(c_double)
        data =self.mx.mxGetData(mx)
        pyarray = array(data[0:numelems],order='F')
        pyarray.shape = dims[0:ndims]

        return pyarray
        



