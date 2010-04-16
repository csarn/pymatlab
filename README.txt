=====================================
Python interface to MATLAB (pymatlab)
=====================================

This package lets python users interface and communicate with MATLAB from
python. This makes it easier for users to migrate from a large MATLAB codebase to
python scripts - one step at a time - by using old MATLAB scripts.

Download
--------

http://sourceforge.net/projects/pymatlab/files/

Installing
----------

When installing from source distribution revise the include_dir and
library_dir.

Preparing to use pymatlab
-------------------------

Set the environmental variable LD_LIBRARY_PATH to correct path where pymatlab
can find MATLAB's libraries (libmx and libeng) or update /etc/ldconfig. On my
system with MATLAB installed in /opt/matlab I have put this line in my
.profile:

export LD_LIBRARY_PATH=/opt/matlab/bin/glnxa64:$LD_LIBRARY_PATH

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
''

>>> session.run('C')
"Error: MATLAB:UndefinedFunction with message: Undefined function or variable 'C'.\n"

A trick to make larger scripts more failsafe with regards to syntax errors.
Send a script to a string variable and run it with eval().

>>> mscript = """D = A
... for i=1:10
...    D = 2*D
... end
... """
>>> session.putstring('MSCRIPT',mscript)
>>> session.run('eval(MSCRIPT)')
''

To retrive the variable back to python:

>>> b = session.getvalue('B')
>>> (2*a==b).all()
True

Don't forget to close MATLAB.

>>> session.close()

Enjoy!

Joakim Moller, joakim.moller@chalmers.se
