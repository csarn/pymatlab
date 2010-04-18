#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from setuptools import setup,find_packages,Extension
import os.path
import platform

if platform.system() == 'Windows':
    libraries = ['libmx', 'libmat', 'libeng']
elif platform.system() == 'Linux':
    libraries = ['eng', 'm', 'mx']
else:
    raise 'Unsupported system %s' % platform.system()

setup(
        name='pymatlab',
        version='0.1.3',
        description = 'A python interface to MATLAB',
        long_description=open("README.txt").read() + "\n" + 
            open(os.path.join("docs", "CHANGELOG.txt")).read(),
        packages = find_packages('src'),
        package_dir={'':'src'},
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
                      ['src/pymatlab/matlab.c'],
                      libraries=libraries,
                      extra_compile_args=['-g',],
                      )],
        test_suite='tests.alltests.test_suite',
        url = 'http://pymatlab.sourceforge.net/',
        zip_safe=False,
        author='Joakim Moller',
        author_email='joakim.moller@chalmers.se',
        install_requires=['setuptools','numpy'],
        #tests_require=['setuptools'],
)

