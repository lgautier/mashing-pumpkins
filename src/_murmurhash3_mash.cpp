#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <MurmurHash3.h>
uint32_t MINHASH_DEFAULT_SEED = 42;

#include <stdio.h>

PyDoc_STRVAR(hasharray_withrc_doc,
             "hasharray_withrc(input, input_rc, width, buffer [, seed]) -> int\n\n"
             "Compute a hash values for a sliding array of bytes over a bytes-like object 'input', "
	     "optionally using a seed (an integer).");

static PyObject *
hasharray_withrc(PyObject * self, PyObject * args)
{
  Py_ssize_t width ;
  Py_buffer inputbuf;
  Py_buffer inputbuf_rc;
  Py_buffer arraybuf;
  uint32_t seed = MINHASH_DEFAULT_SEED;

  if (!PyArg_ParseTuple(args, "s*s*ny*|I", &inputbuf, &inputbuf_rc, &width, &arraybuf, &seed)) {
    return NULL;
  }

  const char * input = (char *)inputbuf.buf;
  const Py_ssize_t length = inputbuf.len;

  const char * input_rc = (char *)inputbuf_rc.buf;
  const Py_ssize_t length_rc = inputbuf_rc.len;

  if (width > length) {
    PyBuffer_Release(&inputbuf);
    PyBuffer_Release(&inputbuf_rc);
    PyBuffer_Release(&arraybuf);
    PyErr_SetString(PyExc_ValueError, "The width of the window cannot be longer than the input string.");
    return NULL;
  }
  if (length != length_rc) {
    PyBuffer_Release(&inputbuf);
    PyBuffer_Release(&inputbuf_rc);
    PyBuffer_Release(&arraybuf);
    PyErr_SetString(PyExc_ValueError, "The length of the input and its reverse-complement must be identical.");
    return NULL;
  }
    
  const Py_ssize_t olength = arraybuf.len / arraybuf.itemsize;

  if (arraybuf.itemsize != sizeof(unsigned long long)) {
    PyBuffer_Release(&inputbuf);
    PyBuffer_Release(&inputbuf_rc);
    PyBuffer_Release(&arraybuf);
    PyErr_SetString(PyExc_ValueError, "The buffer must be of format type Q.");
    return NULL;
  }

  unsigned long long * hasharray = (unsigned long long *) arraybuf.buf;
  const Py_ssize_t maxi = olength < (length-width+1) ? olength : (length-width+1); 
  
  uint64_t outh[2] = {0, 0};
  Py_ssize_t j;
  for (Py_ssize_t i=0; i < maxi; i++) {
    j = length_rc - width -i;
    if (strcmp(input+i, input_rc+j) < 0) {
      MurmurHash3_x64_128((void *)(input + i),
			  (uint32_t)width,
			  seed,
			  &outh);
    } else {
      MurmurHash3_x64_128((void *)(input_rc + j),
			  (uint32_t)width,
			  seed,
			  &outh);
    }
    hasharray[i] = (unsigned long long)outh[0];
  }
  PyBuffer_Release(&inputbuf);
  PyBuffer_Release(&inputbuf_rc);
  PyBuffer_Release(&arraybuf);
  return PyLong_FromSsize_t(maxi);
}


static PyMethodDef murmurhash3_mashModuleMethods[] = {
    {
      "hasharray_withrc", (PyCFunction)hasharray_withrc,
        METH_VARARGS, hasharray_withrc_doc,
    },
    { NULL} // sentinel
};

static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "_murmurhash3_mash",
  "Utilities to compute MurmurHash3 the MASH way.",
  -1,
  murmurhash3_mashModuleMethods};

PyMODINIT_FUNC
PyInit__murmurhash3_mash(void)
{
    PyObject *m;

    m = PyModule_Create(&moduledef);
    
    if (m == NULL) {
        return NULL;
    }

    PyModule_AddIntConstant(m, "DEFAULT_SEED", MINHASH_DEFAULT_SEED);
    
    return m;
}
