#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from setuptools import setup,find_packages,Extension
import os.path

setup(
        name='pymatlab',
        version='0.1.0',
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
                        'Programming Language :: Python',
                          ],
        ext_modules=[Extension('pymatlab.matlab',
                      ['pymatlab/matlab.c'],
                      libraries=['eng','m','mx'],
                      include_dirs=['/opt/matlab/extern/include'],
                      library_dirs=['/opt/matlab/bin/glnxa64'],
                      )],
        test_suite='tests',
        zip_safe=False,
        author='Joakim Möller',
        author_email='joakim.moller@chalmers.se',
        install_requires=['setuptools','numpy'],
        #tests_require=['mocker','setuptools'],
)

