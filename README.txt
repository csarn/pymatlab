=====================================
Python interface to MATLAB (pymatlab)
=====================================

This package lets python users interface and communicate with MATLAB from
python. Pymatlab makes it easier for users to migrate from a large MATLAB
codebase to python scripts - one step at a time - by using old MATLAB scripts.

The package uses Numpy's ndarrays and translates them into MATLAB's mxarrays
using Numpy's c-api and Matlab mx library. The interface to MATLAB's workspace
in done through MATLAB's engine library.

Download
--------

Downloading is possible from PyPi_ and `SourceForge pymatlab files`__. Since
pymatlab is hosted at SourceForge_ the latest development version is avalable
from subversion.

.. _PyPi: http://pypi.python.org  
.. _Files: http://sourceforge.net/projects/pymatlab/files/
.. _SourceForge: http://sourceforge.net

__ Files_

Installing
----------

When installing from source distribution the include_dir and library_dir in
setup.cfg needs to be altered. Sample configurations for different platforms
are avalable in the package.

Preparing to use pymatlab
-------------------------

On UNIX like systems let the system administrator add the MATLAB library
directories in ldconfig. If you don't have root access set the environmental
variable LD_LIBRARY_PATH to correct path where pymatlab can find MATLAB's
libraries (libmx and libeng). On my system with MATLAB installed in
/opt/matlab I have put this line in my .bashrc:

    export LD_LIBRARY_PATH=/opt/matlab/bin/glnxa64:$LD_LIBRARY_PATH

However, this is not necessary if you configure the rpath setting correctly 
in the setup.cfg at build time.

On Windows make sure the Matlab DLLs are in your "Path" environment variable. 

Requirements
------------
 
- Matlab 
    
    Versions 2009a and 2010a verified. Presumably any version?

- Numpy

    Any version? tested on version 1.3.0.

Limitations
-----------

The current version lets you transfer double precision matrixes of any rank.
Any other types will probably fail and give unpredictable results.


Using pymatlab
--------------

First import:

>>> from pymatlab import Session
    

Start a Session, an optional argument is the path the the matlab
executable, if it is not your PATH.

>>> m = Session("/optional/path/to/matlab -options")

Here matlab "-options" default to "-nosplash -nodesktop" which allows MATLAB
GUI windows to open and be interactive!

((
Trouble-shooting Note: If you get a "Can't start MATLAB engine"
here, and you are running a Linux based system, please be sure that
"csh" is install and in /bin/csh, i.e. on Ubuntu:

$ sudo apt-get install csh
# or have you sysadmin install csh
$ which csh
/bin/csh
))

Now try it out ... the Session instance exposes the matlab namespace, so
we can call the matlab "plot" function:

>>> import numpy
>>> a = numpy.arange(0,10,0.1)
>>> m.plot(a,a**2,'r--')
>>> m.close()
>>> print m.help('plot')  # will print MATLAB docs on plot

If you are in ipython
$ ipython -pylab

On can get help directly on objects in the MATLAB namespace
In []: m.plot ?
Type:             FuncWrap
Base Class:       <class 'pymatlab.FuncWrap'>
String Form:   <pymatlab.FuncWrap object at 0x2ed8190>
Namespace:        Interactive
File:             /usr/local/lib/python2.6/dist-packages/pymatlab-0.1.3-py2.6-linux-x86_64.egg/pymatlab/__init__.py
Docstring:
    PLOT   Linear plot.                                                                                                     
    PLOT(X,Y) plots vector Y versus vector X. If X or Y is a matrix,
    then the vector is plotted versus the rows or columns of the matrix,
    whichever line up.  If X is a scalar and Y is a vector, disconnected
    line objects are created and plotted as discrete points vertically at
    X.
 
...

Strings of matlab code can be sent to the Session with the run method:

>>> m.run("a = 0:10")
>>> print m.a
[[  0.   1.   2.   3.   4.   5.   6.   7.   8.   9.  10.]]
>>> m.b = numpy.array([range(11.0)[::-1]],dtype=float)
>>> m.run("c = a+b")
>>> print m.c
[[ 10.  10.  10.  10.  10.  10.  10.  10.  10.  10.  10.]]

Sucessfull m.run commands return an empty string - if MATLAB 
generates an error then a RuntimeError is raised with the 
MATLAB error message 
    
>>> m.run('B=2*A')

    ...
RuntimeError: Error from Matlab: Error: MATLAB:UndefinedFunction with message: Undefined function or variable 'A'.
 end.

A trick to make larger scripts more failsafe with regards to syntax errors.
Send a script to a string variable and run it with eval().

>>> m.code = """D = a
... for i=1:10
...    D = 2*D
... end
... """
>>> m.run('eval(code)')

To retrive the variable back to python:

>>> print m.D
>>> (m.D==m.A*(2**10)).all()
True

The MATLAB session is closed automatically on garbage collection of
the m instance.

>>> quit()
Closing MATLAB session.


Bugs, support and feature requests
----------------------------------

All request for support like bugfixing and installation support or feature
requests are directed to  the `SourceForge tracker for pymatlab
<http://sourceforge.net/tracker/?group_id=307148>`_. 

Please  consider to support us in our efforts by `donating to pymatlab`__. Your donations will be used to buy hardware and software licenses to be able to continue to develop this package. 

.. _Donations: http://sourceforge.net/donate/index.php?group_id=307148

__ Donations_
