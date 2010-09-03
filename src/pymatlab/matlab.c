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


#define CHECK_ENGINE if (self->ep==NULL) return PyErr_Format(PyExc_RuntimeError,"No open MATLAB Session.");


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

    // ep is set to NULL when closing.
    if (self->ep!=NULL) {
      PyErr_SetString(PyExc_RuntimeError,"Close the existing MATLAB Session before opening another!");
      return EXIT_FAILURE;
    }

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
  if (self->ep!=NULL) {
    //printf("Closing MATLAB session.\n");
    engClose(self->ep);
    self->ep=NULL;
  }

  self->ob_type->tp_free((PyObject*)self);
}

static PyObject * PyMatlabSessionObject_run(PyMatlabSessionObject *self, PyObject *args)
{
    char * stringarg;
    char * command,*errmsg;
    int status;
    const mxArray * mxresult;
    PyObject * result;

    CHECK_ENGINE

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

mxArray * numpy_to_mxarray(PyArrayObject *ndarray) {

    double *mx,*nd;
    int i,j;
    mxArray *mxarray;
    PyArrayObject *cont_ndarray;

    npy_intp* dims;

    cont_ndarray = PyArray_FROM_OF(ndarray,NPY_F_CONTIGUOUS | NPY_ALIGNED | NPY_WRITEABLE);
    /*
    allocating and zero initialise */
    if (!(mxarray=mxCreateNumericArray((mwSize)cont_ndarray->nd,
                    (mwSize*)PyArray_DIMS(cont_ndarray),
                    npytomx[PyArray_TYPE(cont_ndarray)],
                    mxREAL)))
      return NULL;

    nd=(double*)PyArray_DATA(cont_ndarray);
    mx=mxGetPr(mxarray);
    j=PyArray_SIZE(cont_ndarray);
    for (i=0;i<j;i++)
        mx[i]=nd[i];


    j = (int)mxGetNumberOfDimensions(mxarray);
    dims = (npy_intp*) mxGetDimensions(mxarray);

    /* debug
    printf("numpy_to_mxarray:\n");
    for (i=0;i<j;i++) {
      printf("i=%d, dim=%d\n",i,dims[i]);
      
      }*/


    return mxarray;

}

mxArray *pobj_to_mx(PyObject *pObj) {

    PyArrayObject *ndarray;
    mxArray *mxarray = NULL;


    // is it a numpy array?
    if (PyArray_Check(pObj)) {
      ndarray = (PyArrayObject*)pObj;
      if (ndarray->nd>2) {
        return PyErr_Format(PyExc_TypeError, 
			    "Array dims>2 unsupported. You passed dim=%i",ndarray->nd); 
      }

      // TODO:
      // this test might need to be more fine grained to be sure of the correctness of  
      // the cast "nd=(double*)PyArray_DATA(cont_ndarray)" in numpy_to_mxarray(pObj) 
      if (!PyArray_ISFLOAT(pObj)) {
	PyErr_SetString(PyExc_TypeError,"array elements should be of numpy.double or numpy.float type");
        return NULL;

      }
      
      if (!(mxarray = numpy_to_mxarray(ndarray))) {
        return PyErr_Format(PyExc_RuntimeError, 
            "Couldn't create mxarray: NPYTYPE:%i - mxtype:%i", 
            PyArray_TYPE(ndarray), npytomx[PyArray_TYPE(ndarray)]);

      }

    }
    // is it a string?
    else if (PyString_Check(pObj)) {
      const char * command_string = PyString_AsString(pObj);

      if (!(mxarray=mxCreateString(command_string))) {
	PyErr_SetString(PyExc_RuntimeError,"Couldn't create mxarray");
        return NULL;
      }

      
    }
    else if (PyList_Check(pObj)) {
      // could be representation of matlab struct
      // let's collect all necessary info to proceed as if ...
      
      int len_l = (int)PyList_Size(pObj);
      int len_d;
      int i,j;
      PyObject *d;

      PyObject *key, *value;
      Py_ssize_t pos = 0;
      mxArray *mx_val;

      // avoid dynamic alloc, by max number of field names
      char* field_names[1024];


      if (len_l==0) {
	PyErr_SetString(PyExc_TypeError,"Minimum struct size is 1x1.");
        return NULL;
      }
      
      d = PyList_GetItem(pObj,0);
      if (PyDict_Check(d)) {
	// infer this is a struct schema: [{}]
	// get length of first dict in list (this tells us number of struct fields)
	len_d = (int)PyDict_Size(d);
      
	if (len_d>1024) {
	  PyErr_SetString(PyExc_TypeError,"Minimum supported number of fields is 1024.");
	  return NULL;
	}

	// build field_name list
      
	pos = 0;
	// pos is not consecutive, so need indexer, j
	j = 0;
	while (PyDict_Next(d, &pos, &key, &value)) {
	  if (!PyString_Check(key)) {
	    PyErr_SetString(PyExc_TypeError,"field names (keys) must be strings.");
	    return NULL;
	  }
	  // ret val is an internal pointer, so no need to delete later
	  field_names[j] = PyString_AsString(key);
	  j+=1;
	}

	// create the resulting matlab struct array
	mxarray = mxCreateStructMatrix(1,len_l,len_d,field_names);
	if (mxarray==NULL) {
	  PyErr_SetString(PyExc_RuntimeError,"error allocating mxarray.");
	  return NULL;
	}

      
	// build the fields
	for (i=0;i<len_l;i++) {

	  d = PyList_GetItem(pObj,i);
	  // check length of dict
	  if (PyDict_Size(d)!=len_d) {
	    PyErr_SetString(PyExc_TypeError,"invalid dict length for (@i>=0).");
	    mxDestroyArray(mxarray);
	    return NULL;
	  }

	  for (j=0;j<len_d;j++) {

	    value = PyDict_GetItemString(d,field_names[j]);
	    if (value==NULL) {
	      mxDestroyArray(mxarray);
	      return PyErr_Format(PyExc_TypeError, 
				  "dict at index %i in list missing field_name %s", 
				  j,field_names[j]);
	    }

	    // recurse to value in dict
	    mx_val = pobj_to_mx(value);
	    if (mx_val==NULL) {
	      mxDestroyArray(mxarray);
	      return NULL;
	    }
	    mxSetFieldByNumber(mxarray, i, j, mx_val);
	  }
	}
      } // if (PyDict_Check(d))
      else {

	// infer cell array schema
	mxarray = mxCreateCellMatrix(1,len_l);
	if (mxarray==NULL) {
	  PyErr_SetString(PyExc_RuntimeError,"error allocating mxarray.");
	  return NULL;
	}
	for (i=0;i<len_l;i++) {

	  d = PyList_GetItem(pObj,i);
	  if (d==NULL) {
	    mxDestroyArray(mxarray);
	    PyErr_SetString(PyExc_RuntimeError,"populating cell array: error indexing pObj.");
	    return NULL;
	  }
	  mx_val = pobj_to_mx(d);
	  if (mx_val==NULL) {
	    mxDestroyArray(mxarray);
	    return NULL;
	  }

	  mxSetCell(mxarray,i,mx_val);

	}

      }


    }
    else if (PyTuple_Check(pObj)) {
      // a sparse matrix schema?
      if (PyTuple_Size(pObj)==4) {
	// assume sparse matrix repr

	PyArrayObject * pr = PyTuple_GetItem(pObj,0);
	PyArrayObject * ir = PyTuple_GetItem(pObj,1);
	PyArrayObject * jc = PyTuple_GetItem(pObj,2);
	PyArrayObject * shape = PyTuple_GetItem(pObj,3);
	int m,n,nzmax,n_jc,i;
	// TODO: check that input data is indeed real only.
	int complex = 0;

	int* data;
	mwIndex *mx_jc,*mx_ir;
	double *pr_data,*mx_pr;

	if (!PyArg_ParseTuple(pObj,"O!O!O!O!", 
			      &PyArray_Type, &pr,
			      &PyArray_Type, &ir,
			      &PyArray_Type, &jc,
			      &PyArray_Type, &shape)) {

	  
	  return PyErr_Format(PyExc_TypeError, 
			      "Expected tuple with 4 ndarrays as elements: (data/pr,indices/ir,indptr/jc,shape/size) for sparse matrix representation.");

	}
			 
	if (pr->nd!=1) {
	  return PyErr_Format(PyExc_TypeError,"Expected 1-D ndarray for pr.");
	}

	if (PyArray_TYPE(pr)!=NPY_DOUBLE) {
	  return PyErr_Format(PyExc_TypeError,"Expected ndarray of NPY_DOUBLE type for pr.");
	}

	if (ir->nd!=1) {
	  return PyErr_Format(PyExc_TypeError,"Expected 1-D ndarray for ir.");
	}

	if (PyArray_TYPE(ir)!=NPY_INT) {
	  return PyErr_Format(PyExc_TypeError,"Expected ndarray of NPY_INT type for ir.");
	}

	if (jc->nd!=1) {
	  return PyErr_Format(PyExc_TypeError,"Expected 1-D ndarray for jc.");
	}

	if (PyArray_TYPE(jc)!=NPY_INT) {
	  return PyErr_Format(PyExc_TypeError,"Expected ndarray of NPY_INT type for jc.");
	}

	if (shape->nd!=1) {
	  return PyErr_Format(PyExc_TypeError,"Expected 1-D ndarray for shape.");
	}

	if (PyArray_TYPE(shape)!=NPY_INT) {
	  return PyErr_Format(PyExc_TypeError,"Expected ndarray of NPY_INT type for shape.");
	}


	if (PyArray_DIM(shape,0)!=2) {
	  return PyErr_Format(PyExc_TypeError,"Expected 1-D ndarray for shape with 2 elements, got %d.", (int)PyArray_DIM(shape,0));
	}

	nzmax = PyArray_DIM(pr,0);
	data = (int*)PyArray_DATA(shape);
	m = data[0];
	n = data[1];
	n_jc = n+1;

	i = PyArray_DIM(jc,0);
	if (i!=n_jc) {
	  return PyErr_Format(PyExc_TypeError,"Expected %d elements for jc array, got %d.",n_jc,i);
	}

	i = PyArray_DIM(ir,0);
	if (i!=nzmax) {
	  return PyErr_Format(PyExc_TypeError,"Expected %d elements for ir array, got %d.",nzmax,i);
	}

	mxarray = mxCreateSparse(m,n,nzmax,0);

	// copy pr array to matlab
	mx_pr = (double*)mxGetPr(mxarray);
	pr_data = (double*)PyArray_DATA(pr);
	for (i=0;i<nzmax;i++) {
	  mx_pr[i] = pr_data[i];
	}

	// copy jc array
	mx_jc = mxGetJc(mxarray);
	data = (int*)PyArray_DATA(jc);
	for (i=0;i<n_jc;i++) {
	  mx_jc[i] = data[i];
	}

	// copy ir

	mx_ir = mxGetIr(mxarray);
	data = (int*)PyArray_DATA(ir);
	for (i=0;i<nzmax;i++) {
	  mx_ir[i] = data[i];

	}

      }
      else {
	return PyErr_Format(PyExc_RuntimeError, 
		     "Got tuple, expected 4 elements: (data/pr,indices/ir,indptr/jc,shape/size) for sparse matrix representation.");
	  
      }
    }
    else if (PyBool_Check(pObj)) {

      if (pObj==Py_True) {
	mxarray = mxCreateLogicalScalar(1);
      }
      else {
	mxarray = mxCreateLogicalScalar(0);
      }
      if (mxarray==NULL) {
        PyErr_SetString(PyExc_RuntimeError, 
			"unknown error creating logical mxArray from Python bool."); 
        return NULL;
      }
    }
    else if (PyInt_Check(pObj)) {
      // put a "scalar"
      // put a "scalar"
      mxarray = mxCreateDoubleScalar((double)PyInt_AsLong(pObj));
      if (mxarray==NULL) {
        PyErr_SetString(PyExc_RuntimeError, 
			"unknown error creating scalar mxArray from Python int."); 
        return NULL;
      }

    }
    else if (PyFloat_Check(pObj)) {
      // put a "scalar"
      mxarray = mxCreateDoubleScalar(PyFloat_AsDouble(pObj));
      if (mxarray==NULL) {
        PyErr_SetString(PyExc_RuntimeError, 
			"unknown error creating scalar mxArray from Python float."); 
        return NULL;
      }

    }
    else {
        PyErr_SetString(PyExc_TypeError, 
			"invalid 2nd argument to putvalue. Supported: numpy array, string"); 
        return NULL;
    }

    return mxarray;


}

static PyObject * PyMatlabSessionObject_putvalue(PyMatlabSessionObject *self, PyObject *args)
{
    const char * name;
    PyObject *pObj;
    mxArray * mxarray;

    CHECK_ENGINE

    if (!PyArg_ParseTuple(args,"sO",&name,&pObj)) {
        PyErr_SetString(PyExc_TypeError, 
			"invalid 1st argument to putvalue: expected 'name' as string"); 
        return NULL;
    }

    mxarray = pobj_to_mx(pObj);
    if (!mxarray) return NULL;

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


PyObject *mx_get_shape(mxArray *mx) {

  int i;
  npy_intp nd = mxGetNumberOfDimensions(mx);
  mwIndex *mx_dims = mxGetDimensions(mx);

  PyObject *pObj = PyArray_EMPTY(1,&nd,NPY_INT,0);
  int *data;
  
  if (pObj==NULL) {
     PyErr_SetString(PyExc_RuntimeError,"Error allocating shape numpy.ndarray.");
        return NULL;
  }

  data = (int*)PyArray_DATA(pObj);
  for (i=0;i<nd;i++) {
    data[i] = mx_dims[i];
  }

  return pObj;
}

PyObject *mx_to_pobj(mxArray *mx) {

  // this function may be called recursively in case of structure arrays


  PyObject *result;
  int nd,i;
  npy_intp* dims;

    // numerical data?
    if (mxIsNumeric(mx)) {
      if (mxIsComplex(mx)) {
        PyErr_SetString(PyExc_TypeError, 
			"Complex-valued MATLAB array detected and unsupported."); 
        return NULL;
      }


      if (mxIsSparse(mx)) {

	PyObject *pr,*ir,*jc,*shape;
	npy_intp nzmax = mxGetNzmax(mx);
	npy_intp n_jc;
	int* data;
	mwIndex *mx_jc,*mx_ir;

	double *pr_data,*mx_pr;
      
	shape = mx_get_shape(mx);

	mx_pr = (double*)mxGetPr(mx);
	pr = PyArray_EMPTY(1,&nzmax,NPY_DOUBLE,0);
	if (pr==NULL) {
	  return PyErr_Format(PyExc_RuntimeError, 
			      "PyArray_SimpleNew failed for sparse matrix pr.");
	  
	}
	pr_data = (double*)PyArray_DATA(pr);
	for (i=0;i<nzmax;i++) {
	  pr_data[i] = mx_pr[i];
	}

	
	//jc = mx_to_pobj(mxGetJc(mx));

	mx_jc = mxGetJc(mx);
	n_jc = mxGetDimensions(mx)[1]+1;
	jc = PyArray_EMPTY(1,&n_jc,NPY_INT,0);

	if (jc==NULL) {
	  return PyErr_Format(PyExc_RuntimeError, 
			      "PyArray_SimpleNew failed for sparse matrix jc with n_jc=%d",(int)n_jc);
	  
	}


	data = (int*)PyArray_DATA(jc);
	for (i=0;i<n_jc;i++) {
	  data[i] = mx_jc[i];

	}

	//ir = mx_to_pobj(mxGetIr(mx));

	mx_ir = mxGetIr(mx);
	ir = PyArray_EMPTY(1,&nzmax,NPY_INT,0);
	data = (int*)PyArray_DATA(ir);
	for (i=0;i<nzmax;i++) {
	  data[i] = mx_ir[i];

	}

     
	if(!shape || !pr || !ir || !jc) {
	  return NULL;
	}

	return Py_BuildValue("(OOOO)", pr,ir,jc,shape);
	
      }

      nd = (int)mxGetNumberOfDimensions(mx);
      dims = (npy_intp*) mxGetDimensions(mx);
      /*
      printf("mx_to_pobj:\n");
      for (i=0;i<nd;i++) {
	printf("i=%d, dim=%d\n",i,dims[i]);

	}*/

      if (!(result=PyArray_New(&PyArray_Type,nd , 
			       dims, mxtonpy[mxGetClassID(mx)],
			       NULL, mxGetData(mx), NULL, NPY_F_CONTIGUOUS, NULL)))
        return PyErr_Format(PyExc_AttributeError,"Couldn't convert to PyArray");


    }
    else if (mxIsChar(mx)) {

      char *buf;
      int len = mxGetNumberOfElements(mx)+1;
      buf = PyMem_Malloc(len);
      if (buf==NULL) {
        PyErr_SetString(PyExc_TypeError, 
			"Error allocating temporary storage for string copy."); 
        return NULL;


      }
      if (mxGetString(mx,buf,len)) {
        PyErr_SetString(PyExc_TypeError, 
			"Error copying MATLAB string.  This should not happen.  File a bug."); 
	PyMem_Free(buf);
        return NULL;
      }

      result = PyString_FromString(buf);
      PyMem_Free(buf);

    }
    else if (mxIsStruct(mx)) {
      // structure array
      // will convert to a list of dictionaries in python

      int nf = mxGetNumberOfFields(mx);
      int ne = mxGetNumberOfElements(mx);
      char *n;
      int i,j;
      mxArray *f;
      PyObject *d,*item;
      
      /*
      if (nf==0) {
        PyErr_SetString(PyExc_TypeError, 
			"Error getting number of Struct-array fields."); 
        return NULL;
	}*/

      result = PyList_New(ne);
      
      for (i=0;i<ne;i++) {
	d = PyDict_New();
	for (j=0;j<nf;j++) {
	  f = mxGetFieldByNumber(mx,i,j);
	  n = mxGetFieldNameByNumber(mx,j);

	  if (f == NULL) {
	    // PyDict_SetItem INCREFs for us
	    PyDict_SetItemString(d,n,Py_None);
	  }
	  else {
	    item = mx_to_pobj(f);
	    if (item==NULL) {
	      PyErr_SetString(PyExc_RuntimeError, 
			      "Error getting number of Struct-array item. That's bad.  TODO: likely memory leak."); 
	      Py_DECREF(result);
	      // TODO: should loop through result and dec ref all the elements.
	      return NULL;
	    }
	    PyDict_SetItemString(d,n,item);
	    //PyDict_SetItem INCREFs for us, so we should decref
	    // as mx_to_pobj returns a new object.
	    Py_DECREF(item);
	  }
        }

	// contrary to PyDict_SetItem, PyList_SetItem will "steal a reference".
	// see e.g.: http://edcjones.tripod.com/refcount.html
	PyList_SetItem(result,i,d);

      }


    }
    else if (mxIsCell(mx)) {
      // return cells as lists, hl-api will deal with shapes.

      int ne = mxGetNumberOfElements(mx);
      int i;
      mxArray *mx_val;
      PyObject *pObj;
      result = PyList_New(ne);
      
      for (i=0;i<ne;i++) {
	mx_val = mxGetCell(mx,i);
	if (mx_val==NULL) {
	  PyErr_SetString(PyExc_RuntimeError, 
			  "error indexing MATLAB cell array on conversion to Python object."); 
	  Py_DECREF(result);
	  return NULL;

	}
	pObj = mx_to_pobj(mx_val);
	if (pObj==NULL) {
	  // Error string already set.
	  Py_DECREF(result);
	  return NULL;
	}
	// pObj is new ref, but PyList_SetItem does not INCREF
	if (PyList_SetItem(result,i,pObj)!=0) {
	  PyErr_SetString(PyExc_RuntimeError, 
			  "creating cell array: error adding pObj to list"); 
	  Py_DECREF(result);
	  return NULL;
	}

      }

    }
    else if (mxIsLogical(mx)) {
      if (mxIsLogicalScalar(mx)) {
	// logical scalar
	if (mxIsLogicalScalarTrue(mx)) {
	  return Py_BuildValue("O",Py_True);
	}
	else {
	  return Py_BuildValue("O",Py_False);
	}
      }
      else {
	// logical array
	int ne = mxGetNumberOfElements(mx);
	char *n;
	int i,j;
	mxLogical *mx_data;
	PyObject *d,*item;
	bool* res_data;

	nd = (int)mxGetNumberOfDimensions(mx);
	dims = (npy_intp*) mxGetDimensions(mx);

	mx_data = mxGetLogicals(mx);
	result = PyArray_EMPTY(nd,dims,NPY_BOOL,1);
	if (result==NULL) {
	  return PyErr_Format(PyExc_RuntimeError, 
			      "PyArray_SimpleNew failed for conversion from MATLAB logical array.");
	  
	}
	res_data = (bool*)PyArray_DATA(result);
	for (i=0;i<ne;i++) {
	  res_data[i] = (bool)mx_data[i];
	}

      }
    }
    else {
      return PyErr_Format(PyExc_TypeError,"MATLAB name of class '%s' is unsupported.",mxGetClassName(mx));


    }



    return result;



}


static PyObject * PyMatlabSessionObject_getvalue(PyMatlabSessionObject * self, PyObject *args)
{
    const char * variable;
    mxArray * mx;
    PyObject *result;

    CHECK_ENGINE

    if (!PyArg_ParseTuple(args,"s",&variable)) {
        PyErr_SetString(PyExc_TypeError, 
			"invalid 1st argument to getvalue: expected 'name' as string"); 
        return NULL;
    }
    if (!(mx = engGetVariable(self->ep,variable)))
        return PyErr_Format(PyExc_AttributeError,"Couldn't find '%s' at MATLAB desktop",variable);
/*    This is how we could make it own data to avoid memory leak: (set OWN_DATA)
 *    data = malloc(sizeof(double[n*m])); 
    memcpy((void * )data,(void *)mxGetPr(mx),sizeof(double[n*m]));*/


    result = mx_to_pobj(mx);

    /*
    mxDestroyArray(mx);
    free((void*)data);
    */
    return result;
}

static PyObject * PyMatlabSessionObject_close(PyMatlabSessionObject * self, PyObject *args)
{
  if (self->ep!=NULL) {
    //printf("Closing MATLAB session.\n");
    engClose(self->ep);
    self->ep=NULL;
    Py_RETURN_NONE;
  }
}

static PyObject * PyMatlabSessionObject_closed(PyMatlabSessionObject * self, PyObject *args)
{
  if (self->ep!=NULL) {
    // not closed yet
    Py_INCREF(Py_False);
    return Py_False;
  }
  else {
    // self->ep==NULL => closed is True
    Py_INCREF(Py_True);
    return Py_True;
  }

}


static PyMethodDef PyMatlabSessionObject_methods[] =
{
    {"run", (PyCFunction)PyMatlabSessionObject_run, METH_VARARGS, "Launch a command in MATLAB."},
    {"close", (PyCFunction)PyMatlabSessionObject_close, METH_VARARGS, "Close the open MATLAB session"},
    {"closed", (PyCFunction)PyMatlabSessionObject_closed, METH_VARARGS, "Check if the MATLAB session has been closed."},
    {"getvalue", (PyCFunction)PyMatlabSessionObject_getvalue, METH_VARARGS, "Get a variable from the workspace and return a ndarray"},
    {"putvalue", (PyCFunction)PyMatlabSessionObject_putvalue, METH_VARARGS, "Put a variable from the workspace. Supported: strings, ndarray(dtype=double)"},
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


