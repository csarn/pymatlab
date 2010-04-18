/* * *
 * Copyright 2010 Joakim Möller
 *
 * This file is part of pymatlab.
 * 
 * pymatlab is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * pymatlab is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with pymatlab.  If not, see <http://www.gnu.org/licenses/>.
 * * */

#include <Python.h>
#include <structmember.h>
#include <numpy/arrayobject.h>
#include <stdio.h>
#include <engine.h>

/* This wraps a command call to the MATLAB interpretor */
const char * function_wrap = "try\n\t%s;\ncatch err\n\tpymatlaberrstring = sprintf('Error: %%s with message: %%s\\n',err.identifier,err.message);\n\tfor i = 1:length(err.stack)\n\t\tpymatlaberrstring = sprintf('%%sError: in fuction %%s in file %%s line %%i\\n',pymatlaberrstring,err.stack(i,1).name,err.stack(i,1).file,err.stack(i,1).line);\n\tend\nend\nif exist('pymatlaberrstring','var')==0\n\tpymatlaberrstring='';\nend";

int mxtonpy[17]={   NPY_USERDEF,
                    NPY_USERDEF,
                    NPY_USERDEF,
                    NPY_BOOL,
                    NPY_CHAR,
                    NPY_USERDEF,
                    NPY_DOUBLE,
                    NPY_FLOAT,
                    NPY_SHORT, NPY_USHORT,
                    NPY_INT, NPY_UINT,
                    NPY_LONG, NPY_ULONG,
                    NPY_LONGLONG, NPY_ULONGLONG,
                    NPY_USERDEF
};
mxClassID npytomx[23]={ mxLOGICAL_CLASS,
                        mxUNKNOWN_CLASS,
                        mxUNKNOWN_CLASS,
                        mxINT8_CLASS, mxUINT8_CLASS,
                        mxINT16_CLASS, mxUINT16_CLASS,
                        mxINT32_CLASS, mxUINT32_CLASS,
                        mxINT64_CLASS, mxUINT64_CLASS,
                        mxSINGLE_CLASS, mxDOUBLE_CLASS, mxUNKNOWN_CLASS,
                        mxUNKNOWN_CLASS, mxUNKNOWN_CLASS, mxUNKNOWN_CLASS,
                        mxUNKNOWN_CLASS,
                        mxCHAR_CLASS, mxCHAR_CLASS,
                        mxUNKNOWN_CLASS,
                        mxUNKNOWN_CLASS,
                        mxCHAR_CLASS,
};
typedef struct 
{
    PyObject_HEAD
    Engine *ep;
} PyMatlabSessionObject;

static PyObject * PyMatlabSessionObject_new(PyTypeObject *type, PyObject *args, PyObject * kwds)
{
    PyMatlabSessionObject *self;
    self = (PyMatlabSessionObject *) type->tp_alloc(type,0);
    if (self!=NULL)
    {
        self->ep = NULL;
    }
    return (PyObject *) self;
}

static int PyMatlabSessionObject_init(PyMatlabSessionObject *self, PyObject *args, PyObject *kwds)
{
    int status;
    char *startstr=NULL;
    if (!PyArg_ParseTuple(args,"|s",&startstr))
        return EXIT_FAILURE;
    if (!(self->ep = engOpen(startstr))) {
        fprintf(stderr, "\nCan't start MATLAB engine\n");
        return EXIT_FAILURE;
    }
    status = engOutputBuffer(self->ep,NULL,0);
    return 0;
}

