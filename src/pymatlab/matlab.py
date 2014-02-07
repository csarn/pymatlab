# -*- coding: iso-8859-15 -*-
'''
Copyright 2010-2013 Joakim Möller

This file is part of pymatlab.

pymatlab is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pymatlab is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pymatlab.  If not, see <http://www.gnu.org/licenses/>.
'''

from ctypes import *
import string
import random
import tempfile
from numpy import array, ndarray, dtype, savetxt
from os.path import join
import platform
import sys, numpy

from pymatlab.typeconv import *


class mxArray(Structure):
    pass


class Engine(Structure):
    pass


wrap_script = '''
pymatlaberrstring ='';
try
    {0}
catch err
    pymatlaberrstring = sprintf('Error: %s with message: %s',err.identifier,err.message);
    for i = 1:length(err.stack)
        pymatlaberrstring = sprintf('%sError: in fuction %s in file %%s line %i',pymatlaberrstring,err.stack(i,1).name,err.stack(i,1).file,err.stack(i,1).line);
    end
end
if exist('pymatlaberrstring','var')==0
    pymatlaberrstring='';
end
'''


class MatlabSession(object):
    def __init__(self, matlab_root='', command='', bufsize=8192):
        system = platform.system()
        if system == 'Linux':
            self.engine = CDLL(join(matlab_root, 'bin', 'glnxa64', 'libeng.so'))
            self.mx = CDLL(join(matlab_root, 'bin', 'glnxa64', 'libmx.so'))
        elif system == 'Windows':
            # determine wether we are using 32 or 64 bit build by testing sys.maxsize
            dll_dir = 'win64' if sys.maxsize > 2**32 else 'win32'            
            path = join(matlab_root,'bin',dll_dir)
            # add the Matlab DLL path to the environment PATH variable
            from os import environ
            environ['PATH'] = path + ';' + environ['PATH']
            
            # load the DLLs
            self.engine = CDLL('libeng')
            self.mx = CDLL('libmx')
            self.ep = self.engine.engOpen(None)
        elif system == 'Darwin':
            self.engine = CDLL(join(matlab_root, 'bin', 'maci64', 'libeng.dylib'))
            self.mx = CDLL(join(matlab_root, 'bin', 'maci64', 'libmx.dylib'))
        else:
            raise NotImplementedError(
                'system {} not yet supported'.format(system))

        # Set up types for engine
        self.engine.engOpen.restype = POINTER(Engine)
        self.engine.engPutVariable.argtypes = [POINTER(Engine), c_char_p, POINTER(mxArray)]
        self.engine.engPutVariable.restype = c_int
        self.engine.engGetVariable.argtypes = [POINTER(Engine), c_char_p]
        self.engine.engGetVariable.restype = POINTER(mxArray)
        self.engine.engEvalString.argtypes = [POINTER(Engine), c_char_p]
        self.engine.engEvalString.restype = c_int
        self.engine.engOutputBuffer.argtypes = [POINTER(Engine), c_char_p, c_int]
        self.engine.engOutputBuffer.restype = c_int

        self.mx.mxGetNumberOfDimensions_730.restype = c_size_t
        self.mx.mxGetNumberOfDimensions_730.argtypes = [POINTER(mxArray)]
        self.mx.mxGetDimensions_730.restype = POINTER(c_int)
        self.mx.mxGetDimensions_730.argtypes = [POINTER(mxArray)]
        self.mx.mxGetNumberOfElements.restype = c_size_t
        self.mx.mxGetNumberOfElements.argtypes = [POINTER(mxArray)]
        self.mx.mxGetElementSize.restype = c_size_t
        self.mx.mxGetElementSize.argtypes = [POINTER(mxArray)]
        self.mx.mxGetClassName.restype = c_char_p
        self.mx.mxGetClassName.argtypes = [POINTER(mxArray)]
        self.mx.mxIsNumeric.restype = c_bool
        self.mx.mxIsNumeric.argtypes = [POINTER(mxArray)]
        self.mx.mxIsComplex.restype = c_bool
        self.mx.mxIsComplex.argtypes = [POINTER(mxArray)]
        self.mx.mxGetData.restype = POINTER(c_void_p)
        self.mx.mxGetData.argtypes = [POINTER(mxArray)]
        self.mx.mxGetImagData.restype = POINTER(c_void_p)
        self.mx.mxGetImagData.argtypes = [POINTER(mxArray)]
        self.mx.mxArrayToString.argtypes = [POINTER(mxArray)]
        self.mx.mxArrayToString.restype = c_char_p
        self.mx.mxCreateString.restype = POINTER(mxArray)
        self.mx.mxCreateString.argtypes = [c_char_p]

        self.mx.mxCreateNumericArray_730.restype = POINTER(mxArray)
        self.mx.mxCreateLogicalArray_730.restype = POINTER(mxArray)
        self.mx.mxCreateCharArray_730.restype = POINTER(mxArray)
        self.mx.mxGetLogicals.restype = POINTER(c_void_p)
        self.mx.mxGetData.restype = POINTER(c_void_p)
        self.mx.mxGetImagData.restype = POINTER(c_void_p)

        # Start Matlab
        self.ep = self.engine.engOpen(None)

        if self.ep is None:
            raise RuntimeError(
                'Could not start matlab using command "{}"'.format(command))
        self.buff_length = bufsize
        if self.buff_length != 0:
            self.buf = create_string_buffer(self.buff_length)
            self.engine.engOutputBuffer(self.ep, self.buf, self.buff_length - 1)

    def __del__(self):
        self.engine.engClose(self.ep)

    def run(self, matlab_statement):
        #wrap statement to be able to catch errors
        real_statement = wrap_script.format(matlab_statement)
        self.engine.engEvalString(self.ep, real_statement)
        mxresult = self.engine.engGetVariable(
            self.ep, c_char_p('pymatlaberrstring'))
        error_string = self.mx.mxArrayToString(mxresult)
        if error_string != "":
            raise (RuntimeError('Error from Matlab: {0}'.format(
                error_string)))

    def getvalue(self, variable):
        mx = self.engine.engGetVariable(self.ep, c_char_p(variable))
        ndims = self.mx.mxGetNumberOfDimensions_730(mx)
        dims = self.mx.mxGetDimensions_730(mx)
        numelems = self.mx.mxGetNumberOfElements(mx)
        elem_size = self.mx.mxGetElementSize(mx)
        class_name = self.mx.mxGetClassName(mx)
        is_numeric = self.mx.mxIsNumeric(mx)
        if is_numeric:
            is_complex = self.mx.mxIsComplex(mx)
            returnsize = numelems * elem_size
            data = self.mx.mxGetData(mx)
            realbuf = create_string_buffer(returnsize)
            memmove(realbuf, data, returnsize)
            datatype = class_name
            if is_complex:
                data_imag = self.mx.mxGetImagData(mx)
                imagbuf = create_string_buffer(returnsize)
                memmove(imagbuf, data_imag, returnsize)
                #datatype = class_name.split()[1]
                pyarray_imag = ndarray(buffer=imagbuf, shape=dims[:ndims],
                                       dtype=dtype(datatype), order='F')
            pyarray_real = ndarray(buffer=realbuf, shape=dims[:ndims],
                                   dtype=dtype(datatype), order='F')
            if is_complex:
                pyarray = pyarray_real + pyarray_imag * 1j
            else:
                pyarray = pyarray_real
            return pyarray.squeeze()
        else:
            if class_name == 'cell':
                raise NotImplementedError('{}-arrays are not implemented'.format(
                    class_name))
            elif class_name == 'char':
                length = numelems + 2
                return_str = create_string_buffer(length)
                self.mx.mxGetString_730(mx, return_str, length - 1);
                return return_str.value
            elif class_name == 'function_handle':
                raise NotImplementedError('{}-arrays are not implemented'.format(
                    class_name))
            elif class_name == 'logical':
                returnsize = numelems * elem_size
                data = self.mx.mxGetData(mx)
                buf = create_string_buffer(returnsize)
                memmove(buf, data, returnsize)
                pyarray = ndarray(buffer=buf, shape=dims[:ndims],
                                  dtype=dtype('bool'), order='F')
                return pyarray.squeeze()
            elif class_name == 'struct':
                raise NotImplementedError('{}-arrays are not implemented'.format(
                    class_name))
            elif class_name == 'unknown':
                raise NotImplementedError('{}-arrays are not implemented'.format(
                    class_name))
            else:
                raise NotImplementedError('{}-arrays are not implemented'.format(
                    class_name))

    def putvalue(self, name, pyvariable):
        if type(pyvariable) == str:
            mx = self.mx.mxCreateString(c_char_p(pyvariable))
        elif type(pyvariable) == dict:
            raise NotImplementedError('dictionaries are not supported')
        else:
            if not type(pyvariable) == ndarray:
                pyvariable = array(pyvariable)
            if pyvariable.dtype.kind in ['i', 'u', 'f', 'c']:
                dim = pyvariable.ctypes.shape_as(c_size_t)

                complex_flag = 0
                if pyvariable.dtype.kind == 'c':
                    complex_flag = 1
                mx = self.mx.mxCreateNumericArray_730(c_size_t(pyvariable.ndim),
                                                      dim,
                                                      np_to_mat(pyvariable),
                                                      c_int(complex_flag))
                data_old = self.mx.mxGetData(mx)
                datastring = pyvariable.real.tostring('F')
                n_datastring = len(datastring)
                memmove(data_old, datastring, n_datastring)
                if complex_flag:
                    data_old_imag = self.mx.mxGetImagData(mx)
                    datastring = pyvariable.imag.tostring('F')
                    n_datastring = len(datastring)
                    memmove(data_old_imag, datastring, n_datastring)

            elif pyvariable.dtype.kind == 'b':
                dim = pyvariable.ctypes.shape_as(c_size_t)

                mx = self.mx.mxCreateLogicalArray_730(c_size_t(pyvariable.ndim),
                                                      dim)

                data_old = self.mx.mxGetData(mx)
                datastring = pyvariable.tostring('F')
                n_datastring = len(datastring)
                memmove(data_old, datastring, n_datastring)
            elif pyvariable.dtype.kind == 'S':
                raise NotImplementedError("String arrays are not supported.")
                dim = pyvariable.ctypes.shape_as(c_size_t)
                mx = self.mx.mxCreateCharArray_730(c_size_t(pyvariable.ndim),
                                                   dim)
                data_old = self.mx.mxGetData(mx)
                datastring = pyvariable.tostring('F')
                n_datastring = len(datastring)
                memmove(data_old, datastring, n_datastring)
            elif pyvariable.dtype.kind == 'O':
                # Implement object arrays
                raise NotImplementedError('Object arrays are not supported')
            else:
                raise NotImplementedError('Type not supported')
        self.engine.engPutVariable(self.ep, name, mx)

    def putdataset(self, name, pyvariable, column_names):
        # Assert that we were passed a not-null variable
        assert pyvariable is not None
        # Assert that it is a numpy array
        if not isinstance(pyvariable, ndarray):
            pyvariable = array(pyvariable)
        pyvariable_shape = pyvariable.shape
        column_count = pyvariable_shape[1]
        # Assert that we have enough column names
        assert len(column_names) == column_count
        # Assert that we have at least one row
        assert pyvariable_shape[0] > 0
        # Create a temporary file
        with tempfile.NamedTemporaryFile() as temp_file:
            # Dump to this file
            savetxt(temp_file.name, pyvariable, fmt=["%s"] * len(column_names), delimiter="\t",
                    header="\t".join(column_names), comments='')
            # Create a dataset from this file
            statement = \
                """
                %s = dataset('File','%s');
                """ % (name, temp_file.name)
            self.run(statement)


