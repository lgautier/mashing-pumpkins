#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <xxhash.h>
uint32_t XXH_DEFAULT_SEED = 0;

#include <stdio.h>

PyDoc_STRVAR(hasharray_doc,
             "hasharray(input, width, buffer [, seed]) -> int\n\n"
             "Compute a hash values for a sliding array of bytes over a bytes-like object 'input', "
	     "optionally using a seed (an integer).");

static PyObject *
hasharray(PyObject * self, PyObject * args)
{
  Py_ssize_t width ;
  Py_buffer inputbuf;
  Py_buffer arraybuf;
  const uint32_t seed = XXH_DEFAULT_SEED;

  if (!PyArg_ParseTuple(args, "s*ny*|I", &inputbuf, &width, &arraybuf, &seed)) {
    return NULL;
  }

  const char * input = (char *)inputbuf.buf;
  const Py_ssize_t length = inputbuf.len;
  
  if (width > length) {
    PyBuffer_Release(&inputbuf);
    PyBuffer_Release(&arraybuf);
    PyErr_SetString(PyExc_ValueError, "The width of the window cannot be longer than the input string.");
    return NULL;
  }
    
  const Py_ssize_t olength = arraybuf.len / arraybuf.itemsize;

  if (arraybuf.itemsize != sizeof(unsigned long long)) {
    PyBuffer_Release(&inputbuf);
    PyBuffer_Release(&arraybuf);
    PyErr_SetString(PyExc_ValueError, "The buffer must be of format type Q.");
    return NULL;
  }

  unsigned long long * hasharray = (unsigned long long *) arraybuf.buf;
  const Py_ssize_t maxi = olength < (length-width+1) ? olength : (length-width+1); 
  
  unsigned long long out;
  for (Py_ssize_t i=0; i < maxi; i++) {
    out = XXH64((void *)(input + i),
		(size_t)width,
		(unsigned long long)seed);
    hasharray[i] = out;
  }
  PyBuffer_Release(&inputbuf);
  PyBuffer_Release(&arraybuf);
  return PyLong_FromSsize_t(maxi);
}

static PyMethodDef xxhashModuleMethods[] = {
    {
      "hasharray", (PyCFunction)hasharray,
        METH_VARARGS, hasharray_doc,
    },
    { NULL} // sentinel
};

static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "_xxhash",
  "Utilities to compute XXHash.",
  -1,
  xxhashModuleMethods};

PyMODINIT_FUNC
PyInit__xxhash(void)
{
    PyObject *m;

    m = PyModule_Create(&moduledef);
    
    if (m == NULL) {
        return NULL;
    }

    PyModule_AddIntConstant(m, "DEFAULT_SEED", XXH_DEFAULT_SEED);
	
    return m;
}
