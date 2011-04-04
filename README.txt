This is a python wrapper for the Java Native Interface.  It was
written as part of the CellProfiler project (http://cellprofiler.org)
by members of the Imaging Platform at the Broad Institute of MIT and
Harvard.

This code should be considered pre-Alpha quality.  It has been in use
in the CellProfiler project, but may take some time to stabilize as a
standalone library.

This package requires numpy.

Cython is used to generate the Python-to-JNI-to-Java interface, but
Cython does not have to be installed (the Cython-generated C code is
included in the distribution).
