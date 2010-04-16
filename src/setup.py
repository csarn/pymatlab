#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from setuptools import setup,find_packages,Extension
import os.path
import platform

if platform.system() == 'Windows':
    libraries = ['libmx', 'libmat', 'libeng']
#    include_dirs = ['C:/Program Files/MATLAB/R2008a/extern/include',
#                    'C:/Python26/Lib/site-packages/numpy/core/include']
#    library_dirs = ['C:/Program Files/MATLAB/R2008a/bin/win64',
#                    'C:/Program Files/MATLAB/R2008a/extern/lib/win64/microsoft']
elif platform.system() == 'Linux':
    libraries = ['eng', 'm', 'mx']
#    include_dirs = ['/opt/matlab2010a/extern/include']
#    library_dirs = ['/opt/matlab2010a/bin/glnxa64',
#            '/opt/matlab2010a/bin/glnx86']
else:
    raise 'Unsupported system %s' % platform.system()

setup(
        name='pymatlab',
        version='0.1.2',
        description = 'A python interface to MATLAB',
        long_description=open("README.txt").read() + "\n" + 
            open(os.path.join("docs", "HISTORY.txt")).read(),
        packages = find_packages(),
        classifiers=['Development Status :: 3 - Alpha',
                        'Intended Audience :: End Users/Desktop',
                        'Intended Audience :: Developers',
                        'Intended Audience :: Science/Research',
                        'License :: OSI Approved :: GNU General Public License (GPL)',
                        'Operating System :: POSIX',
                        'Programming Language :: C',
                        'Programming Language :: Python',
                          ],
        ext_modules=[Extension('pymatlab.matlab',
                      ['pymatlab/matlab.c'],
                      libraries=libraries,
 #                     include_dirs=include_dirs,
 #                     library_dirs=library_dirs,
                      extra_compile_args=['-g',],
                      )],
        test_suite='tests.alltests.suite',
        url = 'http://pymatlab.sourceforge.net/',
        zip_safe=False,
        author='Joakim Moller',
        author_email='joakim.moller@chalmers.se',
        install_requires=['setuptools','numpy'],
        #tests_require=['mocker','setuptools'],
)