static void
PyMatlabSessionObject_dealloc(PyMatlabSessionObject *self)
{
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject * PyMatlabSessionObject_run(PyMatlabSessionObject *self, PyObject *args)
{
    char * stringarg;
    char * command,*errmsg;
    int status;
    const mxArray * mxresult;
    PyObject * result;
    if (!PyArg_ParseTuple(args,"s",&stringarg))
        return NULL;
    if (!(command = (char*)malloc(sizeof(char)*3000)))
        return NULL;
    sprintf(command,function_wrap,stringarg);
    if (engEvalString(self->ep,command)!=0)
        return PyErr_Format(PyExc_RuntimeError,
                "Was not able to evaluate command: %s",command);
    if ((mxresult = engGetVariable(self->ep,"pymatlaberrstring"))==NULL)
        return PyErr_Format(PyExc_RuntimeError,"%s",
                "can't get internal variable: pymatlaberrstring");
    if (strcmp( mxArrayToString(mxresult),"")!=0)
    {
        /*make sure 'pymatlaberrstring' is empty or not exist until next call*/
        status = engEvalString(self->ep,"clear pymatlaberrstring");
        return PyErr_Format(PyExc_RuntimeError,"Error from Matlab: %s end.",
                mxArrayToString(mxresult));
    }
    /*free((void*)command);*/
    Py_RETURN_NONE;
}

static PyObject * PyMatlabSessionObject_putvalue(PyMatlabSessionObject *self, PyObject *args)
{
    const char * name;
    PyArrayObject * ndarray,*cont_ndarray;
    mxArray * mxarray;
    double *mx,*nd;
    int i,j;

    if (!PyArg_ParseTuple(args,"sO",&name,&ndarray))
        return NULL;
    cont_ndarray = PyArray_FROM_OF(ndarray,NPY_F_CONTIGUOUS | NPY_ALIGNED | NPY_WRITEABLE);
    /*
    allocating and zero initialise */
    if (!(mxarray=mxCreateNumericArray((mwSize)cont_ndarray->nd,
                    (mwSize*)PyArray_DIMS(cont_ndarray),
                    npytomx[PyArray_TYPE(cont_ndarray)],
                    mxREAL)))
        return PyErr_Format(PyExc_RuntimeError, 
            "Couldn't create mxarray: NPYTYPE:%i - mxtype:%i", 
            PyArray_TYPE(cont_ndarray), npytomx[PyArray_TYPE(cont_ndarray)]);

    nd=(double*)PyArray_DATA(cont_ndarray);
    mx=mxGetPr(mxarray);
    j=PyArray_SIZE(cont_ndarray);
    for (i=0;i<j;i++)
        mx[i]=nd[i];
    if ((engPutVariable(self->ep,name,mxarray)!=0))
    {
        PyErr_SetString(PyExc_RuntimeError,"Couldn't place string on workspace");
        return NULL;
    }
    /*
    if (ndarray!=cont_ndarray)
        Py_DECREF(cont_ndarray);
    Py_DECREF(ndarray);
        */
    Py_RETURN_NONE;
}

static PyObject * PyMatlabSessionObject_putstring(PyMatlabSessionObject *self, PyObject *args)
{
    const char * name, * command_string;
    const mxArray * variable;
    if (!PyArg_ParseTuple(args,"ss",&name,&command_string))
        return NULL;
    if (!(variable=mxCreateString(command_string)))
    {
        PyErr_SetString(PyExc_RuntimeError,"Couldn't create mxarray");
        return NULL;
    }
    if ((engPutVariable(self->ep,name,variable)!=0))
    {
        PyErr_SetString(PyExc_RuntimeError,"Couldn't place string on workspace");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject * PyMatlabSessionObject_getvalue(PyMatlabSessionObject * self, PyObject *args)
{
    const char * variable;
    mxArray * mx;
    PyObject *result;

    if (!PyArg_ParseTuple(args,"s",&variable))
        return NULL;
    if (!(mx = engGetVariable(self->ep,variable)))
        return PyErr_Format(PyExc_AttributeError,"Couldn't find '%s' at MATLAB desktop",variable);
/*    This is how we could make it own data to avoid memory leak: (set OWN_DATA)
 *    data = malloc(sizeof(double[n*m])); 
    memcpy((void * )data,(void *)mxGetPr(mx),sizeof(double[n*m]));*/
    if (!(result=PyArray_New(&PyArray_Type,(int) mxGetNumberOfDimensions(mx), 
                    (npy_intp*) mxGetDimensions(mx), mxtonpy[mxGetClassID(mx)],
                    NULL, mxGetData(mx), NULL, NPY_F_CONTIGUOUS, NULL)))
        return PyErr_Format(PyExc_AttributeError,"Couldn't convert to PyArray");
    /*
    mxDestroyArray(mx);
    free((void*)data);
    */
    return result;
}

static PyObject * PyMatlabSessionObject_close(PyMatlabSessionObject * self, PyObject *args)
{
    engClose(self->ep);
    Py_RETURN_NONE;
}

static PyMethodDef PyMatlabSessionObject_methods[] =
{
    {"run", (PyCFunction)PyMatlabSessionObject_run, METH_VARARGS, "Launch a command in MATLAB."},
    {"close", (PyCFunction)PyMatlabSessionObject_close, METH_VARARGS, "Close the open MATLAB session"},
    {"putstring", (PyCFunction)PyMatlabSessionObject_putstring, METH_VARARGS, "Put a string on the workspace"},
    {"getvalue", (PyCFunction)PyMatlabSessionObject_getvalue, METH_VARARGS, "Get a variable from the workspace and return a ndarray"},
    {"putvalue", (PyCFunction)PyMatlabSessionObject_putvalue, METH_VARARGS, "Get a variable from the workspace and return a ndarray"},
    {NULL,NULL,0,NULL}
};

static PyMemberDef PyMatlabSessionObject_members[] = 
{
    { NULL }
};


static PyTypeObject PyMatlabSessionObjectType =
    {
        PyObject_HEAD_INIT(NULL)
        0,                         /* ob_size */
        "PyMatlabSessionObject",               /* tp_name */
        sizeof(PyMatlabSessionObject),         /* tp_basicsize */
        0,                         /* tp_itemsize */
        (destructor)PyMatlabSessionObject_dealloc, /* tp_dealloc */
        0,                         /* tp_print */
        0,                         /* tp_getattr */
        0,                         /* tp_setattr */
        0,                         /* tp_compare */
        0,                         /* tp_repr */
        0,                         /* tp_as_number */
        0,                         /* tp_as_sequence */
        0,                         /* tp_as_mapping */
        0,                         /* tp_hash */
        0,                         /* tp_call */
        0,                         /* tp_str */
        0,                         /* tp_getattro */
        0,                         /* tp_setattro */
        0,                         /* tp_as_buffer */
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags*/
        "PyMatlabSessionObject object connects to a torque server.",        /* tp_doc */
        0,                         /* tp_traverse */
        0,                         /* tp_clear */
        0,                         /* tp_richcompare */
        0,                         /* tp_weaklistoffset */
        0,                         /* tp_iter */
        0,                         /* tp_iternext */
        PyMatlabSessionObject_methods,         /* tp_methods */
        PyMatlabSessionObject_members,         /* tp_members */
        0,                         /* tp_getset */
        0,                         /* tp_base */
        0,                         /* tp_dict */
        0,                         /* tp_descr_get */
        0,                         /* tp_descr_set */
        0,                         /* tp_dictoffset */
        (initproc)PyMatlabSessionObject_init,  /* tp_init */
        0,                         /* tp_alloc */
        PyMatlabSessionObject_new,      /* tp_new */
    };

static PyMethodDef matlab_methods[] = 
{
    { NULL }
};

PyMODINIT_FUNC initmatlab (void)
{
    PyObject * mod;
    import_array();
    mod =  Py_InitModule3("matlab",matlab_methods,"Juno's and Hermod's interface to MATLAB");

    if (mod==NULL) {
        return;

    }

    if (PyType_Ready(&PyMatlabSessionObjectType)<0) {
        return;
    }
    Py_INCREF(&PyMatlabSessionObjectType);
    PyModule_AddObject(mod,"MatlabSession", (PyObject*) &PyMatlabSessionObjectType);
}


