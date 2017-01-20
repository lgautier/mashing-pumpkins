#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <MurmurHash3.h>
uint32_t MINHASH_DEFAULT_SEED = 42;

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
  uint32_t seed = MINHASH_DEFAULT_SEED;

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
  
  uint64_t outh[2] = {0, 0};
  for (Py_ssize_t i=0; i < maxi; i++) {
    MurmurHash3_x64_128((void *)(input + i),
			(uint32_t)width,
			seed,
			&outh);
    hasharray[i] = (unsigned long long)outh[0];
  }
  PyBuffer_Release(&inputbuf);
  PyBuffer_Release(&arraybuf);
  return PyLong_FromSsize_t(maxi);
}


static PyMethodDef murmurhash3ModuleMethods[] = {
    {
      "hasharray", (PyCFunction)hasharray,
        METH_VARARGS, hasharray_doc,
    },
    { NULL} // sentinel
};

static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "_murmurhash3",
  "Utilities to compute MurmurHash3.",
  -1,
  murmurhash3ModuleMethods};

PyMODINIT_FUNC
PyInit__murmurhash3(void)
{
    PyObject *m;

    m = PyModule_Create(&moduledef);
    
    if (m == NULL) {
        return NULL;
    }

    PyModule_AddIntConstant(m, "DEFAULT_SEED", MINHASH_DEFAULT_SEED);
    
    return m;
}
