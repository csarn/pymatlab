#!/usr/bin/python
from setuptools import setup,find_packages
from os.path import join
setup(
        name='pymatlab',
        version='0.2.2',
        description = 'A pythonic interface to MATLAB',
        long_description=open("README.txt").read() + "\n" + 
            open(join("docs", "CHANGELOG.txt")).read(),
        packages = find_packages('src'),
        package_dir={'':'src'},
        classifiers=['Development Status :: 3 - Alpha',
                        'Intended Audience :: End Users/Desktop',
                        'Intended Audience :: Developers',
                        'Intended Audience :: Science/Research',
                        'License :: OSI Approved :: GNU General Public License (GPL)',
                        'Operating System :: POSIX',
                        'Programming Language :: Python',
                          ],
        test_suite='tests.test_all.test_suite',
        url = 'http://pymatlab.sourceforge.net/',
        author='Joakim M&ouml;ller',
        author_email='joakim.moller@molflow.com',
        install_requires=['setuptools','numpy'],
        #tests_require=['setuptools'],
)

