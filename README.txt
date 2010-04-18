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

>>> from pymatlab.matlab import MatlabSession
    
Initialise the interpretor, an optional argument is a string to launch matlab:

>>> session = MatlabSession()
>>> session.close()

Now with optional parameters:

>>> session = MatlabSession('matlab -nojvm -nodisplay')

Create an numpy-array to start the work.

>>> from numpy.random import randn
>>> a = randn(20,10,30)

Send the numpy array a to the MATLAB Workspace to the variable 'A'
  
>>> session.putvalue('A',a)

Do something in matlab in MATLAB with variable A. Sucessfull commands return
an empty string - if MATLAB generates an error the returning string holds the
error message
    
>>> session.run('B=2*A')

>>> session.run('C')
Traceback (most recent call last):
    ...
RuntimeError: Error from Matlab: Error: MATLAB:UndefinedFunction with message: Undefined function or variable 'C'.
 end.

A trick to make larger scripts more failsafe with regards to syntax errors.
Send a script to a string variable and run it with eval().

>>> mscript = """D = A
... for i=1:10
...    D = 2*D
... end
... """
>>> session.putstring('MSCRIPT',mscript)
>>> session.run('eval(MSCRIPT)')

To retrive the variable back to python:

>>> b = session.getvalue('B')
>>> (2*a==b).all()
True

Don't forget to close MATLAB.

>>> session.close()

Bugs, support and feature requests
----------------------------------

All request for support like bugfixing and installation support or feature
requests are directed to  the `SourceForge tracker for pymatlab
<http://sourceforge.net/tracker/?group_id=307148>`_. 

Please  consider to support us in our efforts by `donating to pymatlab`__. Your donations will be used to buy hardware and software licenses to be able to continue to develop this package. 

.. _Donations: http://sourceforge.net/donate/index.php?group_id=307148

__ Donations_
